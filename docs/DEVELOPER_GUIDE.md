# Developer Guide

Everything you need to run, change, test and deploy ATS Resume Maker. Read
[ARCHITECTURE.md](ARCHITECTURE.md) first for the big picture and [WORKFLOW.md](WORKFLOW.md) for the
request flows.

## Prerequisites

- Python 3.10+ (CI and Docker use 3.12)
- Node.js 20.19+ (CI and Docker use 22)
- Optional: [Ollama](https://ollama.com) for AI features, Docker for containerized runs

## Local setup

```bash
# Backend: http://localhost:8000 (API docs at /docs)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend: http://localhost:5173
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. To point it elsewhere, set `API_URL`
before `npm run dev`.

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI routes, validation, error mapping
│   │   ├── parser.py        PDF / DOCX / TXT → text
│   │   ├── scorer.py        ATS scoring engine (pure functions)
│   │   ├── skills.py        SKILLS, ACTION_VERBS, JD_NOISE vocabularies
│   │   └── llm.py           Ollama client and prompts
│   ├── tests/test_scorer.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx          Tabs, health check
│   │   ├── api.js           fetch wrapper for /api
│   │   ├── resume.js        Resume data model, resumeToText()
│   │   ├── builder/         Builder, ResumeForm, templates, ResumePDF, renderPdf
│   │   └── analyzer/        Analyzer, Results
│   ├── nginx.conf           Production server config
│   ├── vite.config.js
│   └── Dockerfile
├── docs/                    Architecture, workflows, guides
├── .github/workflows/ci.yml Tests and build on every push / PR
└── docker-compose.yml
```

## Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `OLLAMA_URL` | backend | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | backend | `llama3.2` | Model for rewrites and summaries |
| `CORS_ORIGINS` | backend | `http://localhost:5173` | Comma-separated allowed origins |
| `API_URL` | frontend dev server | `http://127.0.0.1:8000` | Where Vite proxies `/api` |

In Docker, `OLLAMA_URL` defaults to `http://host.docker.internal:11434` (Ollama on your machine).

## Common tasks

### Add skills for your field

Add lowercase terms to `SKILLS` in `backend/app/skills.py`. Multi-word terms (`"power bi"`) and
symbols (`"c++"`, `"node.js"`) work. Add filler words that job posts repeat but aren't skills to
`JD_NOISE`, and verbs to `ACTION_VERBS`.

### Add a resume template

1. Add an entry to `TEMPLATES` in `frontend/src/builder/templates.js`:
   ```js
   minimal: {
     label: "Minimal",
     font: "Helvetica",          // built-in PDF fonts: Helvetica, Times-Roman, Courier (+ -Bold)
     bold: "Helvetica-Bold",
     accent: "#334155",
     headingCase: "uppercase",   // or "none"
     align: "left",              // header alignment: "left" or "center"
     small: false,               // true = tighter spacing and smaller text
   },
   ```
2. It appears in the dropdown automatically. If you need new layout options, read them from `t` in
   `makeStyles()` in `ResumePDF.jsx`.
3. Keep it ATS-friendly: single column, standard fonts, standard headings, no images or tables.

### Change or add a scoring check

1. Edit `analyze()` in `backend/app/scorer.py`. Each check sets `scores["<name>"]` to a value from
   0 to 1 and may append `{"severity": "high"|"medium"|"low", "message": ...}` to `issues`.
2. Add the check's weight to `WEIGHTS`. Weights are rescaled automatically, so they don't need to
   add up to exactly 100, but keeping them at 100 makes the README table easy to read.
3. Add a label for it in `LABELS` in `frontend/src/analyzer/Results.jsx`.
4. Add a test in `backend/tests/` and update the scoring table in the README.

### Add an API endpoint

1. Define a Pydantic request model and route in `backend/app/main.py`.
2. Use a plain `def` (or `run_in_threadpool`) for CPU-heavy work so it doesn't block the event
   loop; use `async def` for I/O such as calling Ollama.
3. Add a method in `frontend/src/api.js`.

### Change the AI prompts

Prompts live in `backend/app/llm.py`. The model is called with `format: "json"`, and parsing falls
back to an empty result if the output is malformed, so keep asking for the same JSON shape.

## Testing

```bash
cd backend && pytest          # scorer unit tests
cd frontend && npm run build  # catches import and syntax errors
```

Manual smoke test with the backend running:

```bash
curl localhost:8000/api/health
curl -X POST localhost:8000/api/analyze-text -H "Content-Type: application/json" \
  -d '{"resume_text":"Experience\n- Built APIs serving 2M users\nEducation\nSkills\nPython","job_description":"Python AWS"}'
curl -F file=@resume.pdf -F job_description="Python AWS" localhost:8000/api/analyze
```

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

| Job | Steps |
|---|---|
| `backend` | Python 3.12 → `pip install -r requirements.txt` → `pytest` |
| `frontend` | Node 22 → `npm ci` → `npm run build` |

## Docker

```bash
docker compose up --build                       # app on http://localhost:8080
OLLAMA_URL=http://ollama:11434 docker compose --profile ai up --build
docker compose exec ollama ollama pull llama3.2 # first time only, with the ai profile
```

The frontend image builds the app with Node and serves it with nginx, which also proxies `/api/`
to the backend, gzips assets and sets cache headers.

## Performance notes

- `@react-pdf/renderer` is loaded with a dynamic `import()` in `builder/Builder.jsx`, so the initial
  bundle is ~246 KB instead of ~1.45 MB. Don't import it (or `ResumePDF.jsx`) statically from
  anywhere else, or it will be pulled back into the main chunk. Import `templates.js` for template
  metadata instead.
- Scoring takes about 8 ms per resume; most of it is TF-IDF. Keyword regexes are cached.
- File parsing and scoring run in a worker thread, keeping the event loop free.

## Releasing

1. Make sure CI is green on `main`.
2. Bump `version` in `frontend/package.json` and in `FastAPI(version=...)` in `backend/app/main.py`.
3. Tag and push: `git tag v0.2.0 && git push --tags`, then create a release on GitHub.
