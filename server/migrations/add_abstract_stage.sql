-- Migration: Add Abstract Review Stage
-- This enables a second review pass on paper abstracts

-- Add stage column to all decision tables
ALTER TABLE swipe_decisions ADD COLUMN IF NOT EXISTS stage VARCHAR(10) DEFAULT 'title';
ALTER TABLE moderator_decisions ADD COLUMN IF NOT EXISTS stage VARCHAR(10) DEFAULT 'title';
ALTER TABLE systems_decisions ADD COLUMN IF NOT EXISTS stage VARCHAR(10) DEFAULT 'title';

-- Add stage column to user progress
ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS stage VARCHAR(10) DEFAULT 'title';

-- Create unique constraint for stage-specific decisions
DROP INDEX IF EXISTS idx_swipe_user_paper;
CREATE UNIQUE INDEX idx_swipe_user_paper_stage ON swipe_decisions(user_id, paper_id, stage);

DROP INDEX IF EXISTS idx_moderator_paper;
CREATE UNIQUE INDEX idx_moderator_paper_stage ON moderator_decisions(paper_id, stage);

-- Table to track which papers are eligible for abstract review
CREATE TABLE IF NOT EXISTS abstract_eligible_papers (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    source VARCHAR(20) NOT NULL CHECK (source IN ('reviewer_consensus', 'moderator_keep', 'systems_keep')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paper_id)
);

-- Create index for abstract eligible papers
CREATE INDEX IF NOT EXISTS idx_abstract_eligible ON abstract_eligible_papers(paper_id);

-- Function to populate abstract eligible papers from title stage results
-- Run this manually after title stage is complete:
-- INSERT INTO abstract_eligible_papers (paper_id, source)
-- SELECT DISTINCT p.id, 'reviewer_consensus'
-- FROM papers p
-- WHERE (
--     SELECT COUNT(*)
--     FROM swipe_decisions sd
--     WHERE sd.paper_id = p.id
--     AND sd.decision = 'keep'
--     AND sd.stage = 'title'
--     AND NOT EXISTS (
--         SELECT 1 FROM flagged_papers fp WHERE fp.paper_id = p.id
--     )
-- ) = 2
-- UNION
-- SELECT DISTINCT md.paper_id, 'moderator_keep'
-- FROM moderator_decisions md
-- WHERE md.decision = 'keep'
-- AND md.stage = 'title'
-- UNION
-- SELECT DISTINCT fp.paper_id, 'systems_keep'
-- FROM flagged_papers fp
-- JOIN systems_decisions sd ON sd.flagged_paper_id = fp.id
-- WHERE sd.decision = 'keep'
-- ON CONFLICT (paper_id) DO NOTHING;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_swipe_stage ON swipe_decisions(stage);
CREATE INDEX IF NOT EXISTS idx_moderator_stage ON moderator_decisions(stage);
CREATE INDEX IF NOT EXISTS idx_systems_stage ON systems_decisions(stage);
CREATE INDEX IF NOT EXISTS idx_progress_stage ON user_progress(user_id, stage);
