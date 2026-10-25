import { pdf } from "@react-pdf/renderer";
import { ResumePDF } from "./ResumePDF";

export function renderPdf(resume, template) {
  return pdf(<ResumePDF resume={resume} template={template} />).toBlob();
}
