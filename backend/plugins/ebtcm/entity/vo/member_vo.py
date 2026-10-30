"""
客户端用户（ebtcm_member）请求模型
"""
import re
from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from plugins.ebtcm.entity.vo.ebtcm_vo import _Camel

MemberStatus = Literal['pending', 'active', 'rejected', 'disabled']


def _check_password(v: str) -> str:
    if not (8 <= len(v) <= 32) or not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
        raise ValueError('密码需为 8-32 位，且同时包含字母和数字')
    return v


def _check_user_name(v: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_@.\-]{4,50}', v):
        raise ValueError('用户名为 4-50 位字母、数字或 _ @ . -')
    return v


class _MemberProfile(_Camel):
    real_name: str = Field(min_length=1, max_length=50)
    organization: str | None = Field(None, max_length=200)
    department: str | None = Field(None, max_length=100)
    job_title: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=100)


class MemberLoginModel(_Camel):
    user_name: str
    password: str
    code: str
    uuid: str


class MemberRegisterModel(_MemberProfile):
    user_name: str
    password: str
    apply_reason: str | None = Field(None, max_length=500)
    code: str
    uuid: str

    v_name = field_validator('user_name')(_check_user_name)
    v_pwd = field_validator('password')(_check_password)


class MemberPasswordModel(_Camel):
    old_password: str
    new_password: str

    v_pwd = field_validator('new_password')(_check_password)


# ---------- 后台管理 ----------
class MemberPageQueryModel(_Camel):
    keyword: str | None = None
    status: MemberStatus | None = None
    source: str | None = None
    page_num: int = 1
    page_size: int = 10


class MemberSaveModel(_MemberProfile):
    member_id: int | None = None
    user_name: str | None = None
    password: str | None = None
    status: MemberStatus | None = None
    expire_date: date | None = None
    remark: str | None = Field(None, max_length=500)

    @field_validator('user_name')
    @classmethod
    def v_name(cls, v):
        return _check_user_name(v) if v else v

    @field_validator('password')
    @classmethod
    def v_pwd(cls, v):
        return _check_password(v) if v else v


class MemberAuditModel(_Camel):
    member_ids: list[int] = Field(min_length=1)
    approved: bool
    audit_remark: str | None = Field(None, max_length=500)
    expire_date: date | None = None


class MemberStatusModel(_Camel):
    member_ids: list[int] = Field(min_length=1)
    status: Literal['active', 'disabled']


class MemberResetPwdModel(_Camel):
    member_id: int
    password: str

    v_pwd = field_validator('password')(_check_password)
