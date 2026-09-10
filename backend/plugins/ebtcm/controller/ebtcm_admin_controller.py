"""
EB_TCM 后台管理接口（需登录）
"""
from typing import Annotated
from uuid import UUID

from fastapi import Body, Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_session import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from plugins.ebtcm.entity.vo.ebtcm_vo import (
    ConceptMergeModel,
    ConceptPageQueryModel,
    ConceptSaveModel,
    GuidelinePageQueryModel,
    GuidelineUpdateModel,
    PassagePageQueryModel,
    PassageUpdateModel,
    RecommendationPageQueryModel,
    RecommendationUpdateModel,
    VerifyBatchModel,
)
from plugins.ebtcm.service.ebtcm_service import EbtcmService
from utils.response_util import ResponseUtil

ebtcm_admin_controller = APIRouterPro(prefix='/ebtcm', order_num=30, tags=['指南知识库-管理'], dependencies=[PreAuthDependency()])

DB = Annotated[AsyncSession, DBSessionDependency()]


# ---------------- 概览 ----------------
@ebtcm_admin_controller.get('/stats/overview', summary='知识库数据概览', dependencies=[UserInterfaceAuthDependency('ebtcm:stats:list')])
async def stats_overview(request: Request, query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.stats_overview(query_db))


# ---------------- 指南 ----------------
@ebtcm_admin_controller.get('/guideline/list', summary='指南分页列表', dependencies=[UserInterfaceAuthDependency('ebtcm:guideline:list')])
async def guideline_list(request: Request, q: Annotated[GuidelinePageQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(dict_content=await EbtcmService.guideline_page(query_db, q))


@ebtcm_admin_controller.get('/guideline/{gid}', summary='指南详情', dependencies=[UserInterfaceAuthDependency('ebtcm:guideline:query')])
async def guideline_get(request: Request, gid: Annotated[UUID, Path()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.guideline_get(query_db, gid))


@ebtcm_admin_controller.get('/guideline/{gid}/bundle', summary='指南全文包（段落/推荐/文献）', dependencies=[UserInterfaceAuthDependency('ebtcm:guideline:query')])
async def guideline_bundle(request: Request, gid: Annotated[UUID, Path()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.guideline_bundle(query_db, gid))


@ebtcm_admin_controller.put('/guideline', summary='修改指南元数据', dependencies=[UserInterfaceAuthDependency('ebtcm:guideline:edit')])
async def guideline_update(request: Request, body: Annotated[GuidelineUpdateModel, Body()], query_db: DB) -> Response:
    await EbtcmService.guideline_update(query_db, body)
    return ResponseUtil.success(msg='修改成功')


# ---------------- 推荐意见 ----------------
@ebtcm_admin_controller.get('/recommendation/list', summary='推荐意见分页列表', dependencies=[UserInterfaceAuthDependency('ebtcm:recommendation:list')])
async def recommendation_list(request: Request, q: Annotated[RecommendationPageQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(dict_content=await EbtcmService.recommendation_page(query_db, q))


@ebtcm_admin_controller.get('/recommendation/{rid}', summary='推荐意见详情', dependencies=[UserInterfaceAuthDependency('ebtcm:recommendation:list')])
async def recommendation_get(request: Request, rid: Annotated[UUID, Path()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.recommendation_get(query_db, rid))


@ebtcm_admin_controller.put('/recommendation', summary='修改推荐意见', dependencies=[UserInterfaceAuthDependency('ebtcm:recommendation:edit')])
async def recommendation_update(request: Request, body: Annotated[RecommendationUpdateModel, Body()], query_db: DB) -> Response:
    await EbtcmService.recommendation_update(query_db, body)
    return ResponseUtil.success(msg='修改成功')


@ebtcm_admin_controller.put('/recommendation/verify', summary='批量核验/取消核验', dependencies=[UserInterfaceAuthDependency('ebtcm:recommendation:verify')])
async def recommendation_verify(request: Request, body: Annotated[VerifyBatchModel, Body()], query_db: DB) -> Response:
    n = await EbtcmService.recommendation_verify(query_db, body.ids, body.verified)
    return ResponseUtil.success(msg=f'已更新 {n} 条')


# ---------------- 段落 ----------------
@ebtcm_admin_controller.get('/passage/list', summary='段落分页列表', dependencies=[UserInterfaceAuthDependency('ebtcm:passage:list')])
async def passage_list(request: Request, q: Annotated[PassagePageQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(dict_content=await EbtcmService.passage_page(query_db, q))


@ebtcm_admin_controller.put('/passage', summary='修改段落', dependencies=[UserInterfaceAuthDependency('ebtcm:passage:edit')])
async def passage_update(request: Request, body: Annotated[PassageUpdateModel, Body()], query_db: DB) -> Response:
    await EbtcmService.passage_update(query_db, body)
    return ResponseUtil.success(msg='修改成功')


# ---------------- 术语 ----------------
@ebtcm_admin_controller.get('/concept/list', summary='术语分页列表', dependencies=[UserInterfaceAuthDependency('ebtcm:concept:list')])
async def concept_list(request: Request, q: Annotated[ConceptPageQueryModel, Query()], query_db: DB) -> Response:
    return ResponseUtil.success(dict_content=await EbtcmService.concept_page(query_db, q))


@ebtcm_admin_controller.get('/concept/terms', summary='原始实体写法统计（归一工作台）', dependencies=[UserInterfaceAuthDependency('ebtcm:concept:list')])
async def concept_terms(request: Request, query_db: DB, context_type: str = Query('drug'), keyword: str | None = Query(None), limit: int = Query(50)) -> Response:
    return ResponseUtil.success(data=await EbtcmService.context_terms(query_db, context_type, keyword, limit))


@ebtcm_admin_controller.post('/concept', summary='新增/修改术语', dependencies=[UserInterfaceAuthDependency('ebtcm:concept:add')])
async def concept_save(request: Request, body: Annotated[ConceptSaveModel, Body()], query_db: DB) -> Response:
    cid = await EbtcmService.concept_save(query_db, body)
    return ResponseUtil.success(data={'id': str(cid)})


@ebtcm_admin_controller.post('/concept/merge', summary='归并原始写法到标准术语', dependencies=[UserInterfaceAuthDependency('ebtcm:concept:edit')])
async def concept_merge(request: Request, body: Annotated[ConceptMergeModel, Body()], query_db: DB) -> Response:
    return ResponseUtil.success(data=await EbtcmService.concept_merge(query_db, body))


@ebtcm_admin_controller.delete('/concept/{ids}', summary='删除术语', dependencies=[UserInterfaceAuthDependency('ebtcm:concept:remove')])
async def concept_delete(request: Request, ids: Annotated[str, Path()], query_db: DB) -> Response:
    n = await EbtcmService.concept_delete(query_db, [UUID(x) for x in ids.split(',') if x])
    return ResponseUtil.success(msg=f'已删除 {n} 条')
