from fastapi.testclient import TestClient

from app import llm, main
from app.resume_model import (
    keep_supported_skills,
    mask_invented_numbers,
    normalize,
    restore_missing_skills,
    to_text,
)

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


def test_drops_skills_not_in_original_resume():
    source = "Skills: Excel, SQL, Power BI, Python (basic), Communication, JS"
    skills, dropped = keep_supported_skills(
        "Tools: Excel, SQL, Power BI\nOther: Python (basic), Stakeholder Communication, Statistics\nJavaScript",
        source,
    )
    assert skills == "Tools: Excel, SQL, Power BI\nOther: Python (basic)\nJavaScript"
    assert dropped == ["Stakeholder Communication", "Statistics"]


def test_normalize_fixes_dates_and_unnamed_projects():
    r = normalize({
        "experience": [{"role": "Analyst", "start": "Mon 2022", "end": "Present"}],
        "projects": [{"tech": "Tableau", "bullets": ["Built a dashboard"]}],
    })
    assert r["experience"][0]["start"] == "2022"
    assert r["projects"][0]["name"] == "Untitled project"


def test_restores_skills_the_model_left_out():
    source = "SKILLS\nPython, Java, JavaScript, React, HTML, CSS, Git, scikit-learn"
    skills, restored = restore_missing_skills("Frameworks: React\nLanguages: Python, JavaScript", source)
    assert restored == ["Java", "HTML", "CSS", "Git", "scikit-learn"]
    assert skills.endswith("\nAdditional: Java, HTML, CSS, Git, scikit-learn")


def test_strips_generic_skill_labels():
    skills, _ = keep_supported_skills("Category: React, Python\nTools: Git", "React Python Git")
    assert skills == "React, Python\nTools: Git"


def test_drops_untitled_job_that_repeats_projects():
    r = normalize({
        "experience": [
            {"role": "Intern", "company": "Pixel Forge", "bullets": ["Fixed 25 UI bugs"]},
            {"bullets": ["Built a movie recommendation system in Python with scikit-learn"]},
            {"bullets": ["Organised the annual tech fest for 2000 attendees"]},
        ],
        "projects": [{"name": "Movie Recommendation System", "tech": "Python, scikit-learn",
                      "bullets": ["Built a recommendation system for movies"]}],
    })
    roles = [e["role"] for e in r["experience"]]
    assert roles == ["Intern", "Untitled role"]


def test_restore_ignores_words_outside_skills_section():
    source = "EXPERIENCE\n- Built a tracker with 1,200 GitHub stars\n- Created weekly sales reports\nSKILLS\nPython, Docker"
    skills, restored = restore_missing_skills("Python", source)
    assert restored == ["Docker"]


def test_masks_numbers_not_in_original():
    source = "Ran social media for 5 brands, growing followers from 20K to 95K. Cut costs by 30%."
    r = normalize({
        "summary": "Marketer with 4 years of experience",
        "experience": [{"role": "Exec", "bullets": [
            "Grew followers from 20K to 95K across 5 brands",
            "Increased engagement by 25% and sales 3.5x",
            "Cut hosting costs by 30% for 1,200 users",
        ]}],
    })
    masked = mask_invented_numbers(r, source)
    assert r["summary"] == "Marketer with [X] years of experience"
    assert r["experience"][0]["bullets"].splitlines() == [
        "Grew followers from 20K to 95K across 5 brands",
        "Increased engagement by [X%] and sales [X]x",
        "Cut hosting costs by 30% for [X] users",
    ]
    assert masked == ["4", "25%", "3.5x", "1,200"]


def test_restore_needs_a_real_skills_heading():
    source = "I want a job where I can use my\nskills and grow.\nI worked in marketing and know MS Office and Excel."
    assert restore_missing_skills("", source) == ("", [])


def test_filler_values_become_empty():
    r = normalize({"location": "N/A", "experience": [{"role": "Marketing", "company": "Not Specified", "start": "Unknown"}]})
    assert r["location"] == ""
    assert r["experience"][0]["company"] == "" and r["experience"][0]["start"] == ""
