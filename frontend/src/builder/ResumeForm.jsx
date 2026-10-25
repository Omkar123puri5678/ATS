import { emptyEducation, emptyExperience, emptyProject } from "../resume";

function Field({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      <input type={type} className="input" value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function Area({ label, value, onChange, placeholder, rows = 4, hint }) {
  return (
    <label className="block">
      <span className="label">
        {label}
        {hint ? <span className="ml-1 font-normal text-slate-400">({hint})</span> : null}
      </span>
      <textarea className="input" rows={rows} value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function Group({ title, children, action }) {
  return (
    <details open className="card group">
      <summary className="flex cursor-pointer list-none items-center justify-between">
        <h3 className="font-semibold text-slate-800">{title}</h3>
        <span className="text-slate-400 transition group-open:rotate-90">›</span>
      </summary>
      <div className="mt-4 space-y-3">
        {children}
        {action}
      </div>
    </details>
  );
}

function ListEditor({ items, onChange, make, render, addLabel }) {
  const update = (i, patch) => onChange(items.map((it, j) => (j === i ? { ...it, ...patch } : it)));
  const remove = (i) => onChange(items.filter((_, j) => j !== i));
  const move = (i, d) => {
    const next = [...items];
    const [it] = next.splice(i, 1);
    next.splice(i + d, 0, it);
    onChange(next);
  };
  return (
    <>
      {items.map((item, i) => (
        <div key={i} className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
          {render(item, (patch) => update(i, patch))}
          <div className="flex justify-end gap-3 text-xs">
            {i > 0 && <button className="text-slate-500 hover:text-slate-800" onClick={() => move(i, -1)}>Move up</button>}
            {i < items.length - 1 && <button className="text-slate-500 hover:text-slate-800" onClick={() => move(i, 1)}>Move down</button>}
            <button className="text-red-600 hover:text-red-800" onClick={() => remove(i)}>Remove</button>
          </div>
        </div>
      ))}
      <button className="btn btn-secondary w-full" onClick={() => onChange([...items, make()])}>+ {addLabel}</button>
    </>
  );
}

export function ResumeForm({ resume: r, onChange, aiAvailable, onGenerateSummary, generatingSummary }) {
  const set = (key) => (value) => onChange({ ...r, [key]: value });

  return (
    <div className="space-y-4">
      <Group title="Personal details">
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Full name" value={r.name} onChange={set("name")} placeholder="Priya Sharma" />
          <Field label="Job title" value={r.title} onChange={set("title")} placeholder="Software Engineer" />
          <Field label="Email" type="email" value={r.email} onChange={set("email")} placeholder="you@example.com" />
          <Field label="Phone" value={r.phone} onChange={set("phone")} placeholder="+91 98765 43210" />
          <Field label="Location" value={r.location} onChange={set("location")} placeholder="City, Country" />
          <Field label="Links (comma separated)" value={r.links} onChange={set("links")} placeholder="linkedin.com/in/you, github.com/you" />
        </div>
      </Group>

      <Group title="Summary">
        <Area label="Professional summary" value={r.summary} onChange={set("summary")} rows={3} placeholder="2-3 sentences about who you are and what you bring." />
        {aiAvailable && (
          <button className="btn btn-secondary" onClick={onGenerateSummary} disabled={generatingSummary}>
            {generatingSummary ? "Writing..." : "✨ Write with AI"}
          </button>
        )}
      </Group>

      <Group title="Experience">
        <ListEditor
          items={r.experience}
          onChange={set("experience")}
          make={emptyExperience}
          addLabel="Add experience"
          render={(e, up) => (
            <>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Role" value={e.role} onChange={(v) => up({ role: v })} />
                <Field label="Company" value={e.company} onChange={(v) => up({ company: v })} />
                <Field label="Location" value={e.location} onChange={(v) => up({ location: v })} />
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Start" value={e.start} onChange={(v) => up({ start: v })} placeholder="Jun 2025" />
                  <Field label="End" value={e.end} onChange={(v) => up({ end: v })} placeholder="Present" />
                </div>
              </div>
              <Area label="Bullet points" hint="one per line" value={e.bullets} onChange={(v) => up({ bullets: v })} placeholder="Built X that did Y, improving Z by 30%" />
            </>
          )}
        />
      </Group>

      <Group title="Projects">
        <ListEditor
          items={r.projects}
          onChange={set("projects")}
          make={emptyProject}
          addLabel="Add project"
          render={(p, up) => (
            <>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Project name" value={p.name} onChange={(v) => up({ name: v })} />
                <Field label="Tech used" value={p.tech} onChange={(v) => up({ tech: v })} placeholder="React, Node.js" />
              </div>
              <Field label="Link" value={p.link} onChange={(v) => up({ link: v })} placeholder="github.com/you/project" />
              <Area label="Bullet points" hint="one per line" value={p.bullets} onChange={(v) => up({ bullets: v })} rows={3} />
            </>
          )}
        />
      </Group>

      <Group title="Education">
        <ListEditor
          items={r.education}
          onChange={set("education")}
          make={emptyEducation}
          addLabel="Add education"
          render={(e, up) => (
            <>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Degree" value={e.degree} onChange={(v) => up({ degree: v })} />
                <Field label="School / University" value={e.school} onChange={(v) => up({ school: v })} />
                <Field label="Start" value={e.start} onChange={(v) => up({ start: v })} />
                <Field label="End" value={e.end} onChange={(v) => up({ end: v })} />
              </div>
              <Field label="Details" value={e.details} onChange={(v) => up({ details: v })} placeholder="CGPA, honours, relevant coursework" />
            </>
          )}
        />
      </Group>

      <Group title="Skills & certifications">
        <Area label="Skills" hint="one group per line, e.g. Languages: Python, Java" value={r.skills} onChange={set("skills")} />
        <Area label="Certifications" hint="one per line" value={r.certifications} onChange={set("certifications")} rows={2} />
      </Group>
    </div>
  );
}
