import { Document, Page, Text, View, Link, StyleSheet } from "@react-pdf/renderer";
import { lines } from "../resume";
import { TEMPLATES } from "./templates";

function makeStyles(t) {
  const base = t.small ? 9.5 : 10.5;
  return StyleSheet.create({
    page: { padding: t.small ? 30 : 40, fontFamily: t.font, fontSize: base, color: "#111", lineHeight: 1.35 },
    // Explicit lineHeight: the page's relative lineHeight would otherwise be
    // computed from the base font size, making the large name overlap the title.
    name: { fontFamily: t.bold, fontSize: base + 10, lineHeight: 1.2, textAlign: t.align, color: t.accent },
    title: { fontSize: base + 1, textAlign: t.align, marginTop: 4 },
    contact: { fontSize: base - 0.5, textAlign: t.align, marginTop: 4, color: "#333" },
    section: { marginTop: t.small ? 8 : 12 },
    heading: {
      fontFamily: t.bold,
      fontSize: base + 1,
      color: t.accent,
      textTransform: t.headingCase,
      borderBottomWidth: 0.75,
      borderBottomColor: t.accent,
      paddingBottom: 2,
      marginBottom: 5,
    },
    row: { flexDirection: "row", justifyContent: "space-between" },
    bold: { fontFamily: t.bold },
    muted: { color: "#444" },
    item: { marginBottom: t.small ? 4 : 6 },
    bullet: { flexDirection: "row", marginTop: 1.5, paddingLeft: 6 },
    bulletDot: { width: 10 },
    bulletText: { flex: 1 },
    link: { color: "#111", textDecoration: "none" },
  });
}

const range = (s, e) => [s, e].filter(Boolean).join(" - ");

function Bullets({ text, s }) {
  return lines(text).map((b, i) => (
    <View key={i} style={s.bullet} wrap={false}>
      <Text style={s.bulletDot}>•</Text>
      <Text style={s.bulletText}>{b}</Text>
    </View>
  ));
}

function Section({ title, s, children }) {
  return (
    <View style={s.section}>
      <Text style={s.heading}>{title}</Text>
      {children}
    </View>
  );
}

export function ResumePDF({ resume: r, template = "modern" }) {
  const t = TEMPLATES[template] || TEMPLATES.modern;
  const s = makeStyles(t);
  const contact = [r.email, r.phone, r.location].filter(Boolean).join("  |  ");
  const exp = r.experience.filter((e) => e.role || e.company);
  const proj = r.projects.filter((p) => p.name);
  const edu = r.education.filter((e) => e.degree || e.school);

  return (
    <Document title={`${r.name || "Resume"} - Resume`} author={r.name}>
      <Page size="A4" style={s.page}>
        <Text style={s.name}>{r.name || "Your Name"}</Text>
        {r.title ? <Text style={s.title}>{r.title}</Text> : null}
        {contact ? <Text style={s.contact}>{contact}</Text> : null}
        {r.links ? <Text style={s.contact}>{r.links.split(",").map((l) => l.trim()).join("  |  ")}</Text> : null}

        {r.summary ? (
          <Section title="Summary" s={s}>
            <Text>{r.summary}</Text>
          </Section>
        ) : null}

        {exp.length ? (
          <Section title="Experience" s={s}>
            {exp.map((e, i) => (
              <View key={i} style={s.item}>
                <View style={s.row}>
                  <Text style={s.bold}>{[e.role, e.company].filter(Boolean).join(", ")}</Text>
                  <Text style={s.muted}>{range(e.start, e.end)}</Text>
                </View>
                {e.location ? <Text style={s.muted}>{e.location}</Text> : null}
                <Bullets text={e.bullets} s={s} />
              </View>
            ))}
          </Section>
        ) : null}

        {proj.length ? (
          <Section title="Projects" s={s}>
            {proj.map((p, i) => (
              <View key={i} style={s.item}>
                <Text>
                  <Text style={s.bold}>{p.name}</Text>
                  {p.tech ? <Text style={s.muted}>{`  |  ${p.tech}`}</Text> : null}
                </Text>
                {p.link ? (
                  <Link src={p.link.startsWith("http") ? p.link : `https://${p.link}`} style={s.link}>
                    {p.link}
                  </Link>
                ) : null}
                <Bullets text={p.bullets} s={s} />
              </View>
            ))}
          </Section>
        ) : null}

        {edu.length ? (
          <Section title="Education" s={s}>
            {edu.map((e, i) => (
              <View key={i} style={s.item}>
                <View style={s.row}>
                  <Text style={s.bold}>{[e.degree, e.school].filter(Boolean).join(", ")}</Text>
                  <Text style={s.muted}>{range(e.start, e.end)}</Text>
                </View>
                {e.details ? <Text>{e.details}</Text> : null}
              </View>
            ))}
          </Section>
        ) : null}

        {r.skills ? (
          <Section title="Skills" s={s}>
            {lines(r.skills).map((l, i) => {
              const [label, ...rest] = l.split(":");
              return rest.length ? (
                <Text key={i}>
                  <Text style={s.bold}>{label}:</Text>
                  {rest.join(":")}
                </Text>
              ) : (
                <Text key={i}>{l}</Text>
              );
            })}
          </Section>
        ) : null}

        {r.certifications ? (
          <Section title="Certifications" s={s}>
            <Bullets text={r.certifications} s={s} />
          </Section>
        ) : null}
      </Page>
    </Document>
  );
}
