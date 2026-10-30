"""
客户端用户：注册/登录/鉴权/后台审核

与后台 sys_user 体系隔离：
- 账号存 public.ebtcm_member，后台 /login 查不到这些账号；
- token 用 JWT 密钥派生出的独立密钥签名，后台 PreAuth 无法解析，反之亦然。
"""
import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_session import DBSessionDependency
from config.env import JwtConfig
from exceptions.exception import AuthException, ServiceException
from module_admin.service.captcha_service import CaptchaService
from plugins.ebtcm.dao.member_dao import MemberDao
from plugins.ebtcm.service.ebtcm_service import camel, page
from utils.client_ip_util import ClientIPUtil
from utils.pwd_util import PwdUtil

TOKEN_TTL = timedelta(days=7)
PDF_TICKET_TTL = timedelta(hours=2)
CAPTCHA_TTL = timedelta(minutes=2)
MAX_PWD_ERRORS, LOCK_TTL = 5, timedelta(minutes=10)

_KEY_TOKEN = 'ebtcm:member_token'
_KEY_CAPTCHA = 'ebtcm:member_captcha'
_KEY_PWD_ERR = 'ebtcm:member_pwd_err'

STATUS_LABEL = {'pending': '待审核', 'active': '正常', 'rejected': '已驳回', 'disabled': '已停用'}


def _secret() -> str:
    return hashlib.sha256(f'{JwtConfig.jwt_secret_key}:ebtcm-member'.encode()).hexdigest()


def _encode(payload: dict, ttl: timedelta) -> str:
    return jwt.encode({**payload, 'exp': datetime.now(timezone.utc) + ttl}, _secret(), algorithm='HS256')


def _decode(token: str, typ: str) -> dict:
    try:
        payload = jwt.decode(token, _secret(), algorithms=['HS256'])
    except PyJWTError as exc:
        raise AuthException(data='', message='登录已失效，请重新登录') from exc
    if payload.get('typ') != typ:
        raise AuthException(data='', message='登录已失效，请重新登录')
    return payload


def _check_usable(m: dict) -> None:
    """账号能否使用：登录和每次请求都校验，后台停用/到期立即生效"""
    st = m['status']
    if st == 'pending':
        raise ServiceException(message='账号正在审核中，审核通过后即可登录')
    if st == 'rejected':
        raise ServiceException(message='注册申请未通过' + (f'：{m["audit_remark"]}' if m.get('audit_remark') else ''))
    if st == 'disabled':
        raise ServiceException(message='账号已停用，请联系管理员')
    if m.get('expire_date') and m['expire_date'] < date.today():
        raise ServiceException(message='账号已过期，请联系管理员续期')


def _public(m: dict) -> dict:
    keys = ('member_id', 'user_name', 'real_name', 'organization', 'department', 'job_title', 'phone', 'email', 'expire_date')
    return camel({k: m.get(k) for k in keys})


