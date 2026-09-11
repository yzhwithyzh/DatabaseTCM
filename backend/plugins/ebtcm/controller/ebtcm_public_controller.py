"""
EB_TCM 公开检索接口（客户端网站使用，无需登录）
"""
import os
import re
from typing import Annotated
from uuid import UUID

from fastapi import Body, Path, Query, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_session import DBSessionDependency
from common.router import APIRouterPro
from plugins.ebtcm.entity.vo.ebtcm_vo import AdvancedQueryModel, PicoQueryModel, SearchQueryModel
from plugins.ebtcm.service.ebtcm_service import EbtcmService
from utils.response_util import ResponseUtil

ebtcm_public_controller = APIRouterPro(prefix='/ebtcm/public', order_num=31, tags=['指南知识库-公开检索'])

DB = Annotated[AsyncSession, DBSessionDependency()]


@ebtcm_public_controller.get('/search', summary='综合检索（指南/推荐意见/段落）+ 分面统计')
async def search(request: Request, q: Annotated[SearchQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.search(query_db, q))


@ebtcm_public_controller.get('/suggest', summary='检索联想（药品/疾病/证候/指南）')
async def suggest(request: Request, query_db: DB, q: str = Query(min_length=1)) -> Response:
    return ResponseUtil.success(data=await EbtcmService.suggest(query_db, q))


@ebtcm_public_controller.post('/advanced', summary='高级检索（字段布尔组合）')
async def advanced(request: Request, body: Annotated[AdvancedQueryModel, Body()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.advanced(query_db, body))


@ebtcm_public_controller.get('/pico', summary='PICOS 检索')
async def pico(request: Request, q: Annotated[PicoQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.pico(query_db, q))


@ebtcm_public_controller.get('/guideline/{gid}', summary='指南详情（元数据、目录、段落、推荐意见、参考文献、版本）')
async def guideline_detail(request: Request, gid: Annotated[UUID, Path()], query_db: DB) -> Response:
    data = await EbtcmService.guideline_bundle(query_db, gid)
    return ResponseUtil.success(data=data) if data else ResponseUtil.failure(msg='指南不存在')


@ebtcm_public_controller.get('/guideline/{gid}/pdf', summary='指南原文 PDF')
async def guideline_pdf(request: Request, gid: Annotated[UUID, Path()], query_db: DB):
    row = (await query_db.execute(text('SELECT source_file, title FROM kb.guideline WHERE id = :id'), {'id': gid})).first()
    path = _resolve_pdf_path(row[0]) if row and row[0] else None
    if not path:
        return ResponseUtil.failure(msg='原文文件不存在')
    return FileResponse(path, media_type='application/pdf', filename=f'{row[1][:60]}.pdf', content_disposition_type='inline')


def _resolve_pdf_path(source_file: str) -> str | None:
    """
    定位指南 PDF：优先在环境变量 EBTCM_PDF_DIR 指定的目录下按文件名查找（线上部署用），
    未配置或找不到时回退到 kb.guideline.source_file 里记录的原始绝对路径（本地抽取环境）。
    """
    name = re.split(r'[\\/]', source_file)[-1]
    base = os.environ.get('EBTCM_PDF_DIR', '').strip()
    if base:
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate):
            return candidate
    return source_file if os.path.isfile(source_file) else None


@ebtcm_public_controller.get('/entity/{context_type}', summary='药品/疾病/证候/人群页：跨指南推荐意见聚合')
async def entity_page(
    request: Request, context_type: Annotated[str, Path()], query_db: DB,
    term: str = Query(min_length=1), strength: str | None = Query(None), page_num: int = Query(1, alias='pageNum'), page_size: int = Query(20, alias='pageSize'),
) -> Response:
    if context_type not in ('drug', 'disease', 'syndrome', 'population', 'outcome'):
        return ResponseUtil.failure(msg='实体类型不支持')
    return ResponseUtil.success(data=await EbtcmService.entity_page(query_db, context_type, term, strength, page_num, page_size))


@ebtcm_public_controller.get('/compare', summary='推荐意见对比（按指南分组）')
async def compare(request: Request, query_db: DB, disease: str | None = Query(None), drug: str | None = Query(None)) -> Response:
    if not disease and not drug:
        return ResponseUtil.failure(msg='请提供疾病或药品')
    return ResponseUtil.success(data=await EbtcmService.compare(query_db, disease, drug))


@ebtcm_public_controller.get('/stats', summary='知识库统计（首页图表）')
async def stats(request: Request, query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.stats_overview(query_db))


@ebtcm_public_controller.get('/labels', summary='枚举中文标签')
async def labels(request: Request) -> Response:
    return ResponseUtil.success(data=EbtcmService.labels)
