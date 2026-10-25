"""Rule-based ATS scoring. Runs fully offline, no AI model required."""
import re
from collections import Counter
from functools import lru_cache

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import ACTION_VERBS, JD_NOISE, NICE_TO_HAVE, SKILLS, SYNONYMS, VAGUE_WORDS

SECTIONS = {
    "summary": [r"summary", r"objective", r"profile", r"about me"],
    "experience": [r"experience", r"employment", r"work history", r"internships?"],
    "education": [r"education", r"academic"],
    "skills": [r"skills", r"technical skills", r"technologies", r"tech stack"],
    "projects": [r"projects?"],
    "certifications": [r"certifications?", r"courses", r"licenses"],
}
REQUIRED_SECTIONS = ["experience", "education", "skills"]

# Precompiled per section: a heading matches if it is exactly the name (optionally
# "X & Y" / "X and Y") or starts with it as a whole word.
_SECTION_RES = {
    name: [(re.compile(rf"({p})(\s*&.*|\s+and.*)?"), re.compile(rf"^{p}\b")) for p in patterns]
    for name, patterns in SECTIONS.items()
}

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

# How much a keyword counts towards the keyword score.
LISTED_ONLY_CREDIT = 0.6  # skill appears only in a skills list, never in experience or projects
OPTIONAL_WEIGHT = 0.5     # job description marks it as nice to have
FREQUENT_WEIGHT = 0.5     # frequent job-description word that is not a known skill

# Sections whose lines list skills rather than show them being used.
LIST_SECTIONS = {"skills", "certifications"}


@lru_cache(maxsize=4096)
def _term_pattern(term: str) -> re.Pattern:
    # Custom boundaries so terms like "c++", "c#" and "node.js" match correctly.
    # Longer alphabetic terms also match their plural ("rest api" -> "rest apis").
    plural = "(?:s|es)?" if len(term) >= 3 and term[-1].isalpha() else ""
    return re.compile(rf"(?<![\w+#]){re.escape(term)}{plural}(?![\w+#])", re.I)


def _contains(text: str, term: str) -> bool:
    return bool(_term_pattern(term).search(text))


def _has_skill(text: str, skill: str) -> bool:
    return any(_contains(text, t) for t in (skill, *SYNONYMS.get(skill, ())))


def _stem(word: str) -> str:
    """Tiny suffix stripper so 'dashboards', 'testing' and 'managed' match their base word."""
    for suffix in ("ing", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            word = word[: -len(suffix)]
            break
    return word[:-1] if word.endswith("e") and len(word) > 4 else word


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9+#./]*", text.lower())


def _jd_segments(job_description: str) -> list[tuple[str, bool]]:
    """Split a job description into sentences, each flagged optional or required.

    A sentence is optional if it says so ("... is a plus") or sits under a
    "Nice to have:" style heading.
    """
    segments, optional_block = [], False
    for line in _split_lines(job_description):
        low = line.lower()
        is_heading = low.endswith(":") or len(low.split()) <= 4
        has_marker = any(m in low for m in NICE_TO_HAVE)
        if is_heading:
            optional_block = has_marker
        for sentence in re.split(r"(?<=[.;!?])\s+", line):
            s = sentence.lower()
            segments.append((sentence, optional_block or any(m in s for m in NICE_TO_HAVE)))
    return segments


def _jd_keywords(job_description: str, limit: int = 25) -> list[dict]:
    """Terms an ATS would likely filter on, each with a weight (required > optional > frequent word)."""
    jd = job_description.lower()
    segments = _jd_segments(job_description)

    def required(found_in) -> bool:
        hits = [opt for seg, opt in segments if found_in(seg)]
        return not hits or not all(hits)

    found = [s for s in sorted(SKILLS) if _has_skill(jd, s)]
    # Prefer the longest form ("spring boot" over "spring").
    found = [s for s in found if not any(s != o and _contains(o, s) for o in found)]

    def first_pos(skill):
        matches = (_term_pattern(t).search(jd) for t in (skill, *SYNONYMS.get(skill, ())))
        return min(m.start() for m in matches if m)

    found.sort(key=first_pos)
    keywords = [
        {"term": s, "skill": True,
         "optional": not required(lambda seg, s=s: _has_skill(seg, s))}
        for s in found
    ]

    stop = ENGLISH_STOP_WORDS | JD_NOISE
    skill_stems = {_stem(t) for s in found for t in s.split()}
    counts: Counter[str] = Counter()
    display: dict[str, str] = {}
    for w in (t.strip("./-") for t in _tokens(jd)):
        if len(w) < 3 or not w[0].isalpha() or w in stop:
            continue
        stem = _stem(w)
        counts[stem] += 1
        display.setdefault(stem, w)
    for stem, c in counts.most_common():
        if c >= 2 and stem not in skill_stems:
            keywords.append({
                "term": display[stem], "skill": False, "stem": stem,
                "optional": not required(lambda seg, st=stem: st in {_stem(t) for t in _tokens(seg)}),
            })
    for k in keywords:
        k["weight"] = (FREQUENT_WEIGHT if not k["skill"] else 1.0) * (OPTIONAL_WEIGHT if k["optional"] else 1.0)
    return keywords[:limit]


def extract_keywords(job_description: str, limit: int = 25) -> list[str]:
    """Pick the terms from a job description that an ATS would likely filter on."""
    return [k["term"] for k in _jd_keywords(job_description, limit)]


def _split_lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]


