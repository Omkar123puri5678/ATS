"""Optional AI suggestions using a local open-source model through Ollama.

Nothing here is required: if Ollama is not running, the API reports it as
unavailable and the rest of the app keeps working.
"""
import json
import os

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class LLMUnavailableError(RuntimeError):
    pass


async def status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
    except (httpx.HTTPError, ValueError):
        return {"available": False, "model": OLLAMA_MODEL, "models": []}
    has_model = any(m.split(":")[0] == OLLAMA_MODEL.split(":")[0] for m in models)
    return {"available": has_model, "model": OLLAMA_MODEL, "models": models}


async def _generate(prompt: str, timeout: float = 120, num_ctx: int | None = None) -> str:
    options = {"temperature": 0.4}
    if num_ctx:
        options["num_ctx"] = num_ctx
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": options,
                },
            )
            r.raise_for_status()
            return r.json()["response"]
    except httpx.HTTPError as e:
        raise LLMUnavailableError(
            f"Could not reach Ollama at {OLLAMA_URL}. Is it running with '{OLLAMA_MODEL}' pulled?"
        ) from e


async def rewrite_bullets(bullets: list[str], job_description: str = "") -> list[dict]:
    jd_part = f"\nTarget job description:\n{job_description[:3000]}\n" if job_description else ""
    numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
    prompt = f"""You are an expert resume writer. Rewrite each resume bullet point so it:
- starts with a strong action verb
- is concise (under 30 words)
- highlights measurable impact; if a number is missing, use a placeholder like [X%] instead of inventing one
- naturally uses relevant keywords from the job description when truthful
{jd_part}
Bullet points:
{numbered}

Respond with JSON only, in this shape:
{{"rewrites": [{{"original": "...", "improved": "..."}}]}}"""
    raw = await _generate(prompt)
    try:
        data = json.loads(raw)
        return [
            {"original": r.get("original", ""), "improved": r.get("improved", "")}
            for r in data.get("rewrites", [])
        ]
    except (json.JSONDecodeError, AttributeError):
        return []


async def write_summary(resume_text: str, job_description: str = "") -> str:
    jd_part = f"\nTarget job description:\n{job_description[:3000]}\n" if job_description else ""
    prompt = f"""You are an expert resume writer. Write a 2-3 sentence professional summary
for the top of this resume. Use only facts from the resume. No first-person pronouns.
{jd_part}
Resume:
{resume_text[:6000]}

Respond with JSON only: {{"summary": "..."}}"""
    raw = await _generate(prompt)
    try:
        return json.loads(raw).get("summary", "")
    except (json.JSONDecodeError, AttributeError):
        return ""


RESUME_SCHEMA = """{
  "name": "", "title": "", "email": "", "phone": "", "location": "",
  "links": "one link per line",
  "summary": "",
  "experience": [{"role": "", "company": "", "location": "", "start": "", "end": "", "bullets": ["..."]}],
  "projects": [{"name": "", "tech": "comma-separated", "link": "", "bullets": ["..."]}],
  "education": [{"degree": "", "school": "", "start": "", "end": "", "details": ""}],
  "skills": ["Category: skill, skill, skill"],
  "certifications": ["..."]
}"""


async def build_resume(resume_text: str, job_description: str = "") -> dict:
    """Read a resume in any layout and return it rewritten in the builder's format.

    Returns the raw parsed JSON; callers should pass it through resume_model.normalize.
    """
    jd_part = (
        f"""
Tailor it to this job description: put the most relevant experience and skills first and use
its keywords wherever they truthfully describe the candidate's work.
Job description:
{job_description[:3000]}
"""
        if job_description
        else ""
    )
    prompt = f"""You are an expert resume writer who knows how Applicant Tracking Systems parse resumes.
Read the resume below. Its text may be jumbled by columns, tables or icons. Extract EVERY piece
of information and rebuild it as a clean, ATS-friendly resume:
- keep all jobs, projects, education, skills and certifications; never drop an entry
- never invent employers, titles, dates, degrees, skills or numbers
- rewrite each bullet to start with a strong action verb, under 30 words, focused on impact;
  if a metric is missing, add a placeholder like [X%] rather than making one up
- write a 2-3 sentence professional summary from the resume's facts, no first-person pronouns
- "title" is the candidate's target or current job title
- dates as "Mon YYYY" (e.g. "Jun 2024"); use "Present" for current roles
- group skills into a few categories, one category per list item
- use "" or [] for anything the resume does not contain
{jd_part}
Resume:
{resume_text[:8000]}

Respond with JSON only, exactly in this shape:
{RESUME_SCHEMA}"""
    # Long input and output: allow a bigger context window and more time than
    # the other prompts, since small local models can be slow here.
    raw = await _generate(prompt, timeout=300, num_ctx=8192)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
