"""Rule-based ATS scoring. Runs fully offline, no AI model required."""
import re
from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import ACTION_VERBS, JD_NOISE, SKILLS

SECTIONS = {
    "summary": [r"summary", r"objective", r"profile", r"about me"],
    "experience": [r"experience", r"employment", r"work history", r"internships?"],
    "education": [r"education", r"academic"],
    "skills": [r"skills", r"technical skills", r"technologies", r"tech stack"],
    "projects": [r"projects?"],
    "certifications": [r"certifications?", r"courses", r"licenses"],
}
REQUIRED_SECTIONS = ["experience", "education", "skills"]

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
LINK_RE = re.compile(r"(linkedin\.com|github\.com|portfolio|https?://)", re.I)
NUMBER_RE = re.compile(r"\d+%|\$\s?\d|\d+\+|\b\d{2,}\b|\b\d+x\b", re.I)

# Weights add up to 100. Components that cannot be computed (no job
# description) are dropped and the rest are rescaled.
WEIGHTS = {
    "keywords": 35,
    "similarity": 10,
    "sections": 20,
    "contact": 10,
    "impact": 15,
    "length": 10,
}


def _term_pattern(term: str) -> re.Pattern:
    # Custom boundaries so terms like "c++", "c#" and "node.js" match correctly.
    return re.compile(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])", re.I)


def _contains(text: str, term: str) -> bool:
    return bool(_term_pattern(term).search(text))


def extract_keywords(job_description: str, limit: int = 25) -> list[str]:
    """Pick the terms from a job description that an ATS would likely filter on."""
    jd = job_description.lower()
    found = [s for s in SKILLS if _contains(jd, s)]
    # Prefer the longest form ("spring boot" over "spring").
    found = [s for s in found if not any(s != o and _contains(o, s) for o in found)]
    found.sort(key=lambda s: _term_pattern(s).search(jd).start())

    words = re.findall(r"[a-z][a-z+#./-]{2,}", jd)
    stop = ENGLISH_STOP_WORDS | JD_NOISE
    counts = Counter(w.strip("./-") for w in words if w not in stop)
    frequent = [w for w, c in counts.most_common() if c >= 2 and w not in found]

    keywords = found + frequent
    return keywords[:limit]


def _split_lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def detect_sections(text: str) -> dict[str, bool]:
    lines = _split_lines(text)
    # Headings are short lines; checking only those avoids false positives
    # like "experience" appearing in a sentence.
    headings = [l.lower().strip(":•-– ") for l in lines if len(l.split()) <= 5]
    result = {}
    for name, patterns in SECTIONS.items():
        result[name] = any(
            re.fullmatch(rf"({p})(\s*&.*|\s+and.*)?", h) or re.match(rf"^{p}\b", h)
            for h in headings
            for p in patterns
        )
    return result


BULLET_CHARS = "•-*–▪●◦➢►"


def _bullets(text: str) -> list[str]:
    lines = _split_lines(text)
    marked = [
        l.lstrip(BULLET_CHARS + " ").strip()
        for l in lines
        if l[0] in BULLET_CHARS and len(l.split()) >= 6
    ]
    if marked:
        return marked
    # No bullet markers (some PDF exports drop them): fall back to sentence-like
    # lines, skipping "Label: a, b, c" skill lines and "Name | tech" headers.
    return [
        l for l in lines
        if len(l.split()) >= 6 and ":" not in l[:25] and "|" not in l
    ]


