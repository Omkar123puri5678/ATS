# Contributing

Thanks for helping improve ATS Resume Maker! By taking part, you agree to follow our
[Code of Conduct](CODE_OF_CONDUCT.md). To report a security issue, see [SECURITY.md](SECURITY.md).

## Getting set up

Follow the "Run locally" steps in the [README](README.md), and read the
[Developer Guide](docs/DEVELOPER_GUIDE.md) and [Architecture](docs/ARCHITECTURE.md). Run the backend tests with `pytest` from `backend/`.

## Ways to contribute

- **Skills vocabulary:** add terms for your field to `backend/app/skills.py` (lowercase).
- **Templates:** add an entry to `TEMPLATES` in `frontend/src/builder/templates.js`.
  Keep templates ATS-friendly: single column, standard fonts, standard headings, no images or tables.
- **Scoring:** improve checks in `backend/app/scorer.py`. Please add a test in `backend/tests/` for any change.
- **Bugs and ideas:** open an issue with steps to reproduce or a short description.

## Pull requests

1. Fork the repo and create a branch: `git checkout -b feature/my-change`
2. Make your change and make sure `pytest` and `npm run build` pass
3. Open a pull request describing what changed and why

## Principles

- **Free and private by default.** No paid APIs, no tracking, and resumes are never stored.
- **AI is optional.** Every feature except AI rewrites must work without Ollama.
