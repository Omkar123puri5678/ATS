"""The builder's resume data model on the backend.

Mirrors frontend/src/resume.js: the AI rebuild returns this shape so the result
loads straight into the builder form. Model output is untrusted, so everything
goes through normalize() before it reaches the client.
"""
import re

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
            if any(entry.values()):
                cleaned.append(entry)
        out[section] = cleaned
    return out


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