def _heading_section(line: str) -> str | None:
    """Section name if this line is a heading. Headings are short lines; checking only
    those avoids false positives like "experience" appearing in a sentence."""
    if len(line.split()) > 5:
        return None
    h = line.lower().strip(":•-– ")
    for name, res in _SECTION_RES.items():
        if any(full.fullmatch(h) or prefix.match(h) for full, prefix in res):
            return name
    return None


def detect_sections(text: str) -> dict[str, bool]:
    found = {_heading_section(l) for l in _split_lines(text)}
    return {name: name in found for name in _SECTION_RES}


def _is_list_line(line: str) -> bool:
    """'Python, SQL, Docker, AWS' style lines: many short comma-separated items."""
    body = line.split(":", 1)[1] if ":" in line[:30] else line
    items = [i for i in re.split(r"[,|;•]", body) if i.strip()]
    return len(items) >= 4 and sum(len(i.split()) for i in items) / len(items) <= 3


def _copied_lines(lines: list[str], job_description: str, n: int = 5) -> set[str]:
    """Resume lines that are mostly word-for-word copies of the job description."""
    def shingles(tokens):
        return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}

    jd_shingles = shingles(_tokens(job_description))
    copied = set()
    for line in lines:
        toks = _tokens(line)
        if len(toks) < 8:
            continue
        sh = shingles(toks)
        overlap = len(sh & jd_shingles) / len(sh)
        if _is_list_line(line):
            # A real skills list can share the job description's order ("SEO, SEM,
            # Google Ads..."). A pasted requirements line also carries its filler
            # words ("Requirements:", "or", "is a plus").
            if overlap >= 0.8 and len(_filler_words(line)) >= 2:
                copied.add(line)
        elif overlap >= 0.6:
            copied.add(line)
    return copied


# Every skill and alias, longest first, so "content marketing" is removed before
# "marketing" can split it.
_ALL_TERMS = sorted({t for s in SKILLS for t in (s, *SYNONYMS.get(s, ()))}, key=lambda t: (-len(t), t))


