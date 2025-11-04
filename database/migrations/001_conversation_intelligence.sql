-- Migration: Conversation Intelligence Platform
-- Description: Add tables for Rilla-like conversation recording, transcription, and AI insights
-- Date: 2025-11-04

-- ============================================
-- PART 1: USER AUTHENTICATION & MANAGEMENT
-- ============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('technician', 'supervisor', 'admin')),
    google_id VARCHAR(255) UNIQUE,
    profile_picture_url TEXT,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Teams/Organizations
CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

-- User-Team relationship
CREATE TABLE IF NOT EXISTS team_members (
    team_id VARCHAR(50) REFERENCES teams(team_id) ON DELETE CASCADE,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('member', 'supervisor', 'admin')),
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id)
);

-- Supervisor-Technician relationships
CREATE TABLE IF NOT EXISTS supervisor_assignments (
    supervisor_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    technician_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (supervisor_id, technician_id)
);

-- Session tokens
CREATE TABLE IF NOT EXISTS auth_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    device_info JSONB
);

-- ============================================
-- PART 2: CONVERSATION RECORDING
-- ============================================

-- Conversations/Calls
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    technician_id VARCHAR(50) REFERENCES users(user_id),
    job_id VARCHAR(50) REFERENCES jobs(job_id),
    customer_name VARCHAR(255),
    customer_phone VARCHAR(50),

    -- Recording metadata
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    recording_url TEXT,
    recording_file_size BIGINT,

    -- Context
    location_address TEXT,
    equipment_discussed JSONB DEFAULT '[]'::jsonb,
    job_context JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'processing', 'analyzed')),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Real-time transcription segments
