"""
EB_TCM 数据访问层：检索、聚合、CRUD
说明：检索用 ILIKE + pg_trgm 索引（中文子串匹配），高亮片段在 Python 侧生成
"""
import re
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

STRENGTH_LABEL = {'strong': '强推荐', 'weak': '弱推荐', 'ungraded': '未分级', 'not_reported': '未报告'}
CERTAINTY_LABEL = {'high': '高', 'moderate': '中', 'low': '低', 'very_low': '极低', 'not_reported': '未报告'}
TYPE_LABEL = {'guideline': '指南', 'consensus': '专家共识', 'standard': '团体标准', 'other': '其他'}


def _rows(result) -> list[dict[str, Any]]:
    return [dict(r._mapping) for r in result]


def _snippet(txt: str | None, q: str | None, width: int = 120) -> str:
    if not txt:
        return ''
    if not q:
        return txt[:width * 2]
    i = txt.find(q)
    if i < 0:
        return txt[:width * 2]
    s = max(0, i - width // 2)
    return ('…' if s > 0 else '') + txt[s:s + width * 2] + ('…' if s + width * 2 < len(txt) else '')


class EbtcmDao:
    # ======================= 指南 =======================
    @classmethod
    async def guideline_page(cls, db: AsyncSession, q) -> tuple[list[dict], int]:
        where, p = ['g.is_active'], {}
        if q.keyword:
            where.append('(g.title ILIKE :kw OR g.organization ILIKE :kw OR g.citation ILIKE :kw)'); p['kw'] = f'%{q.keyword}%'
        if q.guideline_type: where.append('g.guideline_type = :gt'); p['gt'] = q.guideline_type
        if q.domain: where.append('g.domain = :dm'); p['dm'] = q.domain
        if q.organization: where.append('g.organization ILIKE :org'); p['org'] = f'%{q.organization}%'
        if q.status: where.append('g.status = :st'); p['st'] = q.status
        if q.year_from: where.append('g.publication_year >= :yf'); p['yf'] = q.year_from
        if q.year_to: where.append('g.publication_year <= :yt'); p['yt'] = q.year_to
        if q.missing == 'year': where.append('g.publication_year = 0')
        if q.missing == 'organization': where.append('g.organization IS NULL')
        if q.missing == 'title': where.append(r"g.title ~ '^\d+$'")
        if q.missing == 'domain': where.append("(g.domain IS NULL OR g.domain = '其他')")
        w = ' AND '.join(where)
        total = (await db.execute(text(f'SELECT count(*) FROM kb.guideline g WHERE {w}'), p)).scalar()
        p.update(lim=q.page_size, off=(q.page_num - 1) * q.page_size)
        rows = _rows(await db.execute(text(f'''
            SELECT g.id, g.title, g.organization, g.guideline_type, g.publication_year, g.domain, g.status, g.doi, g.citation,
                   g.authors, g.keywords, g.is_active, g.created, g.modified,
                   (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id) AS recommendation_count,
                   (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id AND r.verified) AS verified_count,
                   (SELECT count(*) FROM kb.guideline_passage s WHERE s.guideline_id = g.id) AS passage_count
            FROM kb.guideline g WHERE {w} ORDER BY g.publication_year DESC, g.title LIMIT :lim OFFSET :off'''), p))
        return rows, total

    @classmethod
    async def guideline_get(cls, db: AsyncSession, gid: UUID) -> dict | None:
        rows = _rows(await db.execute(text('''
            SELECT g.*, s.title AS supersedes_title,
                   (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id) AS recommendation_count,
                   (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id AND r.verified) AS verified_count,
                   (SELECT count(*) FROM kb.guideline_passage p WHERE p.guideline_id = g.id) AS passage_count,
                   (SELECT count(*) FROM kb.reference f WHERE f.guideline_id = g.id) AS reference_count
            FROM kb.guideline g LEFT JOIN kb.guideline s ON s.id = g.supersedes_id WHERE g.id = :id'''), {'id': gid}))
        return rows[0] if rows else None

    @classmethod
    async def guideline_update(cls, db: AsyncSession, data: dict) -> None:
        gid = data.pop('id')
        cols = {k: v for k, v in data.items() if v is not None}
        if not cols:
            return
        sets = ', '.join(f'{k} = :{k}' for k in cols)
        await db.execute(text(f'UPDATE kb.guideline SET {sets}, modified = now() WHERE id = :id'), {**cols, 'id': gid})

    @classmethod
    async def guideline_bundle(cls, db: AsyncSession, gid: UUID) -> dict | None:
        g = await cls.guideline_get(db, gid)
        if not g:
            return None
        passages = _rows(await db.execute(text('''
            SELECT id, section, section_path, passage_type, block_type, text, table_html, page, sequence_no, text_source, bbox, verified
            FROM kb.guideline_passage WHERE guideline_id = :id AND is_active ORDER BY sequence_no'''), {'id': gid}))
        recos = await cls.recommendations_with_details(db, 'r.guideline_id = :gid', {'gid': gid})
        refs = _rows(await db.execute(text('''
            SELECT id, ref_number, citation_text, ref_type, doi, pmid FROM kb.reference WHERE guideline_id = :id ORDER BY ref_number'''), {'id': gid}))
        versions = _rows(await db.execute(text('''
            SELECT id, title, publication_year, status FROM kb.guideline
            WHERE (supersedes_id = :id OR id = (SELECT supersedes_id FROM kb.guideline WHERE id = :id)) AND id <> :id'''), {'id': gid}))
        # 章节目录
        toc, seen = [], set()
        for ps in passages:
            sp = ps.get('section_path') or ''
            if sp and sp not in seen:
                seen.add(sp); toc.append({'path': sp, 'depth': sp.count(' › '), 'firstSeq': ps['sequence_no']})
        return {'guideline': g, 'passages': passages, 'recommendations': recos, 'references': refs, 'versions': versions, 'toc': toc}

    # ======================= 推荐意见 =======================
    @classmethod
    async def recommendations_with_details(cls, db: AsyncSession, where: str, params: dict, order: str = 'r.created', limit: int | None = None, offset: int = 0) -> list[dict]:
        lim = f'LIMIT {int(limit)} OFFSET {int(offset)}' if limit else ''
        rows = _rows(await db.execute(text(f'''
            SELECT r.id, r.guideline_id, g.title AS guideline_title, g.publication_year, g.guideline_type, g.organization, g.domain, g.status AS guideline_status,
                   r.passage_id, r.label, r.text_original, r.conditions, r.dosage, r.direction, r.strength, r.certainty, r.grading_original,
                   r.study_type, r.study_count, r.sample_size, r.evidence_summary, r.safety_summary, r.source_page, r.source_section,
                   r.extraction_method, r.verified, r.cited_refs, r.is_active,
                   COALESCE((SELECT json_agg(json_build_object('type', x.context_type, 'text', x.text_original, 'role', x.role, 'conceptId', x.concept_id) ORDER BY x.context_type)
                             FROM kb.recommendation_context x WHERE x.recommendation_id = r.id), '[]'::json) AS contexts,
                   COALESCE((SELECT json_agg(json_build_object('refNumber', f.ref_number, 'citation', f.citation_text, 'refType', f.ref_type, 'doi', f.doi) ORDER BY f.ref_number)
                             FROM kb.recommendation_reference rr JOIN kb.reference f ON f.id = rr.reference_id WHERE rr.recommendation_id = r.id), '[]'::json) AS references
            FROM kb.recommendation r JOIN kb.guideline g ON g.id = r.guideline_id
            WHERE {where} ORDER BY {order} {lim}'''), params))
        return rows

    @classmethod
    async def recommendation_page(cls, db: AsyncSession, q) -> tuple[list[dict], int]:
        where, p = ['r.is_active'], {}
        if q.keyword: where.append('r.text_original ILIKE :kw'); p['kw'] = f'%{q.keyword}%'
        if q.guideline_id: where.append('r.guideline_id = :gid'); p['gid'] = q.guideline_id
        if q.direction: where.append('r.direction = :dr'); p['dr'] = q.direction
        if q.strength: where.append('r.strength = :st'); p['st'] = q.strength
        if q.certainty: where.append('r.certainty = :ce'); p['ce'] = q.certainty
        if q.verified is not None: where.append('r.verified = :vf'); p['vf'] = q.verified
        if q.quote_issue: where.append("r.source_section LIKE '引用校验未通过%'")
        if q.drug:
            where.append("EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type = 'drug' AND x.text_original ILIKE :drug)"); p['drug'] = f'%{q.drug}%'
        if q.disease:
            where.append("EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type = 'disease' AND x.text_original ILIKE :dis)"); p['dis'] = f'%{q.disease}%'
        w = ' AND '.join(where)
        total = (await db.execute(text(f'SELECT count(*) FROM kb.recommendation r WHERE {w}'), p)).scalar()
        rows = await cls.recommendations_with_details(db, w, p, 'r.created DESC', q.page_size, (q.page_num - 1) * q.page_size)
        return rows, total

    @classmethod
    async def recommendation_get(cls, db: AsyncSession, rid: UUID) -> dict | None:
        rows = await cls.recommendations_with_details(db, 'r.id = :id', {'id': rid})
        return rows[0] if rows else None

    @classmethod
    async def recommendation_update(cls, db: AsyncSession, data: dict) -> None:
        rid = data.pop('id')
        cols = {k: v for k, v in data.items() if v is not None}
        if cols:
            sets = ', '.join(f'{k} = :{k}' for k in cols)
            await db.execute(text(f'UPDATE kb.recommendation SET {sets}, modified = now() WHERE id = :id'), {**cols, 'id': rid})

    @classmethod
    async def recommendation_verify(cls, db: AsyncSession, ids: list[UUID], verified: bool) -> int:
        r = await db.execute(text('UPDATE kb.recommendation SET verified = :v, modified = now() WHERE id = ANY(:ids)'), {'v': verified, 'ids': ids})
        return r.rowcount

    # ======================= 段落 =======================
    @classmethod
    async def passage_page(cls, db: AsyncSession, q) -> tuple[list[dict], int]:
        where, p = ['p.is_active'], {}
        if q.guideline_id: where.append('p.guideline_id = :gid'); p['gid'] = q.guideline_id
        if q.keyword: where.append('p.text ILIKE :kw'); p['kw'] = f'%{q.keyword}%'
        if q.passage_type: where.append('p.passage_type = :pt'); p['pt'] = q.passage_type
        if q.block_type: where.append('p.block_type = :bt'); p['bt'] = q.block_type
        w = ' AND '.join(where)
        total = (await db.execute(text(f'SELECT count(*) FROM kb.guideline_passage p WHERE {w}'), p)).scalar()
        p.update(lim=q.page_size, off=(q.page_num - 1) * q.page_size)
        rows = _rows(await db.execute(text(f'''
            SELECT p.id, p.guideline_id, g.title AS guideline_title, p.section, p.section_path, p.passage_type, p.block_type, p.text, p.table_html,
                   p.page, p.sequence_no, p.text_source, p.bbox, p.verified, p.is_active
            FROM kb.guideline_passage p JOIN kb.guideline g ON g.id = p.guideline_id WHERE {w}
            ORDER BY p.guideline_id, p.sequence_no LIMIT :lim OFFSET :off'''), p))
        return rows, total

    @classmethod
    async def passage_update(cls, db: AsyncSession, data: dict) -> None:
        pid = data.pop('id')
        cols = {k: v for k, v in data.items() if v is not None}
        if cols:
            sets = ', '.join(f'{k} = :{k}' for k in cols)
            await db.execute(text(f'UPDATE kb.guideline_passage SET {sets}, modified = now() WHERE id = :id'), {**cols, 'id': pid})

    # ======================= 术语 =======================
    @classmethod
    async def concept_page(cls, db: AsyncSession, q) -> tuple[list[dict], int]:
        where, p = ['c.is_active'], {}
        if q.keyword: where.append('(c.name ILIKE :kw OR array_to_string(c.synonyms, \',\') ILIKE :kw)'); p['kw'] = f'%{q.keyword}%'
        if q.concept_type: where.append('c.concept_type = :ct'); p['ct'] = q.concept_type
        w = ' AND '.join(where)
        total = (await db.execute(text(f'SELECT count(*) FROM kb.concept c WHERE {w}'), p)).scalar()
        p.update(lim=q.page_size, off=(q.page_num - 1) * q.page_size)
        rows = _rows(await db.execute(text(f'''
            SELECT c.id, c.concept_type, c.name, c.synonyms, c.parent_id, c.is_active,
                   (SELECT count(*) FROM kb.recommendation_context x WHERE x.concept_id = c.id) AS usage_count
            FROM kb.concept c WHERE {w} ORDER BY usage_count DESC, c.name LIMIT :lim OFFSET :off'''), p))
        return rows, total

    @classmethod
    async def concept_save(cls, db: AsyncSession, data: dict) -> UUID:
        if data.get('id'):
            await db.execute(text('UPDATE kb.concept SET concept_type=:concept_type, name=:name, synonyms=:synonyms, parent_id=:parent_id, modified=now() WHERE id=:id'), data)
            return data['id']
        r = await db.execute(text('INSERT INTO kb.concept(concept_type, name, synonyms, parent_id) VALUES(:concept_type, :name, :synonyms, :parent_id) ON CONFLICT (concept_type, name) DO UPDATE SET synonyms = EXCLUDED.synonyms RETURNING id'),
                             {k: data.get(k) for k in ('concept_type', 'name', 'synonyms', 'parent_id')})
        return r.scalar()

    @classmethod
    async def concept_delete(cls, db: AsyncSession, ids: list[UUID]) -> int:
        await db.execute(text('UPDATE kb.recommendation_context SET concept_id = NULL WHERE concept_id = ANY(:ids)'), {'ids': ids})
        r = await db.execute(text('DELETE FROM kb.concept WHERE id = ANY(:ids)'), {'ids': ids})
        return r.rowcount

    @classmethod
    async def concept_merge(cls, db: AsyncSession, concept_type: str, name: str, aliases: list[str]) -> dict:
        """把若干原始写法归并到一个标准术语：建/更新 concept，并回填 recommendation_context.concept_id"""
        names = sorted({a.strip() for a in aliases + [name] if a and a.strip()})
        cid = await cls.concept_save(db, {'concept_type': concept_type, 'name': name, 'synonyms': [n for n in names if n != name], 'parent_id': None})
        r = await db.execute(text('UPDATE kb.recommendation_context SET concept_id = :cid WHERE context_type = :ct AND text_original = ANY(:names)'),
                             {'cid': cid, 'ct': concept_type, 'names': names})
        return {'conceptId': cid, 'mapped': r.rowcount}

    @classmethod
    async def context_terms(cls, db: AsyncSession, context_type: str, keyword: str | None, limit: int = 50) -> list[dict]:
        """某类实体的原始写法及出现次数（术语归一的工作台）"""
        p = {'ct': context_type, 'lim': limit}
        kw = ''
        if keyword: kw = 'AND x.text_original ILIKE :kw'; p['kw'] = f'%{keyword}%'
        return _rows(await db.execute(text(f'''
            SELECT x.text_original AS term, count(*) AS n, count(DISTINCT r.guideline_id) AS guidelines,
                   max(c.name) AS concept_name, bool_or(x.concept_id IS NOT NULL) AS mapped
            FROM kb.recommendation_context x JOIN kb.recommendation r ON r.id = x.recommendation_id LEFT JOIN kb.concept c ON c.id = x.concept_id
            WHERE x.context_type = :ct {kw} GROUP BY x.text_original ORDER BY n DESC LIMIT :lim'''), p))

    # ======================= 统计 =======================
    @classmethod
    async def stats_overview(cls, db: AsyncSession) -> dict:
        one = lambda s: db.execute(text(s))  # noqa: E731
        counts = _rows(await one('''
            SELECT (SELECT count(*) FROM kb.guideline) AS guidelines, (SELECT count(*) FROM kb.recommendation) AS recommendations,
                   (SELECT count(*) FROM kb.recommendation WHERE verified) AS verified, (SELECT count(*) FROM kb.guideline_passage) AS passages,
                   (SELECT count(*) FROM kb.reference) AS "references", (SELECT count(*) FROM kb.recommendation_context) AS contexts,
                   (SELECT count(*) FROM kb.concept) AS concepts,
                   (SELECT count(*) FROM kb.guideline WHERE publication_year = 0) AS missing_year,
                   (SELECT count(*) FROM kb.guideline WHERE organization IS NULL) AS missing_org,
                   (SELECT count(*) FROM kb.recommendation WHERE source_section LIKE '引用校验未通过%') AS quote_issues'''))[0]
        by_year = _rows(await one('SELECT publication_year AS year, count(*) AS n FROM kb.guideline WHERE publication_year > 0 GROUP BY 1 ORDER BY 1'))
        by_type = _rows(await one('SELECT guideline_type AS type, count(*) AS n FROM kb.guideline GROUP BY 1 ORDER BY 2 DESC'))
        by_domain = _rows(await one('SELECT COALESCE(domain, \'未分类\') AS domain, count(*) AS n FROM kb.guideline GROUP BY 1 ORDER BY 2 DESC LIMIT 15'))
        by_strength = _rows(await one('SELECT strength, count(*) AS n FROM kb.recommendation GROUP BY 1'))
        by_certainty = _rows(await one('SELECT certainty, count(*) AS n FROM kb.recommendation GROUP BY 1'))
        top_org = _rows(await one('SELECT organization, count(*) AS n FROM kb.guideline WHERE organization IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10'))
        top_drug = _rows(await one("SELECT text_original AS term, count(*) AS n FROM kb.recommendation_context WHERE context_type='drug' GROUP BY 1 ORDER BY 2 DESC LIMIT 15"))
        top_disease = _rows(await one("SELECT text_original AS term, count(*) AS n FROM kb.recommendation_context WHERE context_type='disease' GROUP BY 1 ORDER BY 2 DESC LIMIT 15"))
        return {'counts': counts, 'byYear': by_year, 'byType': by_type, 'byDomain': by_domain, 'byStrength': by_strength,
                'byCertainty': by_certainty, 'topOrganization': top_org, 'topDrug': top_drug, 'topDisease': top_disease}

    # ======================= 公开检索 =======================
    @classmethod
    def _guideline_filters(cls, q, p: dict, alias: str = 'g') -> list[str]:
        w = [f'{alias}.is_active']
        if q.guideline_type: w.append(f'{alias}.guideline_type = :gt'); p['gt'] = q.guideline_type
        if q.domain: w.append(f'{alias}.domain = :dm'); p['dm'] = q.domain
        if q.organization: w.append(f'{alias}.organization = :org'); p['org'] = q.organization
        if q.year_from: w.append(f'{alias}.publication_year >= :yf'); p['yf'] = q.year_from
        if q.year_to: w.append(f'{alias}.publication_year <= :yt'); p['yt'] = q.year_to
        return w

    @classmethod
    async def search(cls, db: AsyncSession, q) -> dict:
        p: dict[str, Any] = {}
        kw = (q.q or '').strip()
        if kw: p['kw'] = f'%{kw}%'
        gw = cls._guideline_filters(q, p)
        off = (q.page_num - 1) * q.page_size
        p.update(lim=q.page_size, off=off)
        order = {'year_desc': 'g.publication_year DESC', 'year_asc': 'g.publication_year ASC'}.get(q.sort)
        if q.scope == 'guideline':
            if kw:
                gw.append('''(g.title ILIKE :kw OR g.organization ILIKE :kw OR EXISTS (SELECT 1 FROM kb.recommendation r WHERE r.guideline_id = g.id AND r.text_original ILIKE :kw)
                              OR EXISTS (SELECT 1 FROM kb.recommendation_context x JOIN kb.recommendation r ON r.id = x.recommendation_id WHERE r.guideline_id = g.id AND x.text_original ILIKE :kw))''')
            w = ' AND '.join(gw)
            total = (await db.execute(text(f'SELECT count(*) FROM kb.guideline g WHERE {w}'), p)).scalar()
            ob = order or ('CASE WHEN g.title ILIKE :kw THEN 0 ELSE 1 END, g.publication_year DESC' if kw else 'g.publication_year DESC')
            rows = _rows(await db.execute(text(f'''
                SELECT g.id, g.title, g.organization, g.guideline_type, g.publication_year, g.domain, g.status, g.doi, g.abstract, g.keywords,
                       (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id) AS recommendation_count,
                       (SELECT string_agg(DISTINCT x.text_original, '、') FROM (SELECT x.text_original FROM kb.recommendation_context x JOIN kb.recommendation r ON r.id = x.recommendation_id
                            WHERE r.guideline_id = g.id AND x.context_type = 'drug' GROUP BY x.text_original ORDER BY count(*) DESC LIMIT 6) x) AS top_drugs,
                       (SELECT string_agg(DISTINCT x.text_original, '、') FROM (SELECT x.text_original FROM kb.recommendation_context x JOIN kb.recommendation r ON r.id = x.recommendation_id
                            WHERE r.guideline_id = g.id AND x.context_type = 'disease' GROUP BY x.text_original ORDER BY count(*) DESC LIMIT 4) x) AS top_diseases,
                       {"(SELECT r.text_original FROM kb.recommendation r WHERE r.guideline_id = g.id AND r.text_original ILIKE :kw LIMIT 1)" if kw else "NULL"} AS hit_text
                FROM kb.guideline g WHERE {w} ORDER BY {ob} LIMIT :lim OFFSET :off'''), p))
            for r in rows:
                r['snippet'] = _snippet(r.pop('hit_text') or r.get('abstract'), kw)
            facets = await cls._facets_guideline(db, w, p)
        elif q.scope == 'recommendation':
            rw = ['r.is_active'] + gw
            if kw: rw.append('(r.text_original ILIKE :kw OR EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.text_original ILIKE :kw))')
            if q.strength: rw.append('r.strength = :st'); p['st'] = q.strength
            if q.certainty: rw.append('r.certainty = :ce'); p['ce'] = q.certainty
            if q.direction: rw.append('r.direction = :dr'); p['dr'] = q.direction
            w = ' AND '.join(rw)
            total = (await db.execute(text(f'SELECT count(*) FROM kb.recommendation r JOIN kb.guideline g ON g.id = r.guideline_id WHERE {w}'), p)).scalar()
            ob = order or ("CASE r.strength WHEN 'strong' THEN 0 WHEN 'weak' THEN 1 ELSE 2 END, g.publication_year DESC")
            rows = await cls.recommendations_with_details(db, w, p, ob, q.page_size, off)
            for r in rows:
                r['snippet'] = _snippet(r['text_original'], kw)
            facets = await cls._facets_recommendation(db, w, p)
        else:  # passage
            pw = ['p.is_active'] + gw
            if kw: pw.append('p.text ILIKE :kw')
            if q.passage_type: pw.append('p.passage_type = :pt'); p['pt'] = q.passage_type
            w = ' AND '.join(pw)
            total = (await db.execute(text(f'SELECT count(*) FROM kb.guideline_passage p JOIN kb.guideline g ON g.id = p.guideline_id WHERE {w}'), p)).scalar()
            ob = order or 'g.publication_year DESC, p.sequence_no'
            rows = _rows(await db.execute(text(f'''
                SELECT p.id, p.guideline_id, g.title AS guideline_title, g.publication_year, g.guideline_type, g.organization, p.section_path, p.passage_type, p.block_type,
                       p.text, p.page, p.sequence_no
                FROM kb.guideline_passage p JOIN kb.guideline g ON g.id = p.guideline_id WHERE {w} ORDER BY {ob} LIMIT :lim OFFSET :off'''), p))
            for r in rows:
                r['snippet'] = _snippet(r['text'], kw)
            facets = await cls._facets_passage(db, w, p)
        return {'total': total, 'rows': rows, 'facets': facets, 'pageNum': q.page_num, 'pageSize': q.page_size}

    @classmethod
    async def _facet(cls, db, sql: str, p: dict) -> list[dict]:
        return _rows(await db.execute(text(sql), p))

    @classmethod
    async def _facets_guideline(cls, db, w: str, p: dict) -> dict:
        base = f'FROM kb.guideline g WHERE {w}'
        return {
            'year': await cls._facet(db, f'SELECT g.publication_year AS key, count(*) AS n {base} AND g.publication_year > 0 GROUP BY 1 ORDER BY 1 DESC', p),
            'type': await cls._facet(db, f'SELECT g.guideline_type AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
            'domain': await cls._facet(db, f'SELECT g.domain AS key, count(*) AS n {base} AND g.domain IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 15', p),
            'organization': await cls._facet(db, f'SELECT g.organization AS key, count(*) AS n {base} AND g.organization IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10', p),
        }

    @classmethod
    async def _facets_recommendation(cls, db, w: str, p: dict) -> dict:
        base = f'FROM kb.recommendation r JOIN kb.guideline g ON g.id = r.guideline_id WHERE {w}'
        return {
            'year': await cls._facet(db, f'SELECT g.publication_year AS key, count(*) AS n {base} AND g.publication_year > 0 GROUP BY 1 ORDER BY 1 DESC', p),
            'type': await cls._facet(db, f'SELECT g.guideline_type AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
            'domain': await cls._facet(db, f'SELECT g.domain AS key, count(*) AS n {base} AND g.domain IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 15', p),
            'strength': await cls._facet(db, f'SELECT r.strength AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
            'certainty': await cls._facet(db, f'SELECT r.certainty AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
            'direction': await cls._facet(db, f'SELECT r.direction AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
        }

    @classmethod
    async def _facets_passage(cls, db, w: str, p: dict) -> dict:
        base = f'FROM kb.guideline_passage p JOIN kb.guideline g ON g.id = p.guideline_id WHERE {w}'
        return {
            'year': await cls._facet(db, f'SELECT g.publication_year AS key, count(*) AS n {base} AND g.publication_year > 0 GROUP BY 1 ORDER BY 1 DESC', p),
            'type': await cls._facet(db, f'SELECT g.guideline_type AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
            'domain': await cls._facet(db, f'SELECT g.domain AS key, count(*) AS n {base} AND g.domain IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 15', p),
            'passageType': await cls._facet(db, f'SELECT p.passage_type AS key, count(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC', p),
        }

    @classmethod
    async def suggest(cls, db: AsyncSession, q: str, limit: int = 10) -> list[dict]:
        p = {'kw': f'%{q}%', 'pre': f'{q}%', 'lim': limit}
        terms = _rows(await db.execute(text('''
            SELECT x.context_type AS type, x.text_original AS term, count(*) AS n FROM kb.recommendation_context x
            WHERE x.text_original ILIKE :kw GROUP BY 1, 2 ORDER BY (x.text_original ILIKE :pre) DESC, n DESC LIMIT :lim'''), p))
        gls = _rows(await db.execute(text('SELECT id, title FROM kb.guideline WHERE title ILIKE :kw ORDER BY publication_year DESC LIMIT 5'), p))
        return [{'type': t['type'], 'term': t['term'], 'n': t['n']} for t in terms] + [{'type': 'guideline', 'term': g['title'], 'id': str(g['id'])} for g in gls]

    @classmethod
    async def entity_page(cls, db: AsyncSession, context_type: str, term: str, strength: str | None, page_num: int, page_size: int) -> dict:
        """药品/疾病/证候页：跨指南聚合推荐意见（同义词：concept 的 synonyms 一并匹配）"""
        p: dict[str, Any] = {'ct': context_type, 'term': term}
        syn = _rows(await db.execute(text('SELECT name, synonyms FROM kb.concept WHERE concept_type = :ct AND (name = :term OR :term = ANY(synonyms))'), p))
        names = {term}
        for s in syn:
            names.add(s['name']); names.update(s['synonyms'] or [])
        p['names'] = list(names)
        w = 'r.is_active AND EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type = :ct AND x.text_original = ANY(:names))'
        if strength: w += ' AND r.strength = :st'; p['st'] = strength
        total = (await db.execute(text(f'SELECT count(*) FROM kb.recommendation r WHERE {w}'), p)).scalar()
        rows = await cls.recommendations_with_details(db, w, p, "g.publication_year DESC, CASE r.strength WHEN 'strong' THEN 0 WHEN 'weak' THEN 1 ELSE 2 END", page_size, (page_num - 1) * page_size)
        base = f'FROM kb.recommendation r JOIN kb.guideline g ON g.id = r.guideline_id WHERE {w}'
        summary = {
            'guidelines': (await db.execute(text(f'SELECT count(DISTINCT r.guideline_id) {base}'), p)).scalar(),
            'byStrength': _rows(await db.execute(text(f'SELECT r.strength AS key, count(*) AS n {base} GROUP BY 1'), p)),
            'byYear': _rows(await db.execute(text(f'SELECT g.publication_year AS key, count(*) AS n {base} AND g.publication_year > 0 GROUP BY 1 ORDER BY 1'), p)),
            'related': _rows(await db.execute(text(f'''
                SELECT x2.context_type AS type, x2.text_original AS term, count(*) AS n
                FROM kb.recommendation r JOIN kb.guideline g ON g.id = r.guideline_id
                JOIN kb.recommendation_context x2 ON x2.recommendation_id = r.id AND x2.context_type <> :ct AND x2.text_original <> ALL(:names)
                WHERE {w} GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20'''), p)),
            'names': list(names),
        }
        return {'term': term, 'type': context_type, 'total': total, 'rows': rows, 'summary': summary, 'pageNum': page_num, 'pageSize': page_size}

    @classmethod
    async def pico(cls, db: AsyncSession, q) -> dict:
        p: dict[str, Any] = {}
        w = ['r.is_active']
        def ctx(ctype: str, val: str | None, key: str):
            if val:
                w.append(f"EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type = '{ctype}' AND x.text_original ILIKE :{key})"); p[key] = f'%{val}%'
        ctx('population', q.population, 'pp'); ctx('drug', q.intervention, 'iv'); ctx('outcome', q.outcome, 'oc'); ctx('disease', q.disease, 'ds'); ctx('syndrome', q.syndrome, 'sy')
        if q.comparator: w.append('(r.text_original ILIKE :cp OR r.conditions ILIKE :cp)'); p['cp'] = f'%{q.comparator}%'
        if q.strength: w.append('r.strength = :st'); p['st'] = q.strength
        ww = ' AND '.join(w)
        total = (await db.execute(text(f'SELECT count(*) FROM kb.recommendation r WHERE {ww}'), p)).scalar()
        rows = await cls.recommendations_with_details(db, ww, p, "CASE r.strength WHEN 'strong' THEN 0 WHEN 'weak' THEN 1 ELSE 2 END, g.publication_year DESC", q.page_size, (q.page_num - 1) * q.page_size)
        return {'total': total, 'rows': rows, 'pageNum': q.page_num, 'pageSize': q.page_size}

    @classmethod
    async def advanced(cls, db: AsyncSession, q) -> dict:
        """字段布尔组合检索（指南粒度）：(c1) AND/OR/NOT (c2) ..."""
        p: dict[str, Any] = {}
        parts: list[str] = []
        for i, c in enumerate(q.conditions):
            key = f'v{i}'; p[key] = f'%{c.value}%' if c.op != 'equals' else c.value
            cmp = '=' if c.op == 'equals' else 'ILIKE'
            if c.field == 'title': expr = f'g.title {cmp} :{key}'
            elif c.field == 'organization': expr = f'g.organization {cmp} :{key}'
            elif c.field == 'domain': expr = f'g.domain {cmp} :{key}'
            elif c.field == 'text': expr = f'EXISTS (SELECT 1 FROM kb.guideline_passage s WHERE s.guideline_id = g.id AND s.text ILIKE :{key})'
            elif c.field == 'keyword': expr = f'(g.title ILIKE :{key} OR EXISTS (SELECT 1 FROM kb.recommendation r WHERE r.guideline_id = g.id AND r.text_original ILIKE :{key}))'
            else:  # drug / disease / syndrome
                expr = f"EXISTS (SELECT 1 FROM kb.recommendation_context x JOIN kb.recommendation r ON r.id = x.recommendation_id WHERE r.guideline_id = g.id AND x.context_type = '{c.field}' AND x.text_original {cmp} :{key})"
            if c.op == 'not_contains': expr = f'NOT ({expr})'
            if not parts: parts.append(f'({expr})')
            else: parts.append({'and': 'AND', 'or': 'OR', 'not': 'AND NOT'}[c.logic] + f' ({expr})')
        w = 'g.is_active' + (' AND (' + ' '.join(parts) + ')' if parts else '')
        if q.year_from: w += ' AND g.publication_year >= :yf'; p['yf'] = q.year_from
        if q.year_to: w += ' AND g.publication_year <= :yt'; p['yt'] = q.year_to
        if q.guideline_type: w += ' AND g.guideline_type = :gt'; p['gt'] = q.guideline_type
        total = (await db.execute(text(f'SELECT count(*) FROM kb.guideline g WHERE {w}'), p)).scalar()
        p.update(lim=q.page_size, off=(q.page_num - 1) * q.page_size)
        rows = _rows(await db.execute(text(f'''
            SELECT g.id, g.title, g.organization, g.guideline_type, g.publication_year, g.domain, g.status, g.abstract,
                   (SELECT count(*) FROM kb.recommendation r WHERE r.guideline_id = g.id) AS recommendation_count
            FROM kb.guideline g WHERE {w} ORDER BY g.publication_year DESC LIMIT :lim OFFSET :off'''), p))
        facets = await cls._facets_guideline(db, w, p)
        return {'total': total, 'rows': rows, 'facets': facets, 'pageNum': q.page_num, 'pageSize': q.page_size}

    @classmethod
    async def compare(cls, db: AsyncSession, disease: str | None, drug: str | None) -> list[dict]:
        """推荐意见对比：同一疾病（或药品）下各指南的推荐，按指南分组"""
        p: dict[str, Any] = {}
        w = ['r.is_active']
        if disease: w.append("EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type='disease' AND x.text_original ILIKE :ds)"); p['ds'] = f'%{disease}%'
        if drug: w.append("EXISTS (SELECT 1 FROM kb.recommendation_context x WHERE x.recommendation_id = r.id AND x.context_type='drug' AND x.text_original ILIKE :dg)"); p['dg'] = f'%{drug}%'
        rows = await cls.recommendations_with_details(db, ' AND '.join(w), p, 'g.publication_year DESC, g.title', 300)
        groups: dict[str, dict] = {}
        for r in rows:
            gk = str(r['guideline_id'])
            groups.setdefault(gk, {'guidelineId': gk, 'title': r['guideline_title'], 'year': r['publication_year'], 'organization': r['organization'], 'status': r['guideline_status'], 'items': []})['items'].append(r)
        return list(groups.values())
