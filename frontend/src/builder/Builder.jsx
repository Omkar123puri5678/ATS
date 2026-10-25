import { useEffect, useRef, useState } from "react";
import { ResumeForm } from "./ResumeForm";
import { TEMPLATES } from "./templates";
import { blankResume, resumeToText, sampleResume } from "../resume";
import { api } from "../api";

const STORAGE_KEY = "ats-resume-maker:resume";

// @react-pdf/renderer is most of the bundle, so it is loaded in its own chunk
// after the page has rendered. The promise is shared so it downloads once.
let rendererPromise;
function renderPdf(resume, template) {
  rendererPromise ??= import("./renderPdf").catch((e) => {
    rendererPromise = undefined; // allow a retry after a network error
    throw e;
  });
  return rendererPromise.then((m) => m.renderPdf(resume, template));
}

function loadSaved() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved?.resume) return saved;
  } catch {
    // ignore unreadable storage
  }
  return { resume: sampleResume, template: "modern" };
}

// Re-renders the PDF shortly after the user stops typing.
function usePdfUrl(resume, template) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState("");
  const rendered = useRef(false);
  useEffect(() => {
    let cancelled = false;
    let objectUrl;
    // The first preview renders right away; later ones wait for a pause in typing.
    const timer = setTimeout(async () => {
      try {
        const blob = await renderPdf(resume, template);
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        rendered.current = true;
        setUrl(objectUrl);
        setError("");
      } catch {
        if (!cancelled) setError("Could not render the preview. Check your connection and try editing again.");
      }
    }, rendered.current ? 500 : 0);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      // Keep the previous preview visible until the next one is ready.
      if (objectUrl) setTimeout(() => URL.revokeObjectURL(objectUrl), 5000);
    };
  }, [resume, template]);
  return { url, error };
}

export function Builder({ aiAvailable, onAnalyze }) {
  const [{ resume, template }, setState] = useState(loadSaved);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [error, setError] = useState("");
  const { url: pdfUrl, error: previewError } = usePdfUrl(resume, template);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ resume, template }));
    } catch {
      // storage may be unavailable (private mode); autosave is best-effort
    }
  }, [resume, template]);

  const setResume = (next) => setState((s) => ({ ...s, resume: next }));
  const setTemplate = (next) => setState((s) => ({ ...s, template: next }));

  const fileName = `${(resume.name || "resume").trim().replace(/\s+/g, "_")}_Resume.pdf`;

  async function download() {
    setError("");
    let blob;
    try {
      blob = await renderPdf(resume, template);
    } catch {
      setError("Could not create the PDF. Check your connection and try again.");
      return;
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fileName;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  async function generateSummary() {
    setGeneratingSummary(true);
    setError("");
    try {
      const { summary } = await api.summary(resumeToText({ ...resume, summary: "" }), "");
      if (summary) setResume({ ...resume, summary });
    } catch (e) {
      setError(e.message);
    } finally {
      setGeneratingSummary(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <select className="input w-auto" value={template} onChange={(e) => setTemplate(e.target.value)} aria-label="Template">
            {Object.entries(TEMPLATES).map(([key, t]) => (
              <option key={key} value={key}>{t.label} template</option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={() => setResume(sampleResume)}>Load sample</button>
          <button
            className="btn btn-secondary"
            onClick={() => confirm("Clear all fields?") && setResume(blankResume)}
          >
            Clear
          </button>
        </div>
        {error && <p className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <ResumeForm
          resume={resume}
          onChange={setResume}
          aiAvailable={aiAvailable}
          onGenerateSummary={generateSummary}
          generatingSummary={generatingSummary}
        />
      </div>

      <div className="lg:sticky lg:top-6 lg:self-start">
        <div className="mb-4 flex flex-wrap gap-2">
          <button className="btn btn-primary" onClick={download}>⬇ Download PDF</button>
          <button className="btn btn-secondary" onClick={() => onAnalyze(resumeToText(resume))}>
            Check ATS score →
          </button>
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
          {pdfUrl ? (
            <iframe title="Resume preview" src={`${pdfUrl}#toolbar=0&navpanes=0`} className="h-[80vh] w-full" />
          ) : (
            <div className="flex h-[80vh] items-center justify-center text-sm text-slate-500">
              {previewError || "Rendering preview..."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
