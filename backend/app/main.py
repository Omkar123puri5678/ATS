import os
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import llm, resume_model
from .parser import UnsupportedFileError, extract_text
from .scorer import analyze

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(title="ATS Resume Maker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeTextRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    job_description: str = ""


class RewriteRequest(BaseModel):
    bullets: list[str] = Field(min_length=1, max_length=15)
    job_description: str = ""


class SummaryRequest(BaseModel):
    resume_text: str = Field(min_length=1)
    job_description: str = ""


@app.get("/api/health")
async def health():
    return {"status": "ok", "ai": await llm.status()}


async def _read_upload(file: UploadFile) -> str:
    # Read one byte past the limit so oversized files are rejected without
    # loading all of them into memory.
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 5 MB.")
    # Parsing and scoring are CPU-bound; run them in a worker thread so one
    # large PDF does not block every other request.
    try:
        return await run_in_threadpool(extract_text, file.filename or "", data)
    except UnsupportedFileError as e:
        raise HTTPException(415, str(e))
    except Exception:
        raise HTTPException(422, "Could not read this file. Is it a valid, non-encrypted document?")


@app.post("/api/analyze")
async def analyze_upload(
    file: UploadFile = File(...),
    job_description: str = Form(""),
):
    text = await _read_upload(file)
    result = await run_in_threadpool(analyze, text, job_description)
    result["resume_text"] = text
    return result


@app.post("/api/analyze-text")
def analyze_text(req: AnalyzeTextRequest):  # sync: FastAPI runs it in a worker thread
    return analyze(req.resume_text, req.job_description)


@app.post("/api/ai/rewrite-bullets")
async def rewrite_bullets(req: RewriteRequest):
    try:
        return {"rewrites": await llm.rewrite_bullets(req.bullets, req.job_description)}
    except llm.LLMUnavailableError as e:
        raise HTTPException(503, str(e))


@app.post("/api/ai/summary")
async def summary(req: SummaryRequest):
    try:
        return {"summary": await llm.write_summary(req.resume_text, req.job_description)}
    except llm.LLMUnavailableError as e:
        raise HTTPException(503, str(e))


@app.post("/api/ai/build-resume")
async def build_resume(
    file: UploadFile = File(...),
    job_description: str = Form(""),
):
    """Upload any resume and get it back rebuilt in the builder's ATS-friendly format."""
    text = await _read_upload(file)
    if len(text.split()) < 20:
        raise HTTPException(
            422,
            "Found almost no text in this file. If it is a scanned image, export it as a text-based PDF or DOCX.",
        )
    try:
        raw = await llm.build_resume(text, job_description)
    except llm.LLMUnavailableError as e:
        raise HTTPException(503, str(e))
    resume = resume_model.normalize(raw)
    resume["skills"], dropped_skills = resume_model.keep_supported_skills(resume["skills"], text)
    resume["skills"], restored_skills = resume_model.restore_missing_skills(resume["skills"], text)
    masked_numbers = resume_model.mask_invented_numbers(resume, text)
    if not (resume["name"] or resume["experience"] or resume["education"]):
        raise HTTPException(502, "The AI model did not return a usable resume. Please try again.")
    before, after = await run_in_threadpool(
        lambda: (analyze(text, job_description), analyze(resume_model.to_text(resume), job_description))
    )
    return {
        "resume": resume,
        "score_before": before["score"],
        "score_after": after["score"],
        "dropped_skills": dropped_skills,
        "restored_skills": restored_skills,
        "masked_numbers": masked_numbers,
    }


# In the single-container deployment (root Dockerfile) the built frontend is
# copied to STATIC_DIR and served from here, so the site and the API share one
# origin. Locally this directory does not exist and Vite serves the frontend.
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parent.parent / "static"))

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        file = (STATIC_DIR / path).resolve()
        if path and file.is_file() and file.is_relative_to(STATIC_DIR.resolve()):
            return FileResponse(file)
        # Single-page app: every other route renders index.html.
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})
