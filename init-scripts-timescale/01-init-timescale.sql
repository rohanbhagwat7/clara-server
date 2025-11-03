-- ============================================================================
-- Clara Analytics Database Initialization Script
-- TimescaleDB Schema for Time-Series Analytics Data
-- ============================================================================

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- Analytics Events (Time-Series)
-- ============================================================================

CREATE TABLE IF NOT EXISTS analytics_events (
    event_id UUID DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,  -- query_received, response_sent, tool_called, etc.
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- User context
    user_id VARCHAR(255),
    session_id VARCHAR(255),

    -- Event data
    event_data JSONB,

    -- Metadata
    agent_version VARCHAR(50),
    client_platform VARCHAR(50),

    PRIMARY KEY (event_time, event_id)
);

-- Convert to hypertable (TimescaleDB time-series optimization)
SELECT create_hypertable('analytics_events', 'event_time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_events_user ON analytics_events(user_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_events_session ON analytics_events(session_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_events_data ON analytics_events USING gin(event_data);

-- ============================================================================
-- Tool Call Metrics (Time-Series)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_metrics (
    metric_id UUID DEFAULT gen_random_uuid(),
    metric_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Tool information
    tool_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),

    -- Performance metrics
    duration_ms DECIMAL(10,2),
    success BOOLEAN,
    error_type VARCHAR(255),
    error_message TEXT,

    -- Tool-specific data
    tool_parameters JSONB,
    tool_result_size INTEGER,

    PRIMARY KEY (metric_time, metric_id)
);

-- Convert to hypertable
SELECT create_hypertable('tool_metrics', 'metric_time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_metrics(tool_name, metric_time DESC);
CREATE INDEX IF NOT EXISTS idx_tool_success ON tool_metrics(success, metric_time DESC);
CREATE INDEX IF NOT EXISTS idx_tool_user ON tool_metrics(user_id, metric_time DESC);

-- ============================================================================
-- Interaction Metrics (Time-Series)
-- ============================================================================

CREATE TABLE IF NOT EXISTS interaction_metrics (
    interaction_id UUID DEFAULT gen_random_uuid(),
    interaction_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- User context
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),

    -- Query information
    query TEXT,
    query_type VARCHAR(100),  -- equipment_spec, nfpa_search, manual_lookup, etc.

    -- Response information
    response_length INTEGER,
    response_time_ms DECIMAL(10,2),

    -- Tools used
    tools_called JSONB,  -- Array of tool names
    tools_count INTEGER,

    -- Success signals
    immediate_success BOOLEAN,
    implicit_success BOOLEAN,
    explicit_feedback DECIMAL(3,2),  -- 1.0 to 5.0 rating

    PRIMARY KEY (interaction_time, interaction_id)
);

-- Convert to hypertable
SELECT create_hypertable('interaction_metrics', 'interaction_time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_interaction_user ON interaction_metrics(user_id, interaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_type ON interaction_metrics(query_type, interaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_success ON interaction_metrics(immediate_success, interaction_time DESC);

-- ============================================================================
-- User Actions (Time-Series)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_actions (
    action_id UUID DEFAULT gen_random_uuid(),
    action_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- User and job context
    user_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255),

    -- Action details
    action_type VARCHAR(100) NOT NULL,  -- get_spec, check_amp_draw, view_manual, etc.
    equipment_type VARCHAR(255),
    equipment_model VARCHAR(255),

    -- Action parameters
    action_parameters JSONB,

    -- Result
    action_success BOOLEAN,
    action_duration_ms DECIMAL(10,2),

    PRIMARY KEY (action_time, action_id)
);

-- Convert to hypertable
SELECT create_hypertable('user_actions', 'action_time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_action_user ON user_actions(user_id, action_time DESC);
CREATE INDEX IF NOT EXISTS idx_action_type ON user_actions(action_type, action_time DESC);
CREATE INDEX IF NOT EXISTS idx_action_equipment ON user_actions(equipment_type, action_time DESC);

-- ============================================================================
-- Continuous Aggregates (Pre-computed Analytics)
-- ============================================================================

-- Hourly tool performance aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS tool_performance_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', metric_time) AS hour,
    tool_name,
    COUNT(*) as call_count,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) as p50_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100 as success_rate_percent
