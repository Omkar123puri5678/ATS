# Security Policy

## Supported versions

Only the latest version on the `main` branch gets security fixes.

## Reporting a vulnerability

**Please don't open a public issue for security problems.**

Report it privately through
[GitHub Security Advisories](https://github.com/Omkar123puri5678/ATS/security/advisories/new).
Include:

- What the issue is and where it is (file, endpoint or component)
- Steps to reproduce it, or a proof of concept
- What an attacker could do with it

You'll get a reply within 7 days. Once the issue is confirmed, a fix will be released as soon as
possible and you'll be credited in the release notes, unless you'd rather not be.

## How the app handles data

- Uploaded resumes are processed in memory and are **never written to disk** on the server.
- Uploads are limited to 5 MB.
- The resume builder saves drafts only in your browser's local storage.
- AI features call a **local** Ollama instance. No resume data is sent to third-party APIs.
- The app is designed to run on your own machine. If you host it publicly, serve it over HTTPS,
  restrict `CORS_ORIGINS` to your domain, and add rate limiting.
