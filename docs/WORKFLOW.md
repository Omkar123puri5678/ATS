# Workflows

How data moves through the app for each thing a user can do, plus the development workflow.
For the component overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Overall user journey

```mermaid
flowchart LR
    start(["Open app"]) --> choice{"What do you<br/>want to do?"}
    choice -- "Create a resume" --> build["Fill the Builder form<br/>(or load the sample)"]
    build --> preview["Live PDF preview<br/>pick a template"]
    preview --> check["Check ATS score →"]
    choice -- "Check an existing resume" --> up["Upload PDF / DOCX / TXT"]
    check --> jd["Paste job description<br/>(optional)"]
    up --> jd
    jd --> report["ATS report<br/>score · missing keywords · fixes"]
    report --> fix{"Score good<br/>enough?"}
    fix -- no --> improve["Apply fixes<br/>AI rewrites weak bullets"]
    improve --> build
    fix -- yes --> dl["⬇ Download PDF"]
    dl --> done(["Apply for the job"])
```

## 1. Building a resume and exporting the PDF

Everything in this flow happens in the browser. The backend is not needed.

```mermaid
sequenceDiagram
    actor U as User
    participant F as ResumeForm
    participant B as Builder
    participant LS as localStorage
    participant R as renderPdf chunk<br/>(@react-pdf/renderer)

    B->>LS: load saved resume (or sample)
    B->>R: dynamic import() + first render (no delay)
    R-->>B: PDF Blob → object URL → iframe preview
    U->>F: types in a field
    F->>B: onChange(resume)
    B->>LS: autosave
    Note over B: wait 500 ms after the last keystroke
    B->>R: renderPdf(resume, template)
    R-->>B: new Blob (old preview stays until ready)
    U->>B: ⬇ Download PDF
    B->>R: renderPdf(resume, template)
    R-->>U: Name_Resume.pdf
```

## 2. Analyzing an uploaded resume

```mermaid
sequenceDiagram
    actor U as User
    participant A as Analyzer
    participant API as FastAPI /api/analyze
    participant P as parser.py
    participant S as scorer.py

    U->>A: drop file + paste job description
    A->>API: POST multipart (file, job_description)
    API->>API: read ≤ 5 MB + 1 byte
    alt larger than 5 MB
        API-->>A: 413 File is larger than 5 MB
    end
    API->>P: extract_text(filename, bytes) [worker thread]
    alt not .pdf / .docx / .txt
        P-->>API: UnsupportedFileError
        API-->>A: 415
    else corrupt or encrypted
        P-->>API: exception
        API-->>A: 422 Could not read this file
    end
    P-->>API: plain text
    API->>S: analyze(text, job_description) [worker thread]
    S-->>API: report
    API-->>A: 200 report + resume_text
    A->>U: score, breakdown, keywords, issues, weak bullets
```

"From builder" works the same way, except the builder's text (from `resumeToText()`) is sent as JSON
to `POST /api/analyze-text`, so no file parsing happens.

## 3. AI bullet rewrites and summaries (optional)

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Analyzer / Builder
    participant API as FastAPI
    participant L as llm.py
    participant O as Ollama

    UI->>API: GET /api/health (on page load)
    API->>L: status()
    L->>O: GET /api/tags (2 s timeout)
    O-->>L: installed models
    L-->>UI: ai.available = model is installed
    Note over UI: badge shows "AI: llama3.2" or "AI: off"
    U->>UI: Improve weak bullets
    UI->>API: POST /api/ai/rewrite-bullets
    API->>L: build prompt (bullets + job description)
    L->>O: POST /api/generate (format: json, 120 s timeout)
    O-->>L: {"rewrites": [...]}
    L-->>API: parsed list ([] if output is malformed)
    API-->>UI: rewrites
    UI->>U: original (struck out) → improved + Copy
    Note over API,O: If Ollama is unreachable → 503 with a helpful message
```

The model is told never to invent numbers; it uses placeholders like `[X%]` for you to fill in.
"✨ Write with AI" next to the summary field follows the same path via `POST /api/ai/summary`.

## 4. Scoring pipeline

```mermaid
flowchart TD
    t["resume text"] --> words["count words"]
    t --> sections["find short lines → match standard headings"]
    t --> contact["regex: email · phone · LinkedIn/GitHub/URL"]
    t --> bullets["find bullet lines<br/>(fallback: sentence-like lines)"]
    bullets --> verbs["first word in ACTION_VERBS?"]
    bullets --> nums["contains %, $, 2+ digits, 10x?"]
    jd["job description"] --> extract["skills from SKILLS vocabulary<br/>+ words repeated ≥ 2×<br/>(minus stop words and JD_NOISE)"]
    extract --> match["each keyword: found in resume?"]
    t --> match
    t & jd --> tfidf["TF-IDF vectors → cosine similarity"]
    words & sections & contact & verbs & nums & match & tfidf --> weigh["weighted average (rescaled if no JD)"]
    weigh --> issues["issues sorted high → medium → low"]
    issues --> report(["JSON report"])
```

## Development workflow

```mermaid
flowchart LR
    fork["Fork / clone"] --> branch["git checkout -b feature/x"]
    branch --> code["Change code"]
    code --> test["pytest (backend)<br/>npm run build (frontend)"]
    test -- fails --> code
    test -- passes --> push["git push"]
    push --> pr["Open pull request"]
    pr --> ci["GitHub Actions CI<br/>backend tests · frontend build"]
    ci -- red --> code
    ci -- green --> review["Review"] --> merge(["Merge to main"])
```

CI is defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) and runs on every push and
pull request to `main`.
