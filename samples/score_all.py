"""Score every sample resume against every sample job description.

Uses the same parser and scoring engine as the app, so the numbers match what
the Analyzer shows. Run from the repo root:

    backend\\.venv\\Scripts\\python samples\\score_all.py      (Windows)
    backend/.venv/bin/python samples/score_all.py            (macOS/Linux)

Pass a folder to score your own resumes instead:  score_all.py path\\to\\resumes
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from app.parser import extract_text  # noqa: E402
from app.scorer import analyze  # noqa: E402


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "resumes"
    jobs = {p.stem: p.read_text(encoding="utf-8") for p in sorted((HERE / "job_descriptions").glob("*.txt"))}
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".pdf", ".docx", ".txt"})
    if not files:
        sys.exit(f"No .pdf, .docx or .txt files in {folder}")

    columns = ["no JD", *jobs]
    width = max(len(p.name) for p in files) + 2
    print("Resume".ljust(width) + "".join(c[:12].rjust(14) for c in columns))
    for path in files:
        text = extract_text(path.name, path.read_bytes())
        scores = [analyze(text, "")["score"]] + [analyze(text, jd)["score"] for jd in jobs.values()]
        print(path.name.ljust(width) + "".join(str(s).rjust(14) for s in scores))


if __name__ == "__main__":
    main()