def analyze(resume_text: str, job_description: str | None = None) -> dict:
    text = resume_text or ""
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    scores: dict[str, float] = {}
    issues: list[dict] = []
    jd = (job_description or "").strip()

    # --- Keywords & similarity -------------------------------------------
    matched, missing = [], []
    similarity = None
    if jd:
        keywords = extract_keywords(jd)
        for k in keywords:
            (matched if _contains(text, k) else missing).append(k)
        scores["keywords"] = len(matched) / len(keywords) if keywords else 1.0
        if missing:
            issues.append({
                "severity": "high" if scores["keywords"] < 0.5 else "medium",
                "message": f"Missing {len(missing)} keywords from the job description. "
                           "Add the ones you genuinely have to your skills or bullet points.",
            })

        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        try:
            m = tfidf.fit_transform([text, jd])
            similarity = float(cosine_similarity(m[0], m[1])[0][0])
        except ValueError:
            similarity = 0.0
        # Raw cosine scores for a good match are usually 0.25-0.5, so scale up.
        scores["similarity"] = min(similarity / 0.4, 1.0)

    # --- Sections ----------------------------------------------------------
    sections = detect_sections(text)
    required_found = sum(sections[s] for s in REQUIRED_SECTIONS)
    optional_found = sum(sections[s] for s in ("summary", "projects", "certifications"))
    scores["sections"] = 0.8 * required_found / len(REQUIRED_SECTIONS) + 0.2 * min(optional_found, 2) / 2
    for s in REQUIRED_SECTIONS:
        if not sections[s]:
            issues.append({
                "severity": "high",
                "message": f"No '{s.title()}' section heading found. Use a standard heading so ATS can parse it.",
            })

    # --- Contact info ------------------------------------------------------
    contact = {
        "email": bool(EMAIL_RE.search(text)),
        "phone": bool(PHONE_RE.search(text)),
        "link": bool(LINK_RE.search(text)),
    }
    scores["contact"] = 0.4 * contact["email"] + 0.4 * contact["phone"] + 0.2 * contact["link"]
    if not contact["email"]:
        issues.append({"severity": "high", "message": "No email address found."})
    if not contact["phone"]:
        issues.append({"severity": "medium", "message": "No phone number found."})
    if not contact["link"]:
        issues.append({"severity": "low", "message": "Add a LinkedIn, GitHub or portfolio link."})

    # --- Impact: action verbs & numbers -----------------------------------
    bullets = _bullets(text)
    weak_bullets = []
    if bullets:
        with_verb = [b for b in bullets if b.split()[0].lower().strip(",.") in ACTION_VERBS]
        with_number = [b for b in bullets if NUMBER_RE.search(b)]
        verb_ratio = len(with_verb) / len(bullets)
        number_ratio = len(with_number) / len(bullets)
        scores["impact"] = min(verb_ratio / 0.6, 1) * 0.5 + min(number_ratio / 0.4, 1) * 0.5
        weak_bullets = [b for b in bullets if b not in with_verb and b not in with_number][:5]
        if number_ratio < 0.25:
            issues.append({
                "severity": "medium",
                "message": "Few bullet points include numbers. Quantify results (e.g. 'reduced load time by 40%').",
            })
        if verb_ratio < 0.4:
            issues.append({
                "severity": "medium",
                "message": "Start bullet points with strong action verbs (built, led, improved...).",
            })
    else:
        scores["impact"] = 0.0
        issues.append({"severity": "medium", "message": "No bullet points detected in the resume."})

    # --- Length ------------------------------------------------------------
    if word_count < 150:
        scores["length"] = 0.2
        issues.append({"severity": "high", "message": f"Resume is very short ({word_count} words). "
                       "If this looks wrong, your PDF may be an image; ATS cannot read image text."})
    elif word_count < 300:
        scores["length"] = 0.6
        issues.append({"severity": "low", "message": f"Resume is short ({word_count} words). Aim for 350-900."})
    elif word_count <= 1000:
        scores["length"] = 1.0
    else:
        scores["length"] = 0.7
        issues.append({"severity": "low", "message": f"Resume is long ({word_count} words). Keep it to 1-2 pages."})

    # --- Total -------------------------------------------------------------
    total_weight = sum(WEIGHTS[k] for k in scores)
    overall = round(sum(scores[k] * WEIGHTS[k] for k in scores) / total_weight * 100)

    order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: order[i["severity"]])

    return {
        "score": overall,
        "breakdown": {
            k: {"score": round(v * 100), "weight": WEIGHTS[k]} for k, v in scores.items()
        },
        "keywords": {"matched": matched, "missing": missing},
        "similarity": None if similarity is None else round(similarity, 3),
        "sections": sections,
        "contact": contact,
        "word_count": word_count,
        "weak_bullets": weak_bullets,
        "issues": issues,
    }