class MemberService:
    # ---------------- 验证码 ----------------
    @classmethod
    async def captcha(cls, request: Request) -> dict:
        image, result = await CaptchaService.create_captcha_image_service()
        sid = str(uuid.uuid4())
        await request.app.state.redis.set(f'{_KEY_CAPTCHA}:{sid}', str(result), ex=CAPTCHA_TTL)
        return {'img': image, 'uuid': sid}

    @classmethod
    async def _check_captcha(cls, request: Request, sid: str, code: str) -> None:
        key = f'{_KEY_CAPTCHA}:{sid}'
        expected = await request.app.state.redis.get(key)
        await request.app.state.redis.delete(key)
        if not expected:
            raise ServiceException(message='验证码已失效，请刷新')
        if str(code).strip() != str(expected):
            raise ServiceException(message='验证码错误')

    # ---------------- 注册 / 登录 ----------------
    @classmethod
    async def register(cls, request: Request, db: AsyncSession, body) -> None:
        await cls._check_captcha(request, body.uuid, body.code)
        if await MemberDao.get_by_name(db, body.user_name):
            raise ServiceException(message='用户名已被使用')
        data = body.model_dump(exclude={'code', 'uuid'})
        data.update(password=PwdUtil.get_password_hash(body.password), status='pending', source='register')
        await MemberDao.insert(db, data)
        await db.commit()

    @classmethod
    async def login(cls, request: Request, db: AsyncSession, body) -> dict:
        redis = request.app.state.redis
        err_key = f'{_KEY_PWD_ERR}:{body.user_name.lower()}'
        if int(await redis.get(err_key) or 0) >= MAX_PWD_ERRORS:
            raise ServiceException(message=f'密码错误次数过多，请 {int(LOCK_TTL.total_seconds() // 60)} 分钟后再试')
        await cls._check_captcha(request, body.uuid, body.code)

        m = await MemberDao.get_by_name(db, body.user_name)
        if not m or not PwdUtil.verify_password(body.password, m['password']):
            n = await redis.incr(err_key)
            if n == 1:
                await redis.expire(err_key, LOCK_TTL)
            raise ServiceException(message='用户名或密码错误')
        await redis.delete(err_key)
        _check_usable(m)

        sid = uuid.uuid4().hex
        token = _encode({'typ': 'ebtcm_member', 'mid': m['member_id'], 'sid': sid}, TOKEN_TTL)
        await redis.set(f'{_KEY_TOKEN}:{sid}', m['member_id'], ex=TOKEN_TTL)
        await MemberDao.touch_login(db, m['member_id'], ClientIPUtil.get_client_ip(request))
        await db.commit()
        return {'token': token, 'member': _public(m)}

    @classmethod
    async def logout(cls, request: Request) -> None:
        token = _bearer(request)
        if token:
            try:
                sid = _decode(token, 'ebtcm_member')['sid']
                await request.app.state.redis.delete(f'{_KEY_TOKEN}:{sid}')
            except AuthException:
                pass

    @classmethod
    async def current(cls, request: Request, db: AsyncSession) -> dict:
        token = _bearer(request)
        if not token:
            raise AuthException(data='', message='请先登录')
        p = _decode(token, 'ebtcm_member')
        if await request.app.state.redis.get(f'{_KEY_TOKEN}:{p["sid"]}') is None:
            raise AuthException(data='', message='登录已失效，请重新登录')
        m = await MemberDao.get_by_id(db, p['mid'])
        if not m:
            raise AuthException(data='', message='账号不存在')
        try:
            _check_usable(m)
        except ServiceException as exc:
            raise AuthException(data='', message=exc.message) from exc
        return m

    @classmethod
    async def change_password(cls, db: AsyncSession, member: dict, body) -> None:
        m = await MemberDao.get_by_id(db, member['member_id'], with_password=True)
        if not PwdUtil.verify_password(body.old_password, m['password']):
            raise ServiceException(message='原密码错误')
        await MemberDao.set_password(db, m['member_id'], PwdUtil.get_password_hash(body.new_password))
        await db.commit()

    # ---------------- PDF 临时凭证 ----------------
    # iframe/新标签页打开 PDF 无法带 Authorization 头，改为登录后换取短期凭证拼在 URL 上
    @classmethod
    def pdf_ticket(cls, member: dict, gid: str) -> str:
        return _encode({'typ': 'ebtcm_pdf', 'mid': member['member_id'], 'gid': gid}, PDF_TICKET_TTL)

    @classmethod
    def check_pdf_ticket(cls, ticket: str, gid: str) -> None:
        if _decode(ticket, 'ebtcm_pdf').get('gid') != gid:
            raise AuthException(data='', message='原文访问凭证无效')

    # ---------------- 后台管理 ----------------
    @classmethod
    async def admin_page(cls, db: AsyncSession, q) -> dict:
        rows, total = await MemberDao.page(db, q)
        return page(rows, total, q.page_num, q.page_size)

    @classmethod
    async def admin_counts(cls, db: AsyncSession) -> dict:
        return await MemberDao.status_counts(db)

    @classmethod
    async def admin_get(cls, db: AsyncSession, member_id: int) -> dict | None:
        return camel(await MemberDao.get_by_id(db, member_id))

    @classmethod
    async def admin_save(cls, db: AsyncSession, body, operator: str) -> int:
        data = body.model_dump(exclude={'member_id', 'user_name', 'password'}, exclude_unset=True)
        if body.member_id:
            if data.get('status') in ('pending', 'rejected'):
                data.pop('status')
            await MemberDao.update_profile(db, body.member_id, data)
            await db.commit()
            return body.member_id
        if not body.user_name or not body.password:
            raise ServiceException(message='新建账号需填写用户名和初始密码')
        if await MemberDao.get_by_name(db, body.user_name):
            raise ServiceException(message='用户名已被使用')
        data.update(user_name=body.user_name, password=PwdUtil.get_password_hash(body.password),
                    status=body.status if body.status in ('active', 'disabled') else 'active', source='admin', create_by=operator)
        mid = await MemberDao.insert(db, data)
        await db.commit()
        return mid

    @classmethod
    async def admin_audit(cls, db: AsyncSession, body, operator: str) -> int:
        if not body.approved and not (body.audit_remark or '').strip():
            raise ServiceException(message='驳回时请填写原因，用户登录时会看到')
        n = await MemberDao.audit(db, body.member_ids, 'active' if body.approved else 'rejected', operator, body.audit_remark, body.expire_date)
        await db.commit()
        return n

    @classmethod
    async def admin_set_status(cls, db: AsyncSession, body) -> int:
        n = await MemberDao.set_status(db, body.member_ids, body.status)
        await db.commit()
        return n

    @classmethod
    async def admin_reset_password(cls, db: AsyncSession, body) -> None:
        await MemberDao.set_password(db, body.member_id, PwdUtil.get_password_hash(body.password))
        await db.commit()

    @classmethod
    async def admin_delete(cls, db: AsyncSession, ids: list[int]) -> int:
        n = await MemberDao.delete(db, ids)
        await db.commit()
        return n


def _bearer(request: Request) -> str | None:
    auth = request.headers.get('Authorization') or ''
    return auth[7:].strip() if auth.lower().startswith('bearer ') else (auth.strip() or None)


async def _current_member(request: Request, db: Annotated[AsyncSession, DBSessionDependency()]) -> dict[str, Any]:
    return await MemberService.current(request, db)


def MemberAuthDependency():  # noqa: N802
    """客户端接口登录校验依赖，返回当前用户 dict"""
    return Depends(_current_member)
