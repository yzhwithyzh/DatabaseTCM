// 客户端登录态：token 存 localStorage，用户信息存内存（刷新后由路由守卫重新拉取）
const KEY = "ebtcm_token";

export const auth = reactive({ token: localStorage.getItem(KEY) || "", member: null });

export function setLogin(token, member) {
  auth.token = token; auth.member = member;
  localStorage.setItem(KEY, token);
}

export function clearLogin() {
  auth.token = ""; auth.member = null;
  localStorage.removeItem(KEY);
}
