"""
EB_TCM 指南知识库 ORM 映射（对应 kb schema，表由 数据库/kb_schema.sql 建立）
"""
import uuid

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import REAL, UUID

from config.database import Base

SCHEMA = 'kb'


class Guideline(Base):
    __tablename__ = 'guideline'
    __table_args__ = {'schema': SCHEMA, 'comment': '指南/共识'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    title = Column(String(300), nullable=False)
    citation = Column(Text, nullable=False)
    organization = Column(String(300))
    guideline_type = Column(String(20), nullable=False)      # enum kb.guideline_type_enum
    publication_year = Column(SmallInteger, nullable=False)
    domain = Column(String(100))
    status = Column(String(20), nullable=False, default='current')
    supersedes_id = Column(UUID(as_uuid=True))
    doi = Column(String(200))
    source_file = Column(Text)
    authors = Column(ARRAY(Text))
    keywords = Column(ARRAY(Text))
    abstract = Column(Text)


class GuidelinePassage(Base):
    __tablename__ = 'guideline_passage'
    __table_args__ = {'schema': SCHEMA, 'comment': '正文段落'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    guideline_id = Column(UUID(as_uuid=True), nullable=False)
    section = Column(String(200), nullable=False)
    passage_type = Column(String(20), nullable=False, default='other')
    text = Column(Text, nullable=False)
    page = Column(String(30), nullable=False)
    sequence_no = Column(Integer, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
    block_type = Column(String(20))
    section_path = Column(Text)
    bbox = Column(ARRAY(REAL))
    text_source = Column(String(20))
    table_html = Column(Text)
    parse_model = Column(String(40))


class Recommendation(Base):
    __tablename__ = 'recommendation'
    __table_args__ = {'schema': SCHEMA, 'comment': '推荐意见'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    guideline_id = Column(UUID(as_uuid=True), nullable=False)
    passage_id = Column(UUID(as_uuid=True))
    label = Column(String(50))
    text_original = Column(Text, nullable=False)
    conditions = Column(Text)
    dosage = Column(Text)
    direction = Column(String(20), nullable=False)
    strength = Column(String(20), nullable=False, default='not_reported')
    certainty = Column(String(20), nullable=False, default='not_reported')
    grading_original = Column(String(200))
    study_type = Column(String(50))
    study_count = Column(SmallInteger)
    sample_size = Column(Integer)
    evidence_summary = Column(Text)
    safety_summary = Column(Text)
    source_page = Column(String(30), nullable=False)
    source_section = Column(String(200))
    extraction_method = Column(String(20), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)
    cited_refs = Column(ARRAY(SmallInteger))


class RecommendationContext(Base):
    __tablename__ = 'recommendation_context'
    __table_args__ = {'schema': SCHEMA, 'comment': '推荐语境'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    recommendation_id = Column(UUID(as_uuid=True), nullable=False)
    context_type = Column(String(20), nullable=False)
    text_original = Column(String(300), nullable=False)
    concept_id = Column(UUID(as_uuid=True))
    role = Column(String(30))


class Concept(Base):
    __tablename__ = 'concept'
    __table_args__ = {'schema': SCHEMA, 'comment': '标准术语'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    concept_type = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    synonyms = Column(ARRAY(Text))
    parent_id = Column(UUID(as_uuid=True))


class Reference(Base):
    __tablename__ = 'reference'
    __table_args__ = {'schema': SCHEMA, 'comment': '参考文献'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    guideline_id = Column(UUID(as_uuid=True), nullable=False)
    ref_number = Column(SmallInteger, nullable=False)
    citation_text = Column(Text, nullable=False)
    ref_type = Column(String(30))
    doi = Column(String(200))
    pmid = Column(String(30))


class RecommendationReference(Base):
    __tablename__ = 'recommendation_reference'
    __table_args__ = {'schema': SCHEMA, 'comment': '推荐-文献关联'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created = Column(DateTime(timezone=True), server_default=func.now())
    recommendation_id = Column(UUID(as_uuid=True), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(20))
