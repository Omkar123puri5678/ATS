async function request(path, options) {
  const res = await fetch(`/api${path}`, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return body;
}

const json = (data) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

export const api = {
  health: () => request("/health"),

  analyzeFile(file, jobDescription) {
    const form = new FormData();
    form.append("file", file);
    form.append("job_description", jobDescription);
    return request("/analyze", { method: "POST", body: form });
  },

  analyzeText: (resumeText, jobDescription) =>
    request("/analyze-text", json({ resume_text: resumeText, job_description: jobDescription })),

  rewriteBullets: (bullets, jobDescription) =>
    request("/ai/rewrite-bullets", json({ bullets, job_description: jobDescription })),

  summary: (resumeText, jobDescription) =>
    request("/ai/summary", json({ resume_text: resumeText, job_description: jobDescription })),
};
