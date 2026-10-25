import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import llm
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


@app.post("/api/analyze")
async def analyze_upload(
    file: UploadFile = File(...),
    job_description: str = Form(""),
):
    # Read one byte past the limit so oversized files are rejected without
    # loading all of them into memory.
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 5 MB.")
    # Parsing and scoring are CPU-bound; run them in a worker thread so one
    # large PDF does not block every other request.
    try:
        text = await run_in_threadpool(extract_text, file.filename or "", data)
    except UnsupportedFileError as e:
        raise HTTPException(415, str(e))
    except Exception:
        raise HTTPException(422, "Could not read this file. Is it a valid, non-encrypted document?")
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
