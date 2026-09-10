"""
EB_TCM 服务层：调用 DAO，统一把 snake_case 行转成 camelCase 输出
"""
import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from plugins.ebtcm.dao.ebtcm_dao import CERTAINTY_LABEL, STRENGTH_LABEL, TYPE_LABEL, EbtcmDao


def _camel(key: str) -> str:
    return re.sub(r'_([a-z0-9])', lambda m: m.group(1).upper(), key)


def camel(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {_camel(k): camel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [camel(x) for x in obj]
    return obj


def page(rows: list, total: int, page_num: int, page_size: int) -> dict:
    return {'rows': camel(rows), 'total': total, 'pageNum': page_num, 'pageSize': page_size, 'hasNext': page_num * page_size < total}


class EbtcmService:
    labels = {'strength': STRENGTH_LABEL, 'certainty': CERTAINTY_LABEL, 'guidelineType': TYPE_LABEL}

    # ---- 指南 ----
    @classmethod
    async def guideline_page(cls, db: AsyncSession, q) -> dict:
        rows, total = await EbtcmDao.guideline_page(db, q)
        return page(rows, total, q.page_num, q.page_size)

    @classmethod
    async def guideline_get(cls, db: AsyncSession, gid: UUID) -> dict | None:
        return camel(await EbtcmDao.guideline_get(db, gid))

    @classmethod
    async def guideline_update(cls, db: AsyncSession, model) -> None:
        await EbtcmDao.guideline_update(db, model.model_dump(exclude_unset=True))
        await db.commit()

    @classmethod
    async def guideline_bundle(cls, db: AsyncSession, gid: UUID) -> dict | None:
        return camel(await EbtcmDao.guideline_bundle(db, gid))

    # ---- 推荐意见 ----
    @classmethod
    async def recommendation_page(cls, db: AsyncSession, q) -> dict:
        rows, total = await EbtcmDao.recommendation_page(db, q)
        return page(rows, total, q.page_num, q.page_size)

    @classmethod
    async def recommendation_get(cls, db: AsyncSession, rid: UUID) -> dict | None:
        return camel(await EbtcmDao.recommendation_get(db, rid))

    @classmethod
    async def recommendation_update(cls, db: AsyncSession, model) -> None:
        await EbtcmDao.recommendation_update(db, model.model_dump(exclude_unset=True))
        await db.commit()

    @classmethod
    async def recommendation_verify(cls, db: AsyncSession, ids: list[UUID], verified: bool) -> int:
        n = await EbtcmDao.recommendation_verify(db, ids, verified)
        await db.commit()
        return n

    # ---- 段落 ----
    @classmethod
    async def passage_page(cls, db: AsyncSession, q) -> dict:
        rows, total = await EbtcmDao.passage_page(db, q)
        return page(rows, total, q.page_num, q.page_size)

    @classmethod
    async def passage_update(cls, db: AsyncSession, model) -> None:
        await EbtcmDao.passage_update(db, model.model_dump(exclude_unset=True))
        await db.commit()

    # ---- 术语 ----
    @classmethod
    async def concept_page(cls, db: AsyncSession, q) -> dict:
        rows, total = await EbtcmDao.concept_page(db, q)
        return page(rows, total, q.page_num, q.page_size)

    @classmethod
    async def concept_save(cls, db: AsyncSession, model) -> UUID:
        cid = await EbtcmDao.concept_save(db, model.model_dump())
        await db.commit()
        return cid

    @classmethod
    async def concept_delete(cls, db: AsyncSession, ids: list[UUID]) -> int:
        n = await EbtcmDao.concept_delete(db, ids)
        await db.commit()
        return n

    @classmethod
    async def concept_merge(cls, db: AsyncSession, model) -> dict:
        r = await EbtcmDao.concept_merge(db, model.concept_type, model.name, model.aliases)
        await db.commit()
        return r

    @classmethod
    async def context_terms(cls, db: AsyncSession, context_type: str, keyword: str | None, limit: int) -> list[dict]:
        return camel(await EbtcmDao.context_terms(db, context_type, keyword, limit))

    # ---- 统计 / 公开 ----
    @classmethod
    async def stats_overview(cls, db: AsyncSession) -> dict:
        return camel(await EbtcmDao.stats_overview(db))

    @classmethod
    async def search(cls, db: AsyncSession, q) -> dict:
        return camel(await EbtcmDao.search(db, q))

    @classmethod
    async def suggest(cls, db: AsyncSession, q: str) -> list[dict]:
        return camel(await EbtcmDao.suggest(db, q))

    @classmethod
    async def entity_page(cls, db: AsyncSession, context_type: str, term: str, strength: str | None, page_num: int, page_size: int) -> dict:
        return camel(await EbtcmDao.entity_page(db, context_type, term, strength, page_num, page_size))

    @classmethod
    async def pico(cls, db: AsyncSession, q) -> dict:
        return camel(await EbtcmDao.pico(db, q))

    @classmethod
    async def advanced(cls, db: AsyncSession, q) -> dict:
        return camel(await EbtcmDao.advanced(db, q))

    @classmethod
    async def compare(cls, db: AsyncSession, disease: str | None, drug: str | None) -> list[dict]:
        return camel(await EbtcmDao.compare(db, disease, drug))
