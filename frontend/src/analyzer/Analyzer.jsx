import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Results } from "./Results";

function BulletRewriter({ bullets, jobDescription }) {
  const [rewrites, setRewrites] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    try {
      const { rewrites } = await api.rewriteBullets(bullets, jobDescription);
      setRewrites(rewrites);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800">✨ AI bullet point rewrites</h3>
          <p className="text-xs text-slate-500">Runs on your local model via Ollama. Nothing leaves your machine.</p>
        </div>
        <button className="btn btn-primary" onClick={run} disabled={loading}>
          {loading ? "Rewriting..." : rewrites ? "Try again" : `Improve ${bullets.length} weak bullets`}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      {rewrites && (
        <ul className="mt-4 space-y-3">
          {rewrites.map((r, i) => (
            <li key={i} className="rounded-md border border-slate-200 p-3 text-sm">
              <p className="text-slate-500 line-through">{r.original}</p>
              <div className="mt-1 flex items-start justify-between gap-2">
                <p className="text-slate-900">{r.improved}</p>
                <button
                  className="shrink-0 text-xs text-indigo-600 hover:underline"
                  onClick={() => navigator.clipboard.writeText(r.improved)}
                >
                  Copy
                </button>
              </div>
            </li>
          ))}
          {!rewrites.length && <li className="text-sm text-slate-500">The model returned no suggestions. Try again.</li>}
        </ul>
      )}
    </div>
  );
}

export function Analyzer({ builderText, aiAvailable }) {
  const [mode, setMode] = useState(builderText ? "builder" : "upload");
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [analyzedJd, setAnalyzedJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  useEffect(() => {
    if (builderText) setMode("builder");
  }, [builderText]);

  const canAnalyze = mode === "upload" ? !!file : !!builderText;

  async function analyze() {
    setLoading(true);
    setError("");
    try {
      const res =
        mode === "upload"
          ? await api.analyzeFile(file, jobDescription)
          : await api.analyzeText(builderText, jobDescription);
      setResult(res);
      setAnalyzedJd(jobDescription.trim());
    } catch (e) {
      setError(e.message === "Failed to fetch" ? "Cannot reach the backend. Is it running on port 8000?" : e.message);
    } finally {
      setLoading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  const weakBullets = result?.weak_bullets?.length ? result.weak_bullets : [];

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
      <div className="space-y-4">
        <div className="card space-y-4">
          <div className="flex rounded-lg bg-slate-100 p-1 text-sm">
            {[
              ["upload", "Upload resume"],
              ["builder", "From builder"],
            ].map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                className={`flex-1 rounded-md py-1.5 font-medium ${mode === key ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}`}
              >
                {label}
              </button>
            ))}
          </div>

          {mode === "upload" ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current.click()}
              className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition ${dragging ? "border-indigo-500 bg-indigo-50" : "border-slate-300 hover:border-indigo-400"}`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <span className="text-3xl">📄</span>
              {file ? (
                <p className="mt-2 text-sm font-medium text-slate-800">{file.name}</p>
              ) : (
                <>
                  <p className="mt-2 text-sm font-medium text-slate-800">Drop your resume here or click to browse</p>
                  <p className="text-xs text-slate-500">PDF, DOCX or TXT, up to 5 MB</p>
                </>
              )}
            </div>
          ) : builderText ? (
            <pre className="max-h-48 overflow-auto rounded-md bg-slate-50 p-3 text-xs whitespace-pre-wrap text-slate-600">{builderText}</pre>
          ) : (
            <p className="text-sm text-slate-500">Build a resume in the Builder tab, then click “Check ATS score”.</p>
          )}

          <label className="block">
            <span className="label">Job description <span className="font-normal text-slate-400">(optional, but recommended)</span></span>
            <textarea
              className="input"
              rows={8}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job posting here to check keyword match..."
            />
          </label>

          <button className="btn btn-primary w-full" disabled={!canAnalyze || loading} onClick={analyze}>
            {loading ? "Analyzing..." : "Analyze resume"}
          </button>
          {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </div>
      </div>

      <div className="space-y-6">
        {result ? (
          <>
            <Results result={result} hasJobDescription={!!analyzedJd} />
            {weakBullets.length > 0 &&
              (aiAvailable ? (
                <BulletRewriter key={weakBullets.join("|")} bullets={weakBullets} jobDescription={analyzedJd} />
              ) : (
                <div className="card text-sm text-slate-600">
                  <h3 className="font-semibold text-slate-800">Weak bullet points</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {weakBullets.map((b, i) => <li key={i}>{b}</li>)}
                  </ul>
                  <p className="mt-3 text-xs text-slate-500">
                    These lack an action verb and a measurable result. Install{" "}
                    <a className="text-indigo-600 underline" href="https://ollama.com" target="_blank" rel="noreferrer">Ollama</a>{" "}
                    and run <code className="rounded bg-slate-100 px-1">ollama pull llama3.2</code> to get AI rewrites.
                  </p>
                </div>
              ))}
          </>
        ) : (
          <div className="card flex h-full min-h-64 flex-col items-center justify-center text-center text-slate-500">
            <span className="text-4xl">🎯</span>
            <p className="mt-3 font-medium text-slate-700">Your ATS report will appear here</p>
            <p className="mt-1 max-w-sm text-sm">
              Scoring runs locally with open-source tools: keyword matching, TF-IDF similarity and formatting checks.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
