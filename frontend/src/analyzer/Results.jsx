const LABELS = {
  keywords: "Keyword match",
  similarity: "Content relevance",
  sections: "Sections",
  contact: "Contact info",
  impact: "Impact (verbs & numbers)",
  length: "Length",
};

const color = (score) =>
  score >= 75 ? "text-emerald-600" : score >= 50 ? "text-amber-500" : "text-red-600";
const barColor = (score) =>
  score >= 75 ? "bg-emerald-500" : score >= 50 ? "bg-amber-400" : "bg-red-500";

function ScoreRing({ score }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" strokeWidth="10" className="stroke-slate-200" />
        <circle
          cx="60" cy="60" r={r} fill="none" strokeWidth="10" strokeLinecap="round"
          className={`stroke-current ${color(score)} transition-all duration-700`}
          strokeDasharray={c}
          strokeDashoffset={c * (1 - score / 100)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold ${color(score)}`}>{score}</span>
        <span className="text-xs text-slate-500">ATS score</span>
      </div>
    </div>
  );
}

const SEVERITY = {
  high: "bg-red-50 text-red-800 border-red-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  low: "bg-slate-50 text-slate-700 border-slate-200",
};

export function Results({ result, hasJobDescription }) {
  const verdict =
    result.score >= 80 ? "Strong. This resume should pass most ATS filters."
    : result.score >= 60 ? "Decent, but a few fixes will noticeably improve your chances."
    : "Needs work. Fix the high-priority issues below first.";

  return (
    <div className="space-y-6">
      <div className="card flex flex-col items-center gap-6 sm:flex-row">
        <ScoreRing score={result.score} />
        <div className="flex-1 space-y-3 self-stretch">
          <p className="font-medium text-slate-800">{verdict}</p>
          {Object.entries(result.breakdown).map(([key, { score }]) => (
            <div key={key}>
              <div className="flex justify-between text-xs text-slate-600">
                <span>{LABELS[key] || key}</span>
                <span>{score}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div className={`h-2 rounded-full ${barColor(score)}`} style={{ width: `${score}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {hasJobDescription ? (
        <div className="card">
          <h3 className="font-semibold text-slate-800">Keywords from the job description</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {result.keywords.matched.map((k) => (
              <span key={k} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">✓ {k}</span>
            ))}
            {result.keywords.missing.map((k) => (
              <span key={k} className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">✗ {k}</span>
            ))}
            {!result.keywords.matched.length && !result.keywords.missing.length && (
              <p className="text-sm text-slate-500">No clear keywords found in the job description.</p>
            )}
          </div>
        </div>
      ) : (
        <p className="rounded-md bg-indigo-50 p-3 text-sm text-indigo-800">
          Tip: paste a job description to see which keywords you are missing.
        </p>
      )}

      <div className="card">
        <h3 className="font-semibold text-slate-800">What to fix</h3>
        {result.issues.length ? (
          <ul className="mt-3 space-y-2">
            {result.issues.map((issue, i) => (
              <li key={i} className={`rounded-md border px-3 py-2 text-sm ${SEVERITY[issue.severity]}`}>
                <span className="mr-2 text-xs font-semibold uppercase">{issue.severity}</span>
                {issue.message}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-600">No issues found. Nice work!</p>
        )}
      </div>

      <div className="card">
        <h3 className="font-semibold text-slate-800">Sections detected</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(result.sections).map(([name, found]) => (
            <span
              key={name}
              className={`rounded-md px-2.5 py-1 text-xs capitalize ${found ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-400 line-through"}`}
            >
              {name}
            </span>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">{result.word_count} words</p>
      </div>
    </div>
  );
}
