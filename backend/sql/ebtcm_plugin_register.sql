-- 补写 ebtcm 插件在平台表中的注册记录（sys_plugin / sys_plugin_menu / sys_plugin_migration）
-- 用于 kb 数据已导入但 sys_plugin 表导入失败（主键冲突）的情况；可重复执行
BEGIN;
INSERT INTO public.sys_plugin (plugin_id, plugin_name, version, installed_version, enabled, status, source, backend_path, frontend_path, last_error, description, create_by, create_time, update_by, update_time, remark) VALUES ('ebtcm', '中成药循证指南库', '0.1.0', '0.1.0', '0', 'installed', 'local', 'ebtcm', 'ebtcm', NULL, '中成药临床指南推荐知识库（EB_TCM）：指南、推荐意见、段落、术语、参考文献的管理与检索接口。', '', '2026-09-09 22:33:39', '', '2026-09-09 22:33:40', NULL) ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2000', 'route:ebtcm/ebtcm#Layout', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2001', 'perm:ebtcm:stats:list', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2002', 'perm:ebtcm:guideline:list', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2003', 'perm:ebtcm:recommendation:list', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2004', 'perm:ebtcm:concept:list', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2005', 'button:perm:ebtcm:guideline:list/指南详情#ebtcm:guideline:query', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2006', 'button:perm:ebtcm:guideline:list/修改指南#ebtcm:guideline:edit', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2007', 'button:perm:ebtcm:recommendation:list/修改推荐意见#ebtcm:recommendation:edit', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2008', 'button:perm:ebtcm:recommendation:list/核验推荐意见#ebtcm:recommendation:verify', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2009', 'button:perm:ebtcm:concept:list/段落列表#ebtcm:passage:list', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2010', 'button:perm:ebtcm:concept:list/修改段落#ebtcm:passage:edit', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2011', 'button:perm:ebtcm:concept:list/新增术语#ebtcm:concept:add', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2012', 'button:perm:ebtcm:concept:list/修改术语#ebtcm:concept:edit', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_menu (plugin_id, menu_id, menu_key, create_time) VALUES ('ebtcm', '2013', 'button:perm:ebtcm:concept:list/删除术语#ebtcm:concept:remove', '2026-09-09 22:33:39') ON CONFLICT DO NOTHING;
INSERT INTO public.sys_plugin_migration (plugin_id, migration_path, migration_checksum, version, statement_count, status, error_message, attempt_count, started_time, finished_time, create_time, update_time) VALUES ('ebtcm', 'migrations/postgresql/001_init.sql', 'b62c19c0c1c11f58517d7819f31110eb6be40510d5f0e864a717b3ff73b18145', '0.1.0', '12', 'success', NULL, '1', '2026-09-09 22:33:39', '2026-09-09 22:33:40', '2026-09-09 22:33:40', '2026-09-09 22:33:40') ON CONFLICT DO NOTHING;
COMMIT;
