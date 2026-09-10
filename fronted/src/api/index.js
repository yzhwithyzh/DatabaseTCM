import axios from "axios";
import { ElMessage } from "element-plus";

const http = axios.create({ baseURL: "/api/ebtcm/public", timeout: 30000 });
http.interceptors.response.use(
  (res) => {
    if (res.data?.code !== 200) {
      ElMessage.error(res.data?.msg || "请求失败");
      return Promise.reject(res.data);
    }
    return res.data.data;
  },
  (err) => {
    ElMessage.error(err.message || "网络错误");
    return Promise.reject(err);
  }
);

export const search = (params) => http.get("/search", { params });
export const suggest = (q) => http.get("/suggest", { params: { q } });
export const advanced = (data) => http.post("/advanced", data);
export const pico = (params) => http.get("/pico", { params });
export const getGuideline = (id) => http.get(`/guideline/${id}`);
export const pdfUrl = (id) => `/api/ebtcm/public/guideline/${id}/pdf`;
export const entity = (type, params) => http.get(`/entity/${type}`, { params });
export const compare = (params) => http.get("/compare", { params });
export const stats = () => http.get("/stats");