CREATE TABLE IF NOT EXISTS transcription_segments (
    segment_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Speaker info
    speaker_type VARCHAR(50) NOT NULL CHECK (speaker_type IN ('technician', 'customer', 'unknown')),
    speaker_id VARCHAR(50) REFERENCES users(user_id),

    -- Transcription
    text TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    confidence FLOAT,

    -- Metadata
    is_final BOOLEAN DEFAULT false,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_transcription_conversation ON transcription_segments(conversation_id);
CREATE INDEX IF NOT EXISTS idx_transcription_time ON transcription_segments(conversation_id, start_time);
CREATE INDEX IF NOT EXISTS idx_conversation_technician ON conversations(technician_id);
CREATE INDEX IF NOT EXISTS idx_conversation_job ON conversations(job_id);
CREATE INDEX IF NOT EXISTS idx_conversation_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversation_started ON conversations(started_at DESC);

-- ============================================
-- PART 3: AI INSIGHTS & ANALYSIS
-- ============================================

-- AI Insights per conversation
CREATE TABLE IF NOT EXISTS conversation_insights (
    insight_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Summary
    summary TEXT,
    key_topics JSONB DEFAULT '[]'::jsonb,

    -- Sentiment Analysis
    overall_sentiment VARCHAR(50) CHECK (overall_sentiment IN ('positive', 'neutral', 'negative')),
    sentiment_scores JSONB,
    customer_satisfaction_score FLOAT CHECK (customer_satisfaction_score >= 0 AND customer_satisfaction_score <= 100),

    -- Keywords & Phrases
    positive_keywords JSONB DEFAULT '[]'::jsonb,
    improvement_keywords JSONB DEFAULT '[]'::jsonb,
    technical_terms JSONB DEFAULT '[]'::jsonb,

    -- Action Items
    action_items JSONB DEFAULT '[]'::jsonb,
    follow_ups JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    analyzed_at TIMESTAMP DEFAULT NOW(),
    analysis_model VARCHAR(100)
);

-- Upsell Opportunities
CREATE TABLE IF NOT EXISTS upsell_opportunities (
    opportunity_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Opportunity details
    opportunity_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,

    -- Detected from conversation
    trigger_phrase TEXT,
    timestamp_in_call FLOAT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),

    -- Business value
    estimated_value DECIMAL(10, 2),
    priority VARCHAR(50) CHECK (priority IN ('high', 'medium', 'low')),

    -- Status
    status VARCHAR(50) DEFAULT 'identified' CHECK (status IN ('identified', 'pitched', 'closed_won', 'closed_lost', 'dismissed')),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Coaching Moments (areas for improvement)
CREATE TABLE IF NOT EXISTS coaching_moments (
    moment_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Moment details
    category VARCHAR(100),
    title VARCHAR(255),
    description TEXT,

    -- Location in conversation
    timestamp_in_call FLOAT,
    transcript_excerpt TEXT,

    -- Feedback
    what_happened TEXT,
    what_should_happen TEXT,
    example_better_response TEXT,

    -- Severity
    severity VARCHAR(50) CHECK (severity IN ('critical', 'important', 'minor')),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for insights
CREATE INDEX IF NOT EXISTS idx_insights_conversation ON conversation_insights(conversation_id);
CREATE INDEX IF NOT EXISTS idx_upsell_conversation ON upsell_opportunities(conversation_id);
CREATE INDEX IF NOT EXISTS idx_upsell_status ON upsell_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_coaching_conversation ON coaching_moments(conversation_id);
CREATE INDEX IF NOT EXISTS idx_coaching_severity ON coaching_moments(severity);

-- ============================================
-- PART 4: LIVE AI NUDGING
-- ============================================

-- Live AI nudges during calls
CREATE TABLE IF NOT EXISTS live_nudges (
    nudge_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,

    -- Nudge content
    type VARCHAR(50) CHECK (type IN ('upsell_prompt', 'objection_handler', 'next_question', 'warning', 'technical_help', 'compliance_reminder')),
    title VARCHAR(255),
    message TEXT,
    suggested_response TEXT,

    -- Trigger
    triggered_by_phrase TEXT,
    triggered_at FLOAT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),

    -- Action
    was_displayed BOOLEAN DEFAULT true,
    was_dismissed BOOLEAN DEFAULT false,
    was_acted_upon BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nudges_conversation ON live_nudges(conversation_id);
CREATE INDEX IF NOT EXISTS idx_nudges_type ON live_nudges(type);

-- ============================================
-- PART 5: ANALYTICS & PERFORMANCE METRICS
-- ============================================

-- Daily technician performance metrics
CREATE TABLE IF NOT EXISTS daily_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    technician_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    date DATE NOT NULL,

    -- Call volume
    total_calls INTEGER DEFAULT 0,
    avg_call_duration INTEGER,

    -- Conversion metrics
    upsells_identified INTEGER DEFAULT 0,
    upsells_pitched INTEGER DEFAULT 0,
    upsells_closed INTEGER DEFAULT 0,
    upsell_conversion_rate FLOAT,
    upsell_revenue DECIMAL(10, 2) DEFAULT 0,

    -- Quality metrics
    avg_customer_satisfaction FLOAT,
    positive_keyword_count INTEGER DEFAULT 0,
    coaching_moments_count INTEGER DEFAULT 0,

    -- Behavioral metrics
    avg_rapport_score FLOAT,
    avg_technical_explanation_score FLOAT,
    avg_objection_handling_score FLOAT,

    -- Live coaching
    nudges_received INTEGER DEFAULT 0,
    nudges_acted_upon INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(technician_id, date)
);

-- Leaderboard rankings
CREATE TABLE IF NOT EXISTS leaderboard_rankings (
    ranking_id SERIAL PRIMARY KEY,
    period_type VARCHAR(50) CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    period_start DATE,
    period_end DATE,

    -- Rankings (array of {user_id, rank, score, metrics})
    rankings JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_technician_date ON daily_performance_metrics(technician_id, date);
CREATE INDEX IF NOT EXISTS idx_leaderboard_period ON leaderboard_rankings(period_type, period_start, period_end);

-- ============================================
-- PART 6: SUPERVISOR FEEDBACK
-- ============================================

-- Supervisor feedback on calls
CREATE TABLE IF NOT EXISTS supervisor_feedback (
    feedback_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(50) REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    supervisor_id VARCHAR(50) REFERENCES users(user_id),
    technician_id VARCHAR(50) REFERENCES users(user_id),

    -- Ratings (0-5 scale)
    overall_rating INTEGER CHECK (overall_rating >= 0 AND overall_rating <= 5),
    rapport_rating INTEGER CHECK (rapport_rating >= 0 AND rapport_rating <= 5),
    technical_rating INTEGER CHECK (technical_rating >= 0 AND technical_rating <= 5),
    upsell_rating INTEGER CHECK (upsell_rating >= 0 AND upsell_rating <= 5),

    -- Feedback text
    strengths TEXT,
    areas_for_improvement TEXT,
    private_notes TEXT,

    -- Flags
    is_training_example BOOLEAN DEFAULT false,
    is_flagged BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON supervisor_feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_technician ON supervisor_feedback(technician_id);

-- ============================================
-- PART 7: UPDATE EXISTING TABLES
-- ============================================

-- Add user_id to existing jobs table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='jobs' AND column_name='assigned_user_id') THEN
        ALTER TABLE jobs ADD COLUMN assigned_user_id VARCHAR(50) REFERENCES users(user_id);
        CREATE INDEX idx_jobs_user ON jobs(assigned_user_id);
    END IF;
END $$;

-- ============================================
-- PART 8: HELPER FUNCTIONS
-- ============================================

-- Function to calculate daily metrics
CREATE OR REPLACE FUNCTION calculate_daily_metrics(tech_id VARCHAR, metric_date DATE)
RETURNS void AS $$
BEGIN
    INSERT INTO daily_performance_metrics (
        technician_id,
        date,
        total_calls,
        avg_call_duration,
        upsells_identified,
        upsells_closed,
        avg_customer_satisfaction,
        coaching_moments_count
    )
    SELECT
        tech_id,
        metric_date,
        COUNT(DISTINCT c.conversation_id),
        AVG(c.duration_seconds)::INTEGER,
        COUNT(DISTINCT uo.opportunity_id) FILTER (WHERE uo.status IN ('identified', 'pitched', 'closed_won', 'closed_lost')),
        COUNT(DISTINCT uo.opportunity_id) FILTER (WHERE uo.status = 'closed_won'),
        AVG(ci.customer_satisfaction_score),
        COUNT(DISTINCT cm.moment_id)
    FROM conversations c
    LEFT JOIN conversation_insights ci ON c.conversation_id = ci.conversation_id
    LEFT JOIN upsell_opportunities uo ON c.conversation_id = uo.conversation_id
    LEFT JOIN coaching_moments cm ON c.conversation_id = cm.conversation_id
    WHERE c.technician_id = tech_id
      AND DATE(c.started_at) = metric_date
      AND c.status = 'analyzed'
    ON CONFLICT (technician_id, date)
    DO UPDATE SET
        total_calls = EXCLUDED.total_calls,
        avg_call_duration = EXCLUDED.avg_call_duration,
        upsells_identified = EXCLUDED.upsells_identified,
        upsells_closed = EXCLUDED.upsells_closed,
        avg_customer_satisfaction = EXCLUDED.avg_customer_satisfaction,
        coaching_moments_count = EXCLUDED.coaching_moments_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update conversation status
CREATE OR REPLACE FUNCTION update_conversation_status()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER conversation_update_timestamp
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_status();

-- ============================================
-- PART 9: INITIAL DATA (OPTIONAL)
-- ============================================

-- Create default admin user (update with real credentials after Google SSO setup)
-- INSERT INTO users (user_id, email, full_name, role, is_active)
-- VALUES ('ADMIN-001', 'admin@clarahvac.com', 'System Admin', 'admin', true)
-- ON CONFLICT (user_id) DO NOTHING;

-- Create default team
-- INSERT INTO teams (team_id, name)
-- VALUES ('TEAM-001', 'Main Team')
-- ON CONFLICT (team_id) DO NOTHING;

COMMENT ON TABLE users IS 'User accounts with roles (technician, supervisor, admin)';
COMMENT ON TABLE conversations IS 'Recorded technician-customer conversations';
COMMENT ON TABLE transcription_segments IS 'Real-time transcription segments with speaker diarization';
COMMENT ON TABLE conversation_insights IS 'AI-generated insights from analyzed conversations';
COMMENT ON TABLE upsell_opportunities IS 'Detected upsell opportunities from conversations';
COMMENT ON TABLE coaching_moments IS 'Coaching feedback points identified by AI';
COMMENT ON TABLE live_nudges IS 'Real-time AI nudges sent during live calls';
COMMENT ON TABLE daily_performance_metrics IS 'Aggregated daily performance metrics per technician';
COMMENT ON TABLE supervisor_feedback IS 'Manual feedback from supervisors on calls';
