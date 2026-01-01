-- Complete Paper Filter Database Setup
-- Run this on a fresh database

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(20) NOT NULL CHECK (role IN ('reviewer', 'moderator', 'systems', 'supervisor', 'admin')),
    invite_code VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Papers table
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    abstract TEXT,
    doi VARCHAR(255),
    source VARCHAR(100),
    nlp_confidence VARCHAR(20),
    nlp_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Swipe decisions table (reviewer decisions)
CREATE TABLE IF NOT EXISTS swipe_decisions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'reject')),
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, paper_id)
);

-- User progress table
CREATE TABLE IF NOT EXISTS user_progress (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_paper_index INTEGER DEFAULT 0,
    total_kept INTEGER DEFAULT 0,
    total_rejected INTEGER DEFAULT 0,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flagged papers table
CREATE TABLE IF NOT EXISTS flagged_papers (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    flagged_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'approved', 'rejected')),
    UNIQUE(paper_id, flagged_by)
);

-- Moderator decisions table
CREATE TABLE IF NOT EXISTS moderator_decisions (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'reject')),
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(paper_id)
);

-- Systems decisions table
CREATE TABLE IF NOT EXISTS systems_decisions (
    id SERIAL PRIMARY KEY,
    flagged_paper_id INTEGER REFERENCES flagged_papers(id) ON DELETE CASCADE,
    decision VARCHAR(10) NOT NULL CHECK (decision IN ('keep', 'reject')),
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(flagged_paper_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_swipe_user ON swipe_decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_swipe_paper ON swipe_decisions(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_title ON papers(title);
CREATE INDEX IF NOT EXISTS idx_flagged_papers ON flagged_papers(paper_id);
CREATE INDEX IF NOT EXISTS idx_flagged_status ON flagged_papers(status);
CREATE INDEX IF NOT EXISTS idx_moderator_decisions ON moderator_decisions(paper_id);
CREATE INDEX IF NOT EXISTS idx_systems_decisions ON systems_decisions(flagged_paper_id);