FROM tool_metrics
GROUP BY hour, tool_name;

-- Add refresh policy (automatically update every hour)
SELECT add_continuous_aggregate_policy('tool_performance_hourly',
    start_offset => INTERVAL '1 week',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Daily user activity aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', interaction_time) AS day,
    user_id,
    COUNT(*) as interaction_count,
    AVG(response_time_ms) as avg_response_time_ms,
    SUM(CASE WHEN immediate_success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100 as success_rate_percent,
    AVG(tools_count) as avg_tools_per_interaction
FROM interaction_metrics
GROUP BY day, user_id;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('user_activity_daily',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Hourly query type distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS query_type_distribution_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', interaction_time) AS hour,
    query_type,
    COUNT(*) as query_count,
    AVG(response_time_ms) as avg_response_time_ms
FROM interaction_metrics
WHERE query_type IS NOT NULL
GROUP BY hour, query_type;

SELECT add_continuous_aggregate_policy('query_type_distribution_hourly',
    start_offset => INTERVAL '1 week',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- Retention Policies (Automatic Data Cleanup)
-- ============================================================================

-- Keep raw events for 90 days
SELECT add_retention_policy('analytics_events', INTERVAL '90 days', if_not_exists => TRUE);

-- Keep raw tool metrics for 90 days
SELECT add_retention_policy('tool_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Keep raw interaction metrics for 180 days (longer for analysis)
SELECT add_retention_policy('interaction_metrics', INTERVAL '180 days', if_not_exists => TRUE);

-- Keep raw user actions for 90 days
SELECT add_retention_policy('user_actions', INTERVAL '90 days', if_not_exists => TRUE);

-- Note: Aggregated views are kept indefinitely (they're much smaller)

-- ============================================================================
-- Compression Policies (Reduce Storage)
-- ============================================================================

-- Compress events older than 7 days
SELECT add_compression_policy('analytics_events', INTERVAL '7 days', if_not_exists => TRUE);

-- Compress tool metrics older than 7 days
SELECT add_compression_policy('tool_metrics', INTERVAL '7 days', if_not_exists => TRUE);

-- Compress interactions older than 7 days
SELECT add_compression_policy('interaction_metrics', INTERVAL '7 days', if_not_exists => TRUE);

-- Compress user actions older than 7 days
SELECT add_compression_policy('user_actions', INTERVAL '7 days', if_not_exists => TRUE);

-- ============================================================================
-- Useful Analytics Queries
-- ============================================================================

-- Create view for recent tool performance
CREATE OR REPLACE VIEW recent_tool_performance AS
SELECT
    tool_name,
    COUNT(*) as calls_24h,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100 as success_rate_percent
FROM tool_metrics
WHERE metric_time > NOW() - INTERVAL '24 hours'
GROUP BY tool_name
ORDER BY calls_24h DESC;

-- Create view for user engagement
CREATE OR REPLACE VIEW user_engagement_7d AS
SELECT
    user_id,
    COUNT(DISTINCT DATE(interaction_time)) as active_days,
    COUNT(*) as total_interactions,
    AVG(response_time_ms) as avg_response_time,
    SUM(CASE WHEN immediate_success THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) * 100 as success_rate
FROM interaction_metrics
WHERE interaction_time > NOW() - INTERVAL '7 days'
GROUP BY user_id
ORDER BY total_interactions DESC;

-- Create view for error patterns
CREATE OR REPLACE VIEW error_patterns_24h AS
SELECT
    tool_name,
    error_type,
    COUNT(*) as error_count,
    array_agg(DISTINCT error_message) as error_messages
FROM tool_metrics
WHERE NOT success
  AND metric_time > NOW() - INTERVAL '24 hours'
GROUP BY tool_name, error_type
ORDER BY error_count DESC;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO clara;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO clara;

-- ============================================================================
-- Schema Complete
-- ============================================================================

-- Insert sample event for testing
INSERT INTO analytics_events (event_type, user_id, session_id, event_data)
VALUES (
    'system_initialized',
    'system',
    'init',
    '{"message": "TimescaleDB analytics schema initialized", "version": "1.0"}'::jsonb
);
