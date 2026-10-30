-- 客户端网站（fronted）用户：与后台 sys_user 完全隔离，前台账号无法登录管理后台
-- status: pending 待审核 / active 正常 / rejected 已驳回 / disabled 已停用
-- source: register 前台自助注册 / admin 后台创建
CREATE TABLE IF NOT EXISTS public.ebtcm_member (
  member_id       bigserial PRIMARY KEY,
  user_name       varchar(50)  NOT NULL UNIQUE,
  password        varchar(100) NOT NULL,
  real_name       varchar(50)  NOT NULL,
  organization    varchar(200),
  department      varchar(100),
  job_title       varchar(50),
  phone           varchar(20),
  email           varchar(100),
  apply_reason    varchar(500),
  status          varchar(10)  NOT NULL DEFAULT 'pending',
  source          varchar(10)  NOT NULL DEFAULT 'register',
  expire_date     date,
  audit_by        varchar(64),
  audit_time      timestamp,
  audit_remark    varchar(500),
  last_login_ip   varchar(128),
  last_login_time timestamp,
  remark          varchar(500),
  create_by       varchar(64),
  create_time     timestamp    NOT NULL DEFAULT now(),
  update_time     timestamp    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ebtcm_member_status ON public.ebtcm_member (status, create_time DESC);
