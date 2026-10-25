# 📄 ATS Resume Maker

An open-source resume builder with an AI-powered ATS (Applicant Tracking System) analyzer.
Build an ATS-friendly resume, export it as a PDF, and score any resume against a job description,
all without paid APIs. AI features run on **local open-source models** through [Ollama](https://ollama.com),
so your resume never leaves your machine.

## Features

**Resume Builder**
- Guided form for personal details, summary, experience, projects, education, skills and certifications
- Live PDF preview with 3 ATS-friendly templates (Classic, Modern, Compact)
- One-click PDF export with real, selectable text (no images, tables or columns that confuse ATS parsers)
- Autosaves to your browser

**ATS Analyzer**
- Upload a resume (PDF, DOCX or TXT) or analyze the one you just built
- Overall ATS score (0–100) with a per-category breakdown
- Keyword match against a job description: see which keywords you have and which you're missing
- Checks for standard section headings, contact info, action verbs, quantified results and length
- Prioritized list of what to fix

**AI suggestions (optional, local)**
- Rewrites weak bullet points with action verbs and measurable impact
- Writes a professional summary from your resume
- Powered by any Ollama model (default: `llama3.2`). The rest of the app works fine without it.

## How the scoring works

The score is a weighted sum of six checks, all computed offline with open-source tools:

| Check | Weight | How |
|---|---|---|
| Keyword match | 35 | Skills and frequent terms extracted from the job description, matched in the resume |
| Content relevance | 10 | TF-IDF cosine similarity (scikit-learn) between resume and job description |
| Sections | 20 | Detects standard headings: Experience, Education, Skills (+ Summary, Projects, Certifications) |
| Contact info | 10 | Email, phone, LinkedIn/GitHub/portfolio link |
| Impact | 15 | Share of bullet points that start with an action verb and include numbers |
| Length | 10 | 300–1000 words is ideal |

Without a job description, the keyword and relevance checks are skipped and the other weights are rescaled.
See [`backend/app/scorer.py`](backend/app/scorer.py).

## Tech stack

- **Frontend:** React, Vite, Tailwind CSS, `@react-pdf/renderer`
- **Backend:** Python, FastAPI, pdfplumber, python-docx, scikit-learn
- **AI:** Ollama (Llama 3.2, Mistral, Qwen or any other local model)

## Getting started

### Option 1: Docker (easiest)

```bash
docker compose up --build
```

Open http://localhost:8080.

### Option 2: Run locally

**Requirements:** Python 3.10+, Node.js 20+

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Enable AI suggestions (optional)

1. Install [Ollama](https://ollama.com/download)
2. Pull a model: `ollama pull llama3.2`
3. Restart the app. The header badge changes from **AI: off** to **AI: llama3.2**.

To use a different model, set `OLLAMA_MODEL` (e.g. `OLLAMA_MODEL=mistral`) before starting the backend.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama is running |
| `OLLAMA_MODEL` | `llama3.2` | Model used for suggestions |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |

## API

Interactive docs are at http://localhost:8000/docs when the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Backend status and AI availability |
| POST | `/api/analyze` | Analyze an uploaded file (`file`, optional `job_description`) |
| POST | `/api/analyze-text` | Analyze plain text (`resume_text`, `job_description`) |
| POST | `/api/ai/rewrite-bullets` | Rewrite bullet points with the local LLM |
| POST | `/api/ai/summary` | Generate a professional summary |

## Project structure

```
backend/
  app/
    main.py        FastAPI routes
    parser.py      PDF / DOCX / TXT text extraction
    scorer.py      ATS scoring engine
    skills.py      Skill vocabulary and action verbs (easy to extend)
    llm.py         Ollama integration
  tests/
frontend/
  src/
    builder/       Resume form, PDF templates, live preview
    analyzer/      Upload, scoring report, AI rewrites
    resume.js      Resume data model
```

## Running tests

```bash
cd backend
pytest
```

## Roadmap

- [ ] More templates
- [ ] Import an existing resume into the builder
- [ ] Semantic keyword matching with local embeddings (sentence-transformers)
- [ ] Cover letter generator
- [ ] Multi-language support

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).
A good first contribution is adding skills for your field to [`backend/app/skills.py`](backend/app/skills.py).

## License

[MIT](LICENSE)
