"""
EB_TCM 请求/响应模型
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)


# ---------- 指南 ----------
class GuidelineModel(_Camel):
    id: UUID | None = None
    title: str | None = None
    citation: str | None = None
    organization: str | None = None
    guideline_type: str | None = None
    publication_year: int | None = None
    domain: str | None = None
    status: str | None = None
    supersedes_id: UUID | None = None
    doi: str | None = None
    source_file: str | None = None
    authors: list[str] | None = None
    keywords: list[str] | None = None
    abstract: str | None = None
    is_active: bool | None = None
    created: datetime | None = None
    modified: datetime | None = None
    # 统计附加字段
    recommendation_count: int | None = None
    passage_count: int | None = None
    verified_count: int | None = None


class GuidelinePageQueryModel(_Camel):
    keyword: str | None = Field(default=None, description='题名/机构关键词')
    guideline_type: str | None = None
    domain: str | None = None
    organization: str | None = None
    status: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    missing: Literal['year', 'organization', 'title', 'domain'] | None = Field(default=None, description='只看缺失某字段的记录')
    page_num: int = 1
    page_size: int = 10


class GuidelineUpdateModel(_Camel):
    id: UUID
    title: str | None = None
    organization: str | None = None
    guideline_type: str | None = None
    publication_year: int | None = None
    domain: str | None = None
    status: str | None = None
    supersedes_id: UUID | None = None
    doi: str | None = None
    authors: list[str] | None = None
    keywords: list[str] | None = None
    abstract: str | None = None
    is_active: bool | None = None


# ---------- 推荐意见 ----------
class RecommendationModel(_Camel):
    id: UUID | None = None
    guideline_id: UUID | None = None
    guideline_title: str | None = None
    publication_year: int | None = None
    passage_id: UUID | None = None
    label: str | None = None
    text_original: str | None = None
    conditions: str | None = None
    dosage: str | None = None
    direction: str | None = None
    strength: str | None = None
    certainty: str | None = None
    grading_original: str | None = None
    study_type: str | None = None
    study_count: int | None = None
    sample_size: int | None = None
    evidence_summary: str | None = None
    safety_summary: str | None = None
    source_page: str | None = None
    source_section: str | None = None
    extraction_method: str | None = None
    verified: bool | None = None
    cited_refs: list[int] | None = None
    is_active: bool | None = None
    contexts: list[dict[str, Any]] | None = None
    references: list[dict[str, Any]] | None = None


class RecommendationPageQueryModel(_Camel):
    keyword: str | None = None
    guideline_id: UUID | None = None
    direction: str | None = None
    strength: str | None = None
    certainty: str | None = None
    verified: bool | None = None
    quote_issue: bool | None = Field(default=None, description='只看原文校验未通过')
    drug: str | None = None
    disease: str | None = None
    page_num: int = 1
    page_size: int = 10


class RecommendationUpdateModel(_Camel):
    id: UUID
    label: str | None = None
    text_original: str | None = None
    conditions: str | None = None
    dosage: str | None = None
    direction: str | None = None
    strength: str | None = None
    certainty: str | None = None
    grading_original: str | None = None
    study_type: str | None = None
    study_count: int | None = None
    sample_size: int | None = None
    evidence_summary: str | None = None
    safety_summary: str | None = None
    source_page: str | None = None
    verified: bool | None = None
    is_active: bool | None = None


class VerifyBatchModel(_Camel):
    ids: list[UUID]
    verified: bool = True


# ---------- 段落 ----------
class PassageModel(_Camel):
    id: UUID | None = None
    guideline_id: UUID | None = None
    section: str | None = None
    section_path: str | None = None
    passage_type: str | None = None
    block_type: str | None = None
    text: str | None = None
    table_html: str | None = None
    page: str | None = None
    sequence_no: int | None = None
    text_source: str | None = None
    bbox: list[float] | None = None
    verified: bool | None = None
    is_active: bool | None = None


class PassagePageQueryModel(_Camel):
    guideline_id: UUID | None = None
    keyword: str | None = None
    passage_type: str | None = None
    block_type: str | None = None
    page_num: int = 1
    page_size: int = 20


class PassageUpdateModel(_Camel):
    id: UUID
    text: str | None = None
    section_path: str | None = None
    passage_type: str | None = None
    verified: bool | None = None
    is_active: bool | None = None


# ---------- 术语 ----------
class ConceptModel(_Camel):
    id: UUID | None = None
    concept_type: str | None = None
    name: str | None = None
    synonyms: list[str] | None = None
    parent_id: UUID | None = None
    is_active: bool | None = None
    usage_count: int | None = None


class ConceptPageQueryModel(_Camel):
    keyword: str | None = None
    concept_type: str | None = None
    page_num: int = 1
    page_size: int = 10


class ConceptSaveModel(_Camel):
    id: UUID | None = None
    concept_type: str
    name: str
    synonyms: list[str] | None = None
    parent_id: UUID | None = None


class ConceptMergeModel(_Camel):
    concept_type: str
    name: str = Field(description='标准名')
    aliases: list[str] = Field(description='要归并到该标准名的原始写法')


# ---------- 公开检索 ----------
class SearchQueryModel(_Camel):
    q: str | None = None
    scope: Literal['guideline', 'recommendation', 'passage'] = 'guideline'
    guideline_type: str | None = None
    domain: str | None = None
    organization: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    strength: str | None = None
    certainty: str | None = None
    direction: str | None = None
    passage_type: str | None = None
    sort: Literal['relevance', 'year_desc', 'year_asc'] = 'relevance'
    page_num: int = 1
    page_size: int = 20


class AdvancedCondition(_Camel):
    field: Literal['title', 'organization', 'domain', 'drug', 'disease', 'syndrome', 'text', 'keyword'] = 'title'
    op: Literal['contains', 'not_contains', 'equals'] = 'contains'
    value: str
    logic: Literal['and', 'or', 'not'] = 'and'


class AdvancedQueryModel(_Camel):
    conditions: list[AdvancedCondition]
    year_from: int | None = None
    year_to: int | None = None
    guideline_type: str | None = None
    page_num: int = 1
    page_size: int = 20


class PicoQueryModel(_Camel):
    population: str | None = None
    intervention: str | None = None
    comparator: str | None = None
    outcome: str | None = None
    disease: str | None = None
    syndrome: str | None = None
    strength: str | None = None
    page_num: int = 1
    page_size: int = 20
