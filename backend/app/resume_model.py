"""The builder's resume data model on the backend.

Mirrors frontend/src/resume.js: the AI rebuild returns this shape so the result
loads straight into the builder form. Model output is untrusted, so everything
goes through normalize() before it reaches the client.
"""
import re

from .scorer import _contains, _has_skill, _heading_section, _split_lines, _tokens
from .skills import SKILLS, SYNONYMS

TEXT_FIELDS = ["name", "title", "email", "phone", "location", "links", "summary", "skills", "certifications"]
SECTION_FIELDS = {
    "experience": ["role", "company", "location", "start", "end", "bullets"],
    "education": ["degree", "school", "start", "end", "details"],
    "projects": ["name", "tech", "link", "bullets"],
}
# Fields that hold one entry per line in the form.
MULTILINE_FIELDS = {"bullets", "skills", "certifications", "links"}
MAX_ITEMS = 15

_BULLET_PREFIX = re.compile(r"^[-•*▪●◦➢►–\s]+")
DATE_FIELDS = {"start", "end"}
# Small models sometimes copy the prompt's "Mon YYYY" format hint literally.
_PLACEHOLDER_MONTH = re.compile(r"^(?:mon|mm|month)\.?\s+(?=\d{4}$)", re.I)
_SYNONYM_OF = {alt: canon for canon, alts in SYNONYMS.items() for alt in alts}
# What models write instead of leaving a field empty.
_FILLER = re.compile(r"^(?:not specified|not mentioned|not provided|unknown|n/?a|none|null|-)\.?$", re.I)
# Labels models emit when they copy the prompt's shape instead of naming a group.
_GENERIC_LABEL = re.compile(r"^(?:category|categories|skills?|group)\s*\d*$", re.I)


def _text(value, multiline: bool = False) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [_text(v, multiline) for v in value]
        sep = "\n" if multiline else ", "
        return sep.join(p for p in parts if p)
    if isinstance(value, dict):
        # e.g. skills as {"Languages": [...], "Tools": [...]}
        return "\n".join(f"{k}: {_text(v)}" for k, v in value.items() if _text(v))
    text = str(value).strip()
    if _FILLER.match(text):
        return ""
    if multiline:
        lines = (_BULLET_PREFIX.sub("", l).strip() for l in text.splitlines())
        return "\n".join(l for l in lines if l)
    return " ".join(text.split())


def normalize(data) -> dict:
    """Coerce model output into the exact shape the builder expects."""
    data = data if isinstance(data, dict) else {}
    out = {f: _text(data.get(f), f in MULTILINE_FIELDS) for f in TEXT_FIELDS}
    for section, fields in SECTION_FIELDS.items():
        items = data.get(section)
        items = items if isinstance(items, list) else []
        cleaned = []
        for item in items[:MAX_ITEMS]:
            if not isinstance(item, dict):
                continue
            entry = {f: _text(item.get(f), f in MULTILINE_FIELDS) for f in fields}
            for f in DATE_FIELDS & entry.keys():
                entry[f] = _PLACEHOLDER_MONTH.sub("", entry[f])
            if section == "projects" and not entry["name"] and any(entry.values()):
                entry["name"] = "Untitled project"  # keeps it visible so the user can name it
            if any(entry.values()):
                cleaned.append(entry)
        out[section] = cleaned
    out["experience"] = _drop_duplicate_entries(out["experience"], out["projects"])
    return out


def _drop_duplicate_entries(experience: list[dict], projects: list[dict]) -> list[dict]:
    """Remove nameless experience entries that only repeat project bullets.

    Small models sometimes copy a "Projects" bullet list into an untitled job.
    A nameless entry with its own content is kept and labelled for the user.
    """
    project_words = set(_tokens(" ".join(f"{p['name']} {p['tech']} {p['bullets']}" for p in projects)))
    kept = []
    for e in experience:
        if not (e["role"] or e["company"]):
            words = set(_tokens(e["bullets"]))
            if words and len(words & project_words) >= 0.6 * len(words):
                continue
            e = {**e, "role": "Untitled role"}
        kept.append(e)
    return kept


def _skill_in(source: str, skill: str) -> bool:
    base = re.sub(r"\s*\(.*?\)", "", skill).strip()  # "Python (basic)" -> "Python"
    terms = {skill, base}
    for t in list(terms):
        canon = _SYNONYM_OF.get(t.lower(), t.lower())
        terms |= {canon, *SYNONYMS.get(canon, ())}
    return any(t and _contains(source, t) for t in terms)


