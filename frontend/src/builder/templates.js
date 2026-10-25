// Template metadata lives apart from ResumePDF so the UI can list templates
// without loading @react-pdf/renderer.

// ATS-friendly rules every template follows:
// single column, real selectable text, standard section headings,
// standard fonts, no tables, icons or images.

export const TEMPLATES = {
  classic: {
    label: "Classic",
    font: "Times-Roman",
    bold: "Times-Bold",
    accent: "#111111",
    headingCase: "uppercase",
    align: "center",
  },
  modern: {
    label: "Modern",
    font: "Helvetica",
    bold: "Helvetica-Bold",
    accent: "#3730a3",
    headingCase: "uppercase",
    align: "left",
  },
  compact: {
    label: "Compact",
    font: "Helvetica",
    bold: "Helvetica-Bold",
    accent: "#0f766e",
    headingCase: "none",
    align: "left",
    small: true,
  },
};
