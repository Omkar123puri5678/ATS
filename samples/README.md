# Sample resumes

Fictional resumes and job descriptions for trying out the analyzer. All names, companies, emails and
phone numbers are made up.

| Resume | What it shows |
|---|---|
| `01_strong_software_engineer` | Clear sections, action verbs, numbers: scores around 90 against the matching job |
| `02_average_data_analyst` | Weak verbs ("responsible for", "helped"), few numbers, no summary |
| `03_weak_no_structure` | No headings, no contact info, first-person paragraphs: scores very low |
| `04_fresher_student` | Student resume with projects and an internship |
| `05_digital_marketing` | Non-tech field: scores well for marketing, poorly for engineering jobs |

Job descriptions are in `job_descriptions/`. Paste one into the Analyzer next to a resume.

## Use them in the app

1. Open the app and go to **Analyzer**.
2. Upload a file from `samples/resumes/` (PDF, DOCX or TXT).
3. Paste a job description from `samples/job_descriptions/` and click **Analyze**.

Try the same resume against different jobs to see the keyword score change.

## Score them all at once

```powershell
backend\.venv\Scripts\python samples\score_all.py              # the samples
backend\.venv\Scripts\python samples\score_all.py D:\my-resumes  # any folder of your own
```

This prints a table of every resume against every job description, using the same engine as the app.

## Make your own

Edit the `RESUMES` or `JOBS` lists in `generate.py`, then run it again (it needs `pip install fpdf2`).
