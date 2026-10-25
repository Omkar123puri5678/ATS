// Resume data model shared by the form, the PDF templates and the analyzer.

export const emptyExperience = () => ({ role: "", company: "", location: "", start: "", end: "", bullets: "" });
export const emptyEducation = () => ({ degree: "", school: "", start: "", end: "", details: "" });
export const emptyProject = () => ({ name: "", tech: "", link: "", bullets: "" });

export const sampleResume = {
  name: "Priya Sharma",
  title: "Software Engineer Intern",
  email: "priya.sharma@example.com",
  phone: "+91 98765 43210",
  location: "Pune, India",
  links: "linkedin.com/in/priyasharma, github.com/priyasharma",
  summary:
    "Computer science student with hands-on experience building full-stack web apps using React, Node.js and Python. Passionate about clean code, performance and shipping useful products.",
  experience: [
    {
      role: "Software Engineering Intern",
      company: "Acme Corp",
      location: "Remote",
      start: "Jun 2025",
      end: "Aug 2025",
      bullets:
        "Built a React dashboard used by 200+ internal users to track orders in real time\nReduced API response time by 35% by adding Redis caching to Node.js services\nWrote unit tests with Jest, raising coverage from 40% to 85%",
    },
  ],
  education: [
    {
      degree: "B.Tech in Computer Science",
      school: "XYZ University",
      start: "2022",
      end: "2026",
      details: "CGPA: 8.7 / 10",
    },
  ],
  projects: [
    {
      name: "ATS Resume Maker",
      tech: "React, FastAPI, scikit-learn, Ollama",
      link: "github.com/priyasharma/ats-resume-maker",
      bullets:
        "Developed an open-source resume builder with ATS scoring and AI suggestions using local LLMs\nImplemented keyword matching and TF-IDF similarity to score resumes against job descriptions",
    },
  ],
  skills:
    "Languages: JavaScript, TypeScript, Python, SQL\nFrameworks: React, Node.js, Express, FastAPI\nTools: Git, Docker, AWS, PostgreSQL, Redis",
  certifications: "AWS Certified Cloud Practitioner (2025)",
};

export const blankResume = {
  name: "",
  title: "",
  email: "",
  phone: "",
  location: "",
  links: "",
  summary: "",
  experience: [emptyExperience()],
  education: [emptyEducation()],
  projects: [],
  skills: "",
  certifications: "",
};

export const lines = (text) =>
  (text || "")
    .split("\n")
    .map((l) => l.replace(/^[-•*\s]+/, "").trim())
    .filter(Boolean);

const range = (start, end) => [start, end].filter(Boolean).join(" - ");

// Plain-text version, laid out the same way an ATS would read the PDF.
export function resumeToText(r) {
  const out = [];
  out.push(r.name, r.title);
  out.push([r.email, r.phone, r.location].filter(Boolean).join(" | "));
  if (r.links) out.push(r.links);

  if (r.summary) out.push("", "Summary", r.summary);

  const exp = r.experience.filter((e) => e.role || e.company);
  if (exp.length) {
    out.push("", "Experience");
    for (const e of exp) {
      out.push(`${e.role}, ${e.company} ${e.location ? `(${e.location})` : ""} ${range(e.start, e.end)}`);
      lines(e.bullets).forEach((b) => out.push(`- ${b}`));
    }
  }

  const proj = r.projects.filter((p) => p.name);
  if (proj.length) {
    out.push("", "Projects");
    for (const p of proj) {
      out.push(`${p.name}${p.tech ? ` | ${p.tech}` : ""}${p.link ? ` | ${p.link}` : ""}`);
      lines(p.bullets).forEach((b) => out.push(`- ${b}`));
    }
  }

  const edu = r.education.filter((e) => e.degree || e.school);
  if (edu.length) {
    out.push("", "Education");
    for (const e of edu) {
      out.push(`${e.degree}, ${e.school} ${range(e.start, e.end)}`);
      if (e.details) out.push(e.details);
    }
  }

  if (r.skills) out.push("", "Skills", ...lines(r.skills));
  if (r.certifications) out.push("", "Certifications", ...lines(r.certifications));

  return out.filter((l) => l !== undefined).join("\n");
}
