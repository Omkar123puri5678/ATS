import os
import subprocess
import sys
from pathlib import Path

from app.scorer import _jd_keywords, analyze, extract_keywords

GOOD_RESUME = """
Priya Sharma
priya.sharma@example.com | +91 98765 43210 | linkedin.com/in/priyasharma

Summary
Computer science student with hands-on experience building web apps with React and Node.js.

Experience
Software Engineering Intern, Acme Corp (Jun 2025 - Aug 2025)
- Built a React dashboard used by 200+ internal users to track orders
- Reduced API response time by 35% by adding Redis caching to Node.js services
- Wrote unit tests with Jest, raising coverage from 40% to 85%

Projects
- Developed a REST API in Python with FastAPI and PostgreSQL deployed on AWS using Docker
- Implemented CI/CD with GitHub Actions, cutting release time by 50%

Education
B.Tech Computer Science, XYZ University, 2022 - 2026, CGPA 8.7

Skills
JavaScript, TypeScript, React, Node.js, Python, FastAPI, PostgreSQL, Redis, Docker, AWS, Git
""" + "\n".join(
    f"- Collaborated with the team on feature {i} and improved quality across modules" for i in range(15)
)

JD = """
We are looking for a Software Engineer Intern with experience in React, TypeScript and Node.js.
Knowledge of Docker, Kubernetes and AWS is a plus. You will build REST API services,
write unit tests and work with PostgreSQL. Experience with GraphQL preferred.
"""


def test_extract_keywords_finds_skills():
    kws = extract_keywords(JD)
    for k in ["react", "typescript", "node.js", "docker", "kubernetes", "aws", "graphql"]:
        assert k in kws
    # "c" must not be pulled in just because it appears inside other words
    assert "c" not in kws


def test_good_resume_scores_well():
    result = analyze(GOOD_RESUME, JD)
    assert result["score"] >= 70
    assert "kubernetes" in result["keywords"]["missing"]
    assert "react" in result["keywords"]["matched"]
    assert result["sections"]["experience"]
    assert result["sections"]["education"]
    assert result["sections"]["skills"]
    assert all(result["contact"].values())


def test_works_without_job_description():
    result = analyze(GOOD_RESUME)
    assert "keywords" not in result["breakdown"]
    assert 0 <= result["score"] <= 100


def test_poor_resume_scores_low():
    result = analyze("John Doe. I like computers and I did some stuff at a job.", JD)
    assert result["score"] < 40
    assert any(i["severity"] == "high" for i in result["issues"])


def test_synonyms_and_plurals_count_as_matches():
    jd = "Requirements: PostgreSQL, Kubernetes, AWS, REST API design and unit testing."
    resume = """Experience
- Built 12 REST APIs on Postgres, deployed to K8s on Amazon Web Services
- Wrote 300 unit tests, raising coverage from 50% to 90%
"""
    result = analyze(resume, jd)
    for k in ["postgresql", "kubernetes", "aws", "rest api", "unit testing"]:
        assert k in result["keywords"]["matched"], k


def test_skills_only_listed_earn_partial_credit():
    jd = "Must know Python and Docker."
    shown = "Experience\n- Built 5 data pipelines in Python and shipped them with Docker to 3 teams\n"
    listed = "Experience\n- Built 5 data pipelines and shipped them to 3 teams across the company\nSkills\nPython, Docker, Git, Linux\n"
    shown_result, listed_result = analyze(shown, jd), analyze(listed, jd)
    assert shown_result["keywords"]["listed_only"] == []
    assert set(listed_result["keywords"]["listed_only"]) == {"python", "docker"}
    assert listed_result["breakdown"]["keywords"]["score"] < shown_result["breakdown"]["keywords"]["score"]


def test_nice_to_have_keywords_weigh_less():
    jd = "Requirements: Python, SQL.\nNice to have: Docker, Kubernetes."
    kws = {k["term"]: k for k in _jd_keywords(jd)}
    assert not kws["python"]["optional"] and kws["docker"]["optional"]
    assert kws["docker"]["weight"] < kws["python"]["weight"]
    assert "kubernetes" in analyze("Python, SQL developer", jd)["keywords"]["optional"]


def test_pasted_job_description_is_ignored():
    stuffed = GOOD_RESUME + "\nSkills\n" + JD
    result = analyze(stuffed, JD)
    assert result["copied_lines"] >= 2
    assert any("copied" in i["message"] for i in result["issues"])
    assert result["score"] <= analyze(GOOD_RESUME, JD)["score"]


def test_skills_list_in_job_order_is_not_flagged_as_copied():
    jd = "Requirements: SEO, SEM, Google Ads, Meta Ads, Google Analytics, content marketing, email marketing."
    resume = "Skills\nSEO, SEM, Google Ads, Meta Ads, Google Analytics, Content Marketing, Email Marketing, Canva, Excel\n"
    assert analyze(resume, jd)["copied_lines"] == 0


def test_vague_bullets_get_no_impact_credit():
    text = """Experience
- Built 10 things and improved 20 things by 50% across various teams
- Developed 5 features and fixed various bugs by 40% etc
"""
    result = analyze(text)
    assert result["breakdown"]["impact"]["score"] == 0
    assert any("vague" in i["message"] for i in result["issues"])


def test_summary_and_skill_lines_are_not_treated_as_bullets():
    text = """Summary
Computer science student with hands-on experience building full-stack web apps
Experience
• Built a React dashboard used by 200+ internal users
• Reduced API response time by 35% with Redis caching
Skills
Languages: JavaScript, TypeScript, Python, SQL, Java, Go
"""
    result = analyze(text)
    assert result["weak_bullets"] == []
    assert result["breakdown"]["impact"]["score"] == 100


def test_scores_do_not_depend_on_hash_seed():
    # Set iteration order changes with PYTHONHASHSEED; scores must not.
    code = (
        "from app.scorer import analyze;"
        "jd='Requirements: SEO, SEM, Google Ads, Meta Ads, content marketing, email marketing, social media marketing.';"
        "print(analyze('Skills\\nSEO, SEM, Google Ads, Meta Ads, Content Marketing, Email Marketing, Canva', jd)['score'])"
    )
    backend = Path(__file__).resolve().parent.parent
    scores = set()
    for seed in range(4):
        run = subprocess.run(
            [sys.executable, "-c", code], cwd=backend, capture_output=True, text=True,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
        )
        assert run.returncode == 0, run.stderr
        scores.add(run.stdout.strip())
    assert len(scores) == 1, scores
