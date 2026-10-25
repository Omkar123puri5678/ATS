# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-25

### Added
- Resume Builder with a guided form, live PDF preview, 3 ATS-friendly templates
  (Classic, Modern, Compact) and autosave to the browser
- PDF export with real, selectable text
- ATS Analyzer: upload a PDF, DOCX or TXT and get a 0–100 score with a per-category breakdown
- Keyword matching against a job description, showing matched and missing keywords
- Checks for sections, contact info, action verbs, quantified results and length
- Optional AI bullet rewrites and summary generation with local Ollama models
- Docker Compose setup
- User guide, architecture, workflow and developer docs
- GitHub Actions CI for backend tests and the frontend build

### Changed
- The PDF renderer loads only when it's needed, so the app opens faster
- Nginx serves static files with gzip compression and caching
- File parsing and scoring run in worker threads, so the API stays responsive

[Unreleased]: https://github.com/Omkar123puri5678/ATS/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Omkar123puri5678/ATS/releases/tag/v0.1.0
