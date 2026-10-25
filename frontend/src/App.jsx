import { useEffect, useState } from "react";
import { api } from "./api";
import { Builder } from "./builder/Builder";
import { Analyzer } from "./analyzer/Analyzer";

const TABS = [
  ["builder", "Resume Builder"],
  ["analyzer", "ATS Analyzer"],
];

export default function App() {
  const [tab, setTab] = useState("builder");
  const [ai, setAi] = useState({ available: false });
  const [backendUp, setBackendUp] = useState(null);
  const [builderText, setBuilderText] = useState("");

  useEffect(() => {
    api
      .health()
      .then((h) => {
        setBackendUp(true);
        setAi(h.ai);
      })
      .catch(() => setBackendUp(false));
  }, []);

  function analyzeFromBuilder(text) {
    setBuilderText(text);
    setTab("analyzer");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">📄 ATS Resume Maker</h1>
            <p className="text-xs text-slate-500">Open-source resume builder with an AI-powered ATS analyzer</p>
          </div>
          <nav className="flex rounded-lg bg-slate-100 p-1">
            {TABS.map(([key, label]) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`rounded-md px-4 py-1.5 text-sm font-medium ${tab === key ? "bg-white text-indigo-700 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                {label}
              </button>
            ))}
          </nav>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${ai.available ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}
            title={ai.available ? `Using ${ai.model} via Ollama` : "Start Ollama to enable AI suggestions"}
          >
            {ai.available ? `AI: ${ai.model}` : "AI: off"}
          </span>
        </div>
      </header>

      {backendUp === false && (
        <div className="bg-amber-50 px-4 py-2 text-center text-sm text-amber-800">
          Backend is not reachable. The builder still works, but scoring needs the API running on port 8000.
        </div>
      )}

      <main className="mx-auto max-w-7xl px-4 py-6">
        {/* Both tabs stay mounted so form state and results survive switching. */}
        <div hidden={tab !== "builder"}>
          <Builder aiAvailable={ai.available} onAnalyze={analyzeFromBuilder} />
        </div>
        <div hidden={tab !== "analyzer"}>
          <Analyzer builderText={builderText} aiAvailable={ai.available} />
        </div>
      </main>

      <footer className="py-6 text-center text-xs text-slate-400">
        MIT licensed · Your resume is processed locally and never stored.
      </footer>
    </div>
  );
}
