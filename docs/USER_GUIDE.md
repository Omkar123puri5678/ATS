# User Guide

This guide walks through building a resume, checking it against a job, and using the optional AI
features. To install the app, see [Getting started](../README.md#getting-started).

## Contents

1. [Building a resume](#1-building-a-resume)
2. [Downloading the PDF](#2-downloading-the-pdf)
3. [Checking your ATS score](#3-checking-your-ats-score)
4. [Reading the report](#4-reading-the-report)
5. [AI suggestions](#5-ai-suggestions-optional)
6. [Tips for a high score](#6-tips-for-a-high-score)
7. [Troubleshooting](#7-troubleshooting)
8. [Privacy](#8-privacy)

## 1. Building a resume

Open the **Resume Builder** tab (it opens by default).

1. The form starts with a **sample resume** so you can see how it looks. Click **Clear** to start
   blank, or edit the sample directly. **Load sample** brings it back.
2. Fill in each section:

   | Section | Tips |
   |---|---|
   | Personal details | Name, job title, email, phone, location. Put links comma-separated: `linkedin.com/in/you, github.com/you` |
   | Professional summary | 2–3 sentences. Click **✨ Write with AI** to draft one (needs Ollama). |
   | Experience | One entry per role. Click **Add experience** for more. Write **one bullet per line**. |
   | Projects | Name, tech used, link, and bullets (one per line). |
   | Education | Degree, school, dates, and details such as CGPA or coursework. |
   | Skills & certifications | Skills: one group per line, e.g. `Languages: Python, Java`. Certifications: one per line. |

3. Pick a template from the dropdown: **Classic**, **Modern** or **Compact**. All three are
   single-column with standard fonts, which is what ATS software reads best.
4. The preview on the right updates about half a second after you stop typing.

Your work **autosaves in your browser**. Closing the tab is safe; it will be there when you return
on the same browser. Clearing browser data or using a private window removes it.

## 2. Downloading the PDF

Click **⬇ Download PDF**. The file is named `Your_Name_Resume.pdf`. The PDF contains real,
selectable text (not an image), so ATS software can read every word.

## 3. Checking your ATS score

There are two ways to get a resume into the analyzer:

- **From the builder:** click **Check ATS score →** under the preview. The app switches to the
  **ATS Analyzer** tab with your resume loaded.
- **Upload a file:** open the **ATS Analyzer** tab, choose **Upload resume**, and drop a **PDF, DOCX
  or TXT** file (up to 5 MB) onto the box, or click it to browse.

Then:

1. Paste the **job description** of the role you're applying for. It's optional, but without it the
   keyword match (the biggest part of the score) is skipped.
2. Click **Analyze resume**.

## 4. Reading the report

**Overall score (0–100).** The ring is colour-coded: **75+** green (strong), **50–74** amber (worth tuning),
**below 50** red (likely to be filtered out).

**Breakdown.** Each category shows its own score and weight:

| Category | Weight | What it checks | How to improve |
|---|---|---|---|
| Keyword match | 35 | Skills and repeated terms from the job description found in your resume | Add missing keywords you genuinely have, in Skills or bullets |
| Content relevance | 10 | Overall wording similarity to the job description | Describe your work using the job's language |
| Sections | 20 | Standard headings: Experience, Education, Skills (+ Summary, Projects, Certifications) | Use those exact heading names |
| Contact info | 10 | Email, phone, and a LinkedIn/GitHub/portfolio link | Add whatever is missing |
| Impact | 15 | Bullets that start with an action verb and include a number | "Reduced load time by 40%" beats "Responsible for performance" |
| Length | 10 | 300–1000 words | Trim or expand accordingly |

Without a job description, keyword match and relevance are skipped and the other weights are scaled up.

**Keywords.** Green chips are keywords you have; red chips are missing. Only add the ones that are
true for you.

**What to fix.** A list of issues sorted by priority: **high**, then **medium**, then **low**.

**Sections detected.** Which standard headings the analyzer found.

**Weak bullet points.** Up to 5 bullets that have neither an action verb nor a number.

## 5. AI suggestions (optional)

AI features run on a free model on your own computer. Setup:

1. Install [Ollama](https://ollama.com/download).
2. In a terminal: `ollama pull llama3.2`
3. Reload the app. The badge in the top-right changes from **AI: off** to **AI: llama3.2**.

Then you can:

- **Rewrite weak bullets:** after an analysis, click **Improve N weak bullets**. Each suggestion
  shows the original (struck through) and the improved version with a **Copy** button. The model
  won't invent numbers; it leaves placeholders like `[X%]` for you to fill in with real figures.
- **Write a summary:** in the builder, click **✨ Write with AI** next to Professional summary.

AI output can be wrong. Always read it and keep only what's accurate.

## 6. Tips for a high score

- Tailor your resume to each job: paste its description and close the keyword gaps.
- Use the standard heading names: **Experience**, **Education**, **Skills**.
- Start every bullet with a verb (*built, led, improved, automated*) and add a number where you can.
- Keep it to one page (two at most for senior roles).
- Don't use tables, text boxes, columns, icons or photos in resumes you make elsewhere. ATS
  software often scrambles them. The builder's templates already avoid all of these.
- If you upload a PDF and get a very low word count, your PDF is probably a scanned image. Export
  it again from Word or Google Docs, or rebuild it in the builder.

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| Yellow banner: "Backend is not reachable" | Start the backend (`uvicorn app.main:app --port 8000` in `backend/`) or run `docker compose up`. The builder still works without it. |
| "Cannot reach the backend. Is it running on port 8000?" | Same as above. |
| "File is larger than 5 MB" | Compress the PDF or export it again without images. |
| "Only .pdf, .docx and .txt files are supported" | Save the file in one of those formats. `.doc` (old Word) isn't supported. |
| "Could not read this file" | The file may be password-protected or corrupted. Export it again. |
| Very low word count on a PDF that looks fine | The PDF is an image. ATS can't read it either. Use a text-based PDF. |
| Badge stays "AI: off" | Check Ollama is running (`ollama list`) and the model is pulled. If you use a different model, set `OLLAMA_MODEL`. |
| "Could not reach Ollama" | Ollama stopped or is on another address. Set `OLLAMA_URL`. |
| Preview stuck on "Rendering preview..." | Reload the page. If it says "Could not render the preview", check your connection, since the PDF engine loads separately. |
| My resume disappeared | Autosave is per-browser. It won't carry over to another browser, device or private window. |

## 8. Privacy

- Resumes are processed in memory and **never stored** on the server.
- No paid or third-party APIs are called. AI runs on your own machine through Ollama.
- The builder autosaves only to your own browser's local storage.