def _filler_words(line: str) -> list[str]:
    """Words left in a line after removing every known skill and alias."""
    rest = line.lower()
    for term in _ALL_TERMS:
        rest = _term_pattern(term).sub(" ", rest)
    return [w for w in re.findall(r"[a-z]{2,}", rest) if w != "and"]


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

    # --- Copied text ----------------------------------------------------------
    # Lines pasted from the job description are keyword stuffing: ignore them for
    # keyword, relevance and impact scoring so they cannot inflate the score.
    lines = _split_lines(text)
    copied = _copied_lines(lines, jd) if jd else set()
    if copied:
        issues.append({
            "severity": "high",
            "message": f"{len(copied)} line(s) look copied from the job description. They were ignored "
                       "for scoring. Describe your own work in your own words.",
        })
    clean_text = "\n".join(l for l in lines if l not in copied)

    # --- Keywords & similarity -------------------------------------------
    matched, missing, listed_only, optional = [], [], [], []
    similarity = None
    if jd:
        # Lines that show a skill in use: anything outside a skills list.
        section = None
        evidence = []
        for line in lines:
            if line in copied:
                continue
            heading = _heading_section(line)
            section = heading or section
            if heading is None and section not in LIST_SECTIONS and not _is_list_line(line):
                evidence.append(line)
        evidence_text = "\n".join(evidence)
        clean_stems = {_stem(t) for t in _tokens(clean_text)}
        evidence_stems = {_stem(t) for t in _tokens(evidence_text)}

        keywords = _jd_keywords(jd)
        earned = 0.0
        for k in keywords:
            if k["skill"]:
                in_evidence = _has_skill(evidence_text, k["term"])
                found = in_evidence or _has_skill(clean_text, k["term"])
            else:
                in_evidence = k["stem"] in evidence_stems
                found = in_evidence or k["stem"] in clean_stems
            if k["optional"]:
                optional.append(k["term"])
            if not found:
                missing.append(k["term"])
                continue
            matched.append(k["term"])
            credit = 1.0
            if not in_evidence and k["skill"]:
                listed_only.append(k["term"])
                credit = LISTED_ONLY_CREDIT
            earned += k["weight"] * credit
        total = sum(k["weight"] for k in keywords)
        scores["keywords"] = earned / total if total else 1.0

        missing_required = [k for k in missing if k not in optional]
        if missing:
            issues.append({
                "severity": "high" if scores["keywords"] < 0.5 else "medium",
                "message": f"Missing {len(missing)} keywords from the job description"
                           + (f", {len(missing_required)} of them required" if missing_required else "")
                           + ". Add the ones you genuinely have to your skills or bullet points.",
            })
        if listed_only:
            issues.append({
                "severity": "medium",
                "message": "These skills are only listed, never shown in your experience or projects: "
                           f"{', '.join(listed_only[:8])}. Mention them in a bullet that shows how you used them.",
            })

        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        try:
            m = tfidf.fit_transform([clean_text, jd])
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
    bullets = _bullets(clean_text)
    weak_bullets = []
    if bullets:
        # Vague bullets ("improved 20 things by 50%") get no credit even with a verb and a number.
        vague = [b for b in bullets if VAGUE_WORDS & set(_tokens(b))]
        concrete = [b for b in bullets if b not in vague]
        with_verb = [b for b in concrete if b.split()[0].lower().strip(",.") in ACTION_VERBS]
        with_number = [b for b in concrete if NUMBER_RE.search(b)]
        verb_ratio = len(with_verb) / len(bullets)
        number_ratio = len(with_number) / len(bullets)
        scores["impact"] = min(verb_ratio / 0.6, 1) * 0.5 + min(number_ratio / 0.4, 1) * 0.5
        weak_bullets = (vague + [b for b in concrete if b not in with_verb and b not in with_number])[:5]
        if vague:
            issues.append({
                "severity": "medium",
                "message": f"{len(vague)} bullet point(s) are vague (\"things\", \"various\", \"etc.\"). "
                           "Say exactly what you built or changed and for whom.",
            })
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
        "keywords": {"matched": matched, "missing": missing, "listed_only": listed_only, "optional": optional},
        "copied_lines": len(copied),
        "similarity": None if similarity is None else round(similarity, 3),
        "sections": sections,
        "contact": contact,
        "word_count": word_count,
        "weak_bullets": weak_bullets,
        "issues": issues,
    }
