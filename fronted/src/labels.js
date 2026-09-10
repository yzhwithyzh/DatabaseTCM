export const STRENGTH = { strong: "强推荐", weak: "弱推荐", ungraded: "未分级", not_reported: "未报告" };
export const STRENGTH_TAG = { strong: "success", weak: "warning", ungraded: "info", not_reported: "info" };
export const CERTAINTY = { high: "高", moderate: "中", low: "低", very_low: "极低", not_reported: "未报告" };
export const DIRECTION = { for: "推荐", against: "不推荐", none: "未表态" };
export const GTYPE = { guideline: "指南", consensus: "专家共识", standard: "团体标准", other: "其他" };
export const STATUS = { current: "现行", superseded: "已被替代", withdrawn: "撤回" };
export const CTX = { disease: "疾病", syndrome: "证候", drug: "中成药", population: "人群", outcome: "结局" };
export const CTX_TAG = { disease: "danger", syndrome: "warning", drug: "success", population: "info", outcome: "" };
export const PTYPE = { diagnosis: "诊断", syndrome: "辨证", treatment: "治疗", precaution: "注意事项", background: "背景", other: "其他" };

export function highlight(text, q) {
  if (!text) return "";
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  if (!q) return esc(text);
  const parts = text.split(q);
  return parts.map(esc).join(`<mark>${esc(q)}</mark>`);
}
export const STRENGTH_COLOR = { strong: "#2f8f5b", weak: "#e0a83f", ungraded: "#7b8cae", not_reported: "#c9d1dc" };
