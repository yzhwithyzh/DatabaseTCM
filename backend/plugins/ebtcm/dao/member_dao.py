"""
客户端用户（public.ebtcm_member）数据访问
"""
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 列表/详情对外字段（不含 password）
_COLS = '''member_id, user_name, real_name, organization, department, job_title, phone, email, apply_reason,
           status, source, expire_date, audit_by, audit_time, audit_remark, last_login_ip, last_login_time,
           remark, create_by, create_time, update_time'''
_PROFILE = ('real_name', 'organization', 'department', 'job_title', 'phone', 'email')


def _one(result) -> dict[str, Any] | None:
    r = result.first()
    return dict(r._mapping) if r else None


class MemberDao:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, member_id: int, with_password: bool = False) -> dict | None:
        cols = _COLS + (', password' if with_password else '')
        return _one(await db.execute(text(f'SELECT {cols} FROM public.ebtcm_member WHERE member_id = :id'), {'id': member_id}))

    @classmethod
    async def get_by_name(cls, db: AsyncSession, user_name: str) -> dict | None:
        return _one(await db.execute(text(f'SELECT {_COLS}, password FROM public.ebtcm_member WHERE lower(user_name) = lower(:n)'), {'n': user_name}))

    @classmethod
    async def page(cls, db: AsyncSession, q) -> tuple[list[dict], int]:
        where, p = ['TRUE'], {}
        if q.keyword:
            where.append('(user_name ILIKE :kw OR real_name ILIKE :kw OR organization ILIKE :kw OR phone ILIKE :kw OR email ILIKE :kw)')
            p['kw'] = f'%{q.keyword}%'
        if q.status: where.append('status = :st'); p['st'] = q.status
        if q.source: where.append('source = :src'); p['src'] = q.source
        w = ' AND '.join(where)
        total = (await db.execute(text(f'SELECT count(*) FROM public.ebtcm_member WHERE {w}'), p)).scalar()
        p.update(lim=q.page_size, off=(q.page_num - 1) * q.page_size)
        rows = await db.execute(text(f'''SELECT {_COLS} FROM public.ebtcm_member WHERE {w}
            ORDER BY (status = 'pending') DESC, create_time DESC LIMIT :lim OFFSET :off'''), p)
        return [dict(r._mapping) for r in rows], total

    @classmethod
    async def status_counts(cls, db: AsyncSession) -> dict[str, int]:
        rows = await db.execute(text('SELECT status, count(*) AS n FROM public.ebtcm_member GROUP BY status'))
        return {r.status: r.n for r in rows}

    @classmethod
    async def insert(cls, db: AsyncSession, data: dict) -> int:
        cols = ('user_name', 'password', *_PROFILE, 'apply_reason', 'status', 'source', 'expire_date', 'remark', 'create_by')
        r = await db.execute(text(f'''INSERT INTO public.ebtcm_member({", ".join(cols)})
            VALUES({", ".join(":" + c for c in cols)}) RETURNING member_id'''), {c: data.get(c) for c in cols})
        return r.scalar()

    @classmethod
    async def update_profile(cls, db: AsyncSession, member_id: int, data: dict) -> None:
        cols = [c for c in (*_PROFILE, 'status', 'expire_date', 'remark') if c in data]
        sets = ', '.join(f'{c} = :{c}' for c in cols)
        await db.execute(text(f'UPDATE public.ebtcm_member SET {sets}, update_time = now() WHERE member_id = :id'),
                         {**{c: data[c] for c in cols}, 'id': member_id})

    @classmethod
    async def audit(cls, db: AsyncSession, ids: list[int], status: str, by: str, remark: str | None, expire_date) -> int:
        r = await db.execute(text('''UPDATE public.ebtcm_member
            SET status = :st, audit_by = :by, audit_time = now(), audit_remark = :rm,
                expire_date = COALESCE(CAST(:exp AS date), expire_date), update_time = now()
            WHERE member_id = ANY(:ids) AND status = 'pending' '''),
            {'st': status, 'by': by, 'rm': remark, 'exp': expire_date, 'ids': ids})
        return r.rowcount

    @classmethod
    async def set_status(cls, db: AsyncSession, ids: list[int], status: str) -> int:
        # 只在“正常/停用”之间切换，待审核与已驳回走审核流程
        r = await db.execute(text('''UPDATE public.ebtcm_member SET status = :st, update_time = now()
            WHERE member_id = ANY(:ids) AND status IN ('active', 'disabled')'''), {'st': status, 'ids': ids})
        return r.rowcount

    @classmethod
    async def set_password(cls, db: AsyncSession, member_id: int, hashed: str) -> None:
        await db.execute(text('UPDATE public.ebtcm_member SET password = :pw, update_time = now() WHERE member_id = :id'),
                         {'pw': hashed, 'id': member_id})

    @classmethod
    async def touch_login(cls, db: AsyncSession, member_id: int, ip: str) -> None:
        await db.execute(text('UPDATE public.ebtcm_member SET last_login_ip = :ip, last_login_time = now() WHERE member_id = :id'),
                         {'ip': ip, 'id': member_id})

    @classmethod
    async def delete(cls, db: AsyncSession, ids: list[int]) -> int:
        r = await db.execute(text('DELETE FROM public.ebtcm_member WHERE member_id = ANY(:ids)'), {'ids': ids})
        return r.rowcount
