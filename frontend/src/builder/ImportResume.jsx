import { useRef, useState } from "react";
import { api } from "../api";

// Upload an existing resume in any layout; the local AI model extracts every
// section and rewrites it into the builder's ATS-friendly format.
export function ImportResume({ aiAvailable, onImported }) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [scores, setScores] = useState(null);
  const inputRef = useRef();

  async function build() {
    setLoading(true);
    setError("");
    setScores(null);
    try {
      const res = await api.buildResume(file, jobDescription);
      onImported(res.resume);
      setScores({
        before: res.score_before,
        after: res.score_after,
        tailored: !!jobDescription.trim(),
        dropped: res.dropped_skills || [],
        restored: res.restored_skills || [],
        masked: res.masked_numbers || [],
      });
      setOpen(false);
    } catch (e) {
      setError(e.message === "Failed to fetch" ? "Cannot reach the backend. Is it running on port 8000?" : e.message);
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <div className="card mb-4 border-indigo-200 bg-indigo-50/50">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-slate-800">✨ Already have a resume?</h3>
            <p className="text-xs text-slate-500">
              Upload it and the AI rebuilds it here in an ATS-friendly format. You can edit everything before downloading.
            </p>
          </div>
          <button
            className="btn btn-primary"
            disabled={!aiAvailable}
            title={aiAvailable ? "" : "Start Ollama to enable AI features"}
            onClick={() => setOpen(true)}
          >
            Upload &amp; rebuild with AI
          </button>
        </div>
        {!aiAvailable && (
          <p className="mt-2 text-xs text-slate-500">
            Needs a local AI model: install{" "}
            <a className="text-indigo-600 underline" href="https://ollama.com" target="_blank" rel="noreferrer">Ollama</a>{" "}
            and run <code className="rounded bg-slate-100 px-1">ollama pull llama3.2</code>.
          </p>
        )}
        {scores && (
          <p className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">
            Resume rebuilt. ATS score{scores.tailored ? " for this job" : ""}: <b>{scores.before}</b> → <b>{scores.after}</b>.
            Review every section below: fill in any <code>[X%]</code> placeholders with your real numbers, and fix anything the AI got wrong.
            {scores.dropped.length > 0 && (
              <span className="mt-1 block text-xs text-emerald-700">
                Removed skills the AI added that are not in your original resume: {scores.dropped.join(", ")}. Add them back only if you really have them.
              </span>
            )}
            {scores.masked.length > 0 && (
              <span className="mt-1 block text-xs font-medium text-amber-700">
                The AI made up {scores.masked.length} number(s) that are not in your original resume. They were
                replaced with [X] placeholders: put in your real figures or remove them.
              </span>
            )}
            {scores.restored.length > 0 && (
              <span className="mt-1 block text-xs text-emerald-700">
                Added back skills from your original resume that the AI left out: {scores.restored.join(", ")}.
              </span>
            )}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="card mb-4 space-y-4 border-indigo-200">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">✨ Rebuild my resume with AI</h3>
        <button className="text-sm text-slate-500 hover:text-slate-800" onClick={() => setOpen(false)} disabled={loading}>
          Cancel
        </button>
      </div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
        }}
        onClick={() => inputRef.current.click()}
        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 p-6 text-center hover:border-indigo-400"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <span className="text-2xl">📄</span>
        <p className="mt-1 text-sm font-medium text-slate-800">{file ? file.name : "Drop your current resume or click to browse"}</p>
        {!file && <p className="text-xs text-slate-500">PDF, DOCX or TXT, up to 5 MB</p>}
      </div>
      <label className="block">
        <span className="label">
          Job description <span className="font-normal text-slate-400">(optional: tailors the resume to this job)</span>
        </span>
        <textarea
          className="input"
          rows={5}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the job posting here..."
        />
      </label>
      <p className="text-xs text-amber-700">This replaces what is currently in the builder.</p>
      <button className="btn btn-primary w-full" disabled={!file || loading} onClick={build}>
        {loading ? "Reading and rebuilding your resume (this can take a minute)..." : "Build my ATS-friendly resume"}
      </button>
      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    </div>
  );
}
