import request from "@/utils/request";

// ---------- 概览 ----------
export function getStatsOverview() {
  return request({ url: "/ebtcm/stats/overview", method: "get" });
}

// ---------- 指南 ----------
export function listGuideline(query) {
  return request({ url: "/ebtcm/guideline/list", method: "get", params: query });
}
export function getGuideline(id) {
  return request({ url: "/ebtcm/guideline/" + id, method: "get" });
}
export function getGuidelineBundle(id) {
  return request({ url: "/ebtcm/guideline/" + id + "/bundle", method: "get" });
}
export function updateGuideline(data) {
  return request({ url: "/ebtcm/guideline", method: "put", data });
}

// ---------- 推荐意见 ----------
export function listRecommendation(query) {
  return request({ url: "/ebtcm/recommendation/list", method: "get", params: query });
}
export function getRecommendation(id) {
  return request({ url: "/ebtcm/recommendation/" + id, method: "get" });
}
export function updateRecommendation(data) {
  return request({ url: "/ebtcm/recommendation", method: "put", data });
}
export function verifyRecommendation(ids, verified = true) {
  return request({ url: "/ebtcm/recommendation/verify", method: "put", data: { ids, verified } });
}

// ---------- 段落 ----------
export function listPassage(query) {
  return request({ url: "/ebtcm/passage/list", method: "get", params: query });
}
export function updatePassage(data) {
  return request({ url: "/ebtcm/passage", method: "put", data });
}

// ---------- 术语 ----------
export function listConcept(query) {
  return request({ url: "/ebtcm/concept/list", method: "get", params: query });
}
export function listContextTerms(query) {
  return request({ url: "/ebtcm/concept/terms", method: "get", params: query });
}
export function saveConcept(data) {
  return request({ url: "/ebtcm/concept", method: "post", data });
}
export function mergeConcept(data) {
  return request({ url: "/ebtcm/concept/merge", method: "post", data });
}
export function delConcept(ids) {
  return request({ url: "/ebtcm/concept/" + ids, method: "delete" });
}

export const STRENGTH = { strong: "强推荐", weak: "弱推荐", ungraded: "未分级", not_reported: "未报告" };
export const CERTAINTY = { high: "高", moderate: "中", low: "低", very_low: "极低", not_reported: "未报告" };
export const DIRECTION = { for: "推荐", against: "不推荐", none: "未表态" };
export const GTYPE = { guideline: "指南", consensus: "专家共识", standard: "团体标准", other: "其他" };
export const STRENGTH_TAG = { strong: "success", weak: "warning", ungraded: "info", not_reported: "" };