def keep_supported_skills(skills: str, source: str) -> tuple[str, list[str]]:
    """Drop skills that never appear in the original resume.

    Models tend to copy the job description's requirements into the skills
    list; listing skills the candidate does not have is the one thing a
    rebuilt resume must never do. Returns the cleaned text and what was dropped.
    """
    kept_lines, dropped = [], []
    for line in skills.splitlines():
        label, sep, items = line.rpartition(":") if ":" in line else ("", "", line)
        kept = []
        for item in (i.strip() for i in items.split(",")):
            if not item:
                continue
            (kept if _skill_in(source, item) else dropped).append(item)
        if _GENERIC_LABEL.match(label.strip()):
            label = sep = ""
        if kept:
            kept_lines.append(f"{label}{sep} {', '.join(kept)}".strip() if sep else ", ".join(kept))
    return "\n".join(kept_lines), dropped


def _find(text: str, term: str) -> re.Match | None:
    return re.search(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])", text, re.I)


def _skills_section(text: str) -> str:
    """Lines under the resume's Skills heading, or "" if it has none."""
    out, inside = [], False
    for line in _split_lines(text):
        heading = _heading_section(line)
        # A wrapped sentence can leave a short line like "skills and grow."
        if heading and not line.endswith((".", ",")):
            inside = heading == "skills"
        elif inside:
            out.append(line)
    return "\n".join(out)


def restore_missing_skills(skills: str, source: str) -> tuple[str, list[str]]:
    """Add back known skills from the original Skills section that the model left out.

    Only the Skills section counts: a word in a bullet ("GitHub stars", "sales
    reports") is not a claim to have that skill.
    """
    source = _skills_section(source)
    # Single letters ("c", "r") match too much ordinary text to restore safely.
    missing = [s for s in SKILLS if len(s) > 1 and _has_skill(source, s) and not _has_skill(skills, s)]
    # Keep the candidate's order and spelling ("scikit-learn", "HTML").
    matches = sorted((m for m in map(lambda s: _find(source, s), missing) if m), key=lambda m: m.start())
    found = list(dict.fromkeys(m.group(0) for m in matches))
    if not found:
        return skills, []
    extra = f"Additional: {', '.join(found)}"
    return (f"{skills}\n{extra}" if skills else extra), found


# A number with its unit: "45%", "1,200", "4.2x", "20K", "200+".
_NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(%|x\b|[kKmM]\b|\+)?")


def _numbers(text: str) -> set[str]:
    return {m.group(1).replace(",", "") for m in _NUMBER.finditer(text)}


def mask_invented_numbers(resume: dict, source: str) -> list[str]:
    """Replace numbers the original resume never mentions with [X] placeholders.

    Small models often "improve" a bullet by inventing a metric. A made-up
    number on a resume is worse than none, so any figure that is not in the
    source becomes a placeholder for the candidate to fill in. Edits resume
    in place and returns the numbers it masked.
    """
    known = _numbers(source)
    masked = []

    def fix(text: str) -> str:
        def repl(m):
            if m.group(1).replace(",", "") in known:
                return m.group(0)
            masked.append(m.group(0))
            unit = m.group(2) or ""
            return "[X%]" if unit == "%" else f"[X]{unit}"
        return _NUMBER.sub(repl, text)

    resume["summary"] = fix(resume["summary"])
    for section in ("experience", "projects"):
        for entry in resume[section]:
            entry["bullets"] = fix(entry["bullets"])
    return masked


def to_text(r: dict) -> str:
    """Plain-text version, laid out like the builder's PDF (see resumeToText)."""
    def rng(a, b):
        return " - ".join(x for x in (a, b) if x)

    out = [r["name"], r["title"], " | ".join(x for x in (r["email"], r["phone"], r["location"]) if x)]
    if r["links"]:
        out.append(r["links"].replace("\n", ", "))
    if r["summary"]:
        out += ["", "Summary", r["summary"]]
    if r["experience"]:
        out += ["", "Experience"]
        for e in r["experience"]:
            loc = f" ({e['location']})" if e["location"] else ""
            out.append(f"{e['role']}, {e['company']}{loc} {rng(e['start'], e['end'])}".strip())
            out += [f"- {b}" for b in e["bullets"].splitlines()]
    if r["projects"]:
        out += ["", "Projects"]
        for p in r["projects"]:
            out.append(" | ".join(x for x in (p["name"], p["tech"], p["link"]) if x))
            out += [f"- {b}" for b in p["bullets"].splitlines()]
    if r["education"]:
        out += ["", "Education"]
        for e in r["education"]:
            out.append(f"{e['degree']}, {e['school']} {rng(e['start'], e['end'])}".strip())
            if e["details"]:
                out.append(e["details"])
    if r["skills"]:
        out += ["", "Skills", *r["skills"].splitlines()]
    if r["certifications"]:
        out += ["", "Certifications", *r["certifications"].splitlines()]
    return "\n".join(l for l in out if l is not None)
