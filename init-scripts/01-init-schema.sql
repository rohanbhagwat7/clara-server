-- ============================================================================
-- Clara Database Initialization Script
-- PostgreSQL Schema for User Preferences, Cache, and General Data
-- ============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================================================
-- User Preferences Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    skill_level VARCHAR(50) DEFAULT 'intermediate',  -- beginner, intermediate, expert
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES user_profiles(user_id) ON DELETE CASCADE,

    -- Voice preferences
    voice_mic_sensitivity VARCHAR(50) DEFAULT 'medium',
    voice_push_to_talk BOOLEAN DEFAULT false,
    voice_echo_cancellation BOOLEAN DEFAULT true,

    -- Notification preferences
    notification_daily_brief_time TIME DEFAULT '08:00:00',
    notification_proximity_distance_meters INTEGER DEFAULT 500,
    notification_nudge_priority VARCHAR(50) DEFAULT 'all',

    -- Display preferences
    display_theme VARCHAR(50) DEFAULT 'auto',
    display_text_size VARCHAR(50) DEFAULT 'medium',
    display_high_contrast BOOLEAN DEFAULT false,

    -- Response style preferences
    response_max_words INTEGER DEFAULT 100,
    response_include_explanations BOOLEAN DEFAULT true,
    response_jargon_level VARCHAR(50) DEFAULT 'medium',
    response_step_by_step BOOLEAN DEFAULT true,

    -- Equipment specialties
    equipment_specialties JSONB DEFAULT '[]'::jsonb,
    certifications JSONB DEFAULT '[]'::jsonb,

    -- Custom shortcuts
    custom_shortcuts JSONB DEFAULT '{}'::jsonb,
    favorite_tools JSONB DEFAULT '[]'::jsonb,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Cache Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS response_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    cache_type VARCHAR(100),  -- nfpa_search, manual_lookup, spec_query, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_expires ON response_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_type ON response_cache(cache_type);

-- ============================================================================
-- CRM Tables (if replacing mock CRM)
-- ============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company_type VARCHAR(50),  -- commercial, residential, industrial
    location TEXT,

    -- Contact information
    primary_contact VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),

    -- Business details
    industry VARCHAR(255),
    building_type VARCHAR(255),
    square_footage INTEGER,

    -- Relationship
    customer_since DATE,
    lifetime_value DECIMAL(15,2) DEFAULT 0,
    annual_spend DECIMAL(15,2) DEFAULT 0,

    -- Preferences
    special_requirements JSONB DEFAULT '[]'::jsonb,
    preferred_service_times JSONB DEFAULT '[]'::jsonb,
    notes TEXT,

    -- Equipment
    total_equipment_count INTEGER DEFAULT 0,
    equipment_types JSONB DEFAULT '[]'::jsonb,

    -- Service history
    total_service_calls INTEGER DEFAULT 0,
    last_service_date DATE,
    satisfaction_score DECIMAL(3,2) DEFAULT 4.5,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contracts (
    contract_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255) REFERENCES customers(customer_id) ON DELETE CASCADE,
    contract_type VARCHAR(100),  -- monthly_inspection, comprehensive, etc.
    status VARCHAR(50),  -- active, expiring_soon, expired

    -- Dates
    start_date DATE,
    end_date DATE,
    next_service_date DATE,

    -- Coverage
    covered_equipment JSONB DEFAULT '[]'::jsonb,
    service_frequency VARCHAR(50),
    included_services JSONB DEFAULT '[]'::jsonb,

    -- Financial
    annual_value DECIMAL(15,2),
    payment_status VARCHAR(50) DEFAULT 'current',

    -- Performance
    services_completed INTEGER DEFAULT 0,
    services_scheduled INTEGER DEFAULT 0,
    compliance_rate DECIMAL(5,2) DEFAULT 100.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);

CREATE TABLE IF NOT EXISTS sales_opportunities (
    opportunity_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255) REFERENCES customers(customer_id) ON DELETE CASCADE,
    opportunity_type VARCHAR(100),  -- upgrade, replacement, new_equipment, contract_renewal

    -- Details
    title VARCHAR(255),
    description TEXT,
    estimated_value DECIMAL(15,2),
    confidence DECIMAL(3,2),  -- 0.0 to 1.0

    -- Equipment related
    equipment_model VARCHAR(255),
    equipment_age INTEGER,
    current_issue TEXT,

    -- Timing
    identified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(50) DEFAULT 'medium',
    expected_close_date DATE,

    -- Context
    trigger TEXT,
    next_steps JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_opportunities_customer ON sales_opportunities(customer_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_priority ON sales_opportunities(priority);

-- ============================================================================
-- Pattern Learning Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS action_sequences (
    sequence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    job_id VARCHAR(255),
    equipment_type VARCHAR(255),

    actions JSONB NOT NULL,  -- Array of actions with timestamps

    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    success BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sequences_user ON action_sequences(user_id);
CREATE INDEX IF NOT EXISTS idx_sequences_equipment ON action_sequences(equipment_type);

CREATE TABLE IF NOT EXISTS equipment_measurements (
    measurement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_model VARCHAR(255) NOT NULL,
    parameter VARCHAR(255) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(50),

    measured_by VARCHAR(255),
    job_id VARCHAR(255),

    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_measurements_model ON equipment_measurements(equipment_model);
CREATE INDEX IF NOT EXISTS idx_measurements_parameter ON equipment_measurements(parameter);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_prefs_skill ON user_preferences(response_jargon_level);
CREATE INDEX IF NOT EXISTS idx_customers_location ON customers USING gin(to_tsvector('english', location));
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers USING gin(to_tsvector('english', name));

-- ============================================================================
-- Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON sales_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data (Optional - for testing)
-- ============================================================================

-- Insert a test user
INSERT INTO user_profiles (user_id, name, email, skill_level)
VALUES ('test_user_001', 'Test Technician', 'test@clara.local', 'intermediate')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_preferences (user_id)
VALUES ('test_user_001')
ON CONFLICT (user_id) DO NOTHING;

-- Cleanup function for expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM response_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clara;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO clara;

-- ============================================================================
-- Schema Complete
-- ============================================================================
