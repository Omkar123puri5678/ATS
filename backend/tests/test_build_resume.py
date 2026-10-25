from fastapi.testclient import TestClient

from app import llm, main
from app.resume_model import normalize, to_text

MESSY_RESUME = """PRIYA SHARMA   priya@example.com   +91 98765 43210
SKILLS          EXPERIENCE
Python, React   Acme Corp  Intern  Jun 2025 - Aug 2025
                worked on dashboard for orders
                did caching stuff with redis
EDUCATION       B.Tech Computer Science, XYZ University 2022 - 2026
"""

MODEL_OUTPUT = {
    "name": "Priya Sharma",
    "title": "Software Engineer",
    "email": "priya@example.com",
    "phone": "+91 98765 43210",
    "location": None,
    "links": ["linkedin.com/in/priya", "github.com/priya"],
    "summary": "Computer science student who builds web apps with React and Python.",
    "experience": [
        {
            "role": "Software Engineering Intern",
            "company": "Acme Corp",
            "start": "Jun 2025",
            "end": "Aug 2025",
            "bullets": ["Built a React order dashboard used by [X] users", "- Cut API latency by [X%] with Redis caching"],
        },
        "not an object",
        {},
    ],
    "education": [{"degree": "B.Tech in Computer Science", "school": "XYZ University", "start": "2022", "end": "2026"}],
    "skills": {"Languages": ["Python", "JavaScript"], "Tools": ["React", "Redis"]},
    "certifications": [],
    "unexpected": "ignored",
}


def test_normalize_coerces_model_output():
    r = normalize(MODEL_OUTPUT)
    assert r["location"] == ""
    assert r["links"] == "linkedin.com/in/priya\ngithub.com/priya"
    assert len(r["experience"]) == 1  # junk entries dropped
    exp = r["experience"][0]
    assert exp["location"] == ""
    assert exp["bullets"].splitlines()[1] == "Cut API latency by [X%] with Redis caching"
    assert r["education"][0]["details"] == ""
    assert r["skills"] == "Languages: Python, JavaScript\nTools: React, Redis"
    assert r["projects"] == []
    assert "unexpected" not in r


def test_normalize_handles_garbage():
    r = normalize("not json")
    assert r["experience"] == [] and r["name"] == ""


def test_to_text_has_standard_sections():
    text = to_text(normalize(MODEL_OUTPUT))
    for heading in ("Summary", "Experience", "Education", "Skills"):
        assert f"\n{heading}\n" in text


def test_build_resume_endpoint(monkeypatch):
    async def fake_build(text, jd):
        assert "Acme Corp" in text
        return MODEL_OUTPUT

    monkeypatch.setattr(llm, "build_resume", fake_build)
    client = TestClient(main.app)
    res = client.post(
        "/api/ai/build-resume",
        files={"file": ("resume.txt", MESSY_RESUME.encode())},
        data={"job_description": "React developer with Python and Redis"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["resume"]["experience"][0]["company"] == "Acme Corp"
    assert body["score_after"] > body["score_before"]


def test_build_resume_rejects_empty_file():
    client = TestClient(main.app)
    res = client.post("/api/ai/build-resume", files={"file": ("resume.txt", b"hello")})
    assert res.status_code == 422


def test_build_resume_reports_unusable_model_output(monkeypatch):
    async def fake_build(text, jd):
        return {}

    monkeypatch.setattr(llm, "build_resume", fake_build)
    client = TestClient(main.app)
    res = client.post("/api/ai/build-resume", files={"file": ("resume.txt", MESSY_RESUME.encode())})
    assert res.status_code == 502
