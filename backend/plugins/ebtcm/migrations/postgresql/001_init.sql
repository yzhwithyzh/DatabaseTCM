-- EB_TCM 指南知识库：kb schema 已由 数据库/kb_schema.sql 建好并导入数据，这里只补检索索引与辅助字段
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 中文子串检索用 trigram 索引（未装中文分词器时的关键词检索方案）
CREATE INDEX IF NOT EXISTS ix_trgm_guideline_title ON kb.guideline USING gin (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_trgm_guideline_org   ON kb.guideline USING gin (organization gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_trgm_reco_text       ON kb.recommendation USING gin (text_original gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_trgm_passage_text    ON kb.guideline_passage USING gin (text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_trgm_context_text    ON kb.recommendation_context USING gin (text_original gin_trgm_ops);
CREATE INDEX IF NOT EXISTS ix_context_type_text    ON kb.recommendation_context (context_type, text_original);
CREATE INDEX IF NOT EXISTS ix_reco_strength        ON kb.recommendation (strength, certainty);
CREATE INDEX IF NOT EXISTS ix_guideline_domain     ON kb.guideline (domain);
CREATE INDEX IF NOT EXISTS ix_guideline_type       ON kb.guideline (guideline_type);
CREATE INDEX IF NOT EXISTS ix_passage_guideline_seq ON kb.guideline_passage (guideline_id, sequence_no);

-- 指南补充元数据（作者、关键词、摘要），由后台维护或后续批处理填充
ALTER TABLE kb.guideline
  ADD COLUMN IF NOT EXISTS authors  text[],
  ADD COLUMN IF NOT EXISTS keywords text[],
  ADD COLUMN IF NOT EXISTS abstract text;
