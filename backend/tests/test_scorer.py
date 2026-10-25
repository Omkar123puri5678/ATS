from app.scorer import analyze, extract_keywords

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
