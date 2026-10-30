import axios from "axios";
import { ElMessage } from "element-plus";
import { auth, clearLogin } from "@/auth";
import router from "@/router";

function createHttp(baseURL) {
  const http = axios.create({ baseURL, timeout: 30000 });
  http.interceptors.request.use((cfg) => {
    if (auth.token) cfg.headers.Authorization = `Bearer ${auth.token}`;
    return cfg;
  });
  http.interceptors.response.use(
    (res) => {
      if (res.data?.code === 401) {
        // 未登录、登录过期、账号被停用：清掉登录态回登录页，并带上原页面地址
        const loggedIn = !!auth.token;
        clearLogin();
        const cur = router.currentRoute.value;
        if (cur.name !== "login") {
          if (loggedIn) ElMessage.warning(res.data.msg || "登录已失效，请重新登录");
          router.replace({ name: "login", query: { redirect: cur.fullPath } });
        }
        return Promise.reject(res.data);
      }
      if (res.data?.code !== 200) {
        ElMessage.error(res.data?.msg || "请求失败");
        return Promise.reject(res.data);
      }
      return res.data.data ?? res.data;
    },
    (err) => {
      ElMessage.error(err.message || "网络错误");
      return Promise.reject(err);
    }
  );
  return http;
}

const http = createHttp("/api/ebtcm/public");
const memberHttp = createHttp("/api/ebtcm/member");

// ---------- 账号 ----------
export const getCaptcha = () => memberHttp.get("/captcha");
export const login = (data) => memberHttp.post("/login", data);
export const register = (data) => memberHttp.post("/register", data);
export const logout = () => memberHttp.post("/logout");
export const getMemberInfo = () => memberHttp.get("/info");
export const changePassword = (data) => memberHttp.put("/password", data);

// ---------- 检索 ----------

export const search = (params) => http.get("/search", { params });
export const suggest = (q) => http.get("/suggest", { params: { q } });
export const advanced = (data) => http.post("/advanced", data);
export const pico = (params) => http.get("/pico", { params });
export const getGuideline = (id) => http.get(`/guideline/${id}`);
// iframe 带不了 Authorization 头：先换短期凭证，再拼到 PDF 地址上
export const pdfUrl = async (id) => {
  const ticket = await http.get(`/guideline/${id}/pdf-ticket`);
  return `/api/ebtcm/public/guideline/${id}/pdf?ticket=${encodeURIComponent(ticket)}`;
};
export const entity = (type, params) => http.get(`/entity/${type}`, { params });
export const compare = (params) => http.get("/compare", { params });
export const stats = () => http.get("/stats");
