"""
客户端用户接口：验证码、注册、登录、个人信息（客户端网站使用）
以及后台“前台用户”管理与审核接口（需后台登录 + 权限）
"""
from typing import Annotated

from fastapi import Body, Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.rate_limit_annotation import ApiRateLimit, ApiRateLimitPreset
from common.aspect.db_session import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from plugins.ebtcm.entity.vo.member_vo import (
    MemberAuditModel,
    MemberLoginModel,
    MemberPageQueryModel,
    MemberPasswordModel,
    MemberRegisterModel,
    MemberResetPwdModel,
    MemberSaveModel,
    MemberStatusModel,
)
from plugins.ebtcm.service.member_service import MemberAuthDependency, MemberService, _public
from utils.response_util import ResponseUtil

DB = Annotated[AsyncSession, DBSessionDependency()]
Member = Annotated[dict, MemberAuthDependency()]
Admin = Annotated[CurrentUserModel, CurrentUserDependency()]

# ================= 客户端 =================
ebtcm_member_controller = APIRouterPro(prefix='/ebtcm/member', order_num=32, tags=['指南知识库-客户端用户'])


@ebtcm_member_controller.get('/captcha', summary='登录/注册验证码')
@ApiRateLimit(namespace='ebtcm:member:captcha', preset=ApiRateLimitPreset.ANON_AUTH_CAPTCHA)
async def captcha(request: Request) -> Response:
    return ResponseUtil.success(data=await MemberService.captcha(request))


@ebtcm_member_controller.post('/register', summary='注册申请（需后台审核）')
@ApiRateLimit(namespace='ebtcm:member:register', preset=ApiRateLimitPreset.ANON_AUTH_REGISTER)
async def register(request: Request, body: Annotated[MemberRegisterModel, Body()], query_db: DB) -> Response:
    await MemberService.register(request, query_db, body)
    return ResponseUtil.success(msg='注册申请已提交，管理员审核通过后即可登录')


@ebtcm_member_controller.post('/login', summary='登录')
@ApiRateLimit(namespace='ebtcm:member:login', preset=ApiRateLimitPreset.ANON_AUTH_LOGIN)
async def login(request: Request, body: Annotated[MemberLoginModel, Body()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await MemberService.login(request, query_db, body))


@ebtcm_member_controller.post('/logout', summary='退出登录')
async def logout(request: Request) -> Response:
    await MemberService.logout(request)
    return ResponseUtil.success(msg='已退出')


@ebtcm_member_controller.get('/info', summary='当前用户信息')
async def info(request: Request, member: Member) -> Response:
    return ResponseUtil.success(data=_public(member))


@ebtcm_member_controller.put('/password', summary='修改密码')
async def change_password(request: Request, body: Annotated[MemberPasswordModel, Body()], member: Member, query_db: DB) -> Response:
    await MemberService.change_password(query_db, member, body)
    return ResponseUtil.success(msg='密码已修改')


# ================= 后台管理 =================
ebtcm_member_admin_controller = APIRouterPro(prefix='/ebtcm/admin/member', order_num=33, tags=['指南知识库-前台用户管理'], dependencies=[PreAuthDependency()])


@ebtcm_member_admin_controller.get('/list', summary='前台用户分页列表', dependencies=[UserInterfaceAuthDependency('ebtcm:member:list')])
async def member_list(request: Request, q: Annotated[MemberPageQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(dict_content=await MemberService.admin_page(query_db, q))


@ebtcm_member_admin_controller.get('/counts', summary='各状态用户数（待审核角标）', dependencies=[UserInterfaceAuthDependency('ebtcm:member:list')])
async def member_counts(request: Request, query_db: DB) -> Response:
    return ResponseUtil.success(data=await MemberService.admin_counts(query_db))


@ebtcm_member_admin_controller.get('/{member_id}', summary='前台用户详情', dependencies=[UserInterfaceAuthDependency('ebtcm:member:list')])
async def member_get(request: Request, member_id: Annotated[int, Path()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await MemberService.admin_get(query_db, member_id))


@ebtcm_member_admin_controller.post('', summary='新增/修改前台用户', dependencies=[UserInterfaceAuthDependency('ebtcm:member:edit')])
async def member_save(request: Request, body: Annotated[MemberSaveModel, Body()], query_db: DB, admin: Admin) -> Response:
    mid = await MemberService.admin_save(query_db, body, admin.user.user_name)
    return ResponseUtil.success(data=mid, msg='保存成功')


@ebtcm_member_admin_controller.put('/audit', summary='审核注册申请（通过/驳回）', dependencies=[UserInterfaceAuthDependency('ebtcm:member:audit')])
async def member_audit(request: Request, body: Annotated[MemberAuditModel, Body()], query_db: DB, admin: Admin) -> Response:
    n = await MemberService.admin_audit(query_db, body, admin.user.user_name)
    return ResponseUtil.success(data=n, msg=f'已{"通过" if body.approved else "驳回"} {n} 个申请')


@ebtcm_member_admin_controller.put('/status', summary='启用/停用', dependencies=[UserInterfaceAuthDependency('ebtcm:member:edit')])
async def member_status(request: Request, body: Annotated[MemberStatusModel, Body()], query_db: DB) -> Response:
    n = await MemberService.admin_set_status(query_db, body)
    return ResponseUtil.success(data=n, msg=f'已{"启用" if body.status == "active" else "停用"} {n} 个账号')


@ebtcm_member_admin_controller.put('/resetPwd', summary='重置密码', dependencies=[UserInterfaceAuthDependency('ebtcm:member:edit')])
async def member_reset_pwd(request: Request, body: Annotated[MemberResetPwdModel, Body()], query_db: DB) -> Response:
    await MemberService.admin_reset_password(query_db, body)
    return ResponseUtil.success(msg='密码已重置')


@ebtcm_member_admin_controller.delete('/{ids}', summary='删除前台用户', dependencies=[UserInterfaceAuthDependency('ebtcm:member:remove')])
async def member_delete(request: Request, ids: Annotated[str, Path()], query_db: DB) -> Response:
    n = await MemberService.admin_delete(query_db, [int(x) for x in ids.split(',') if x.strip()])
    return ResponseUtil.success(msg=f'已删除 {n} 个账号')
