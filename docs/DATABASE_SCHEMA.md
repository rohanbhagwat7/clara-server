# Clara Backend - PostgreSQL Database Schema

## Overview

This document defines the production PostgreSQL database schema for Clara Backend,
replacing the current demo data approach with a scalable, production-ready database.

**Status:** Design Complete - Ready for Implementation
**Database:** PostgreSQL 14+
**ORM:** SQLAlchemy (Python) / Prisma (TypeScript)

---

## Schema Design Principles

1. **Normalization:** 3NF for data integrity
2. **Indexing:** Strategic indexes for fast lookups
3. **Audit Trail:** Created/updated timestamps on all tables
4. **Soft Deletes:** Use `deleted_at` instead of hard deletes
5. **JSON Fields:** Use JSONB for flexible schema (specifications, metadata)
6. **Foreign Keys:** Enforce referential integrity
7. **Partitioning:** Time-based partitioning for large tables (inspection_records)

---

## Core Tables

### 1. `manufacturers`

Stores manufacturer/brand information.

```sql
CREATE TABLE manufacturers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    website VARCHAR(500),
    support_phone VARCHAR(50),
    support_email VARCHAR(255),
    headquarters_location VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_manufacturers_name ON manufacturers(name);
CREATE INDEX idx_manufacturers_deleted ON manufacturers(deleted_at) WHERE deleted_at IS NULL;
```

**Sample Data:**
```sql
INSERT INTO manufacturers (name, website) VALUES
    ('Carrier', 'https://www.carrier.com'),
    ('Daikin', 'https://www.daikin.com'),
    ('Peerless Pump', 'https://www.peerlesspump.com');
```

---

### 2. `equipment_models`

Stores equipment model information with specifications.

```sql
CREATE TYPE equipment_category AS ENUM (
    'fire_pump',
    'backflow_preventer',
    'sprinkler_head',
    'fire_extinguisher',
    'fire_alarm_panel',
    'smoke_detector',
    'hvac',
    'standpipe',
    'other'
);

CREATE TABLE equipment_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manufacturer_id UUID NOT NULL REFERENCES manufacturers(id),
    model_number VARCHAR(255) NOT NULL,
    product_name VARCHAR(500),
    equipment_category equipment_category NOT NULL,

    -- Specifications stored as JSONB for flexibility
    electrical_specs JSONB DEFAULT '{}',
    pressure_specs JSONB DEFAULT '{}',
    temperature_specs JSONB DEFAULT '{}',
    flow_specs JSONB DEFAULT '{}',
    physical_specs JSONB DEFAULT '{}',

    -- Additional information
    year_introduced INTEGER,
    year_discontinued INTEGER,
    replacement_model_id UUID REFERENCES equipment_models(id),
    maintenance_notes TEXT,
    data_source VARCHAR(500),
    confidence_score FLOAT DEFAULT 1.0,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,

    UNIQUE(manufacturer_id, model_number)
);

CREATE INDEX idx_equipment_models_manufacturer ON equipment_models(manufacturer_id);
CREATE INDEX idx_equipment_models_model_number ON equipment_models(model_number);
CREATE INDEX idx_equipment_models_category ON equipment_models(equipment_category);
CREATE INDEX idx_equipment_models_deleted ON equipment_models(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_equipment_models_electrical_specs ON equipment_models USING GIN (electrical_specs);
```

**JSONB Structure Examples:**

```json
// electrical_specs
{
    "amp_draw_nominal": 17.8,
    "amp_draw_min": 15.0,
    "amp_draw_max": 20.0,
    "voltage": 208.0,
    "phase": 1,
    "frequency": 60,
    "capacitor_microfarads": 55.0,
    "power_watts": 3000
}

// physical_specs
{
    "filter_size": "16x25x4",
    "belt_size": "4L340",
    "weight_lbs": 205.0,
    "dimensions": "24x18x12",
    "thread_size": "1/2 NPT"
}
```

---

### 3. `common_problems`

Stores common problems/failures for equipment models.

```sql
CREATE TYPE problem_severity AS ENUM ('critical', 'high', 'medium', 'low');
CREATE TYPE problem_frequency AS ENUM ('very_common', 'common', 'occasional', 'rare');

CREATE TABLE common_problems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_model_id UUID NOT NULL REFERENCES equipment_models(id),
    problem_description TEXT NOT NULL,
    symptoms JSONB DEFAULT '[]',  -- Array of symptom strings
    root_cause TEXT,
    solution TEXT,
    severity problem_severity NOT NULL,
    frequency problem_frequency NOT NULL,
    typical_age_range VARCHAR(50),
    related_parts JSONB DEFAULT '[]',  -- Array of part names
    estimated_repair_cost VARCHAR(50),
    data_sources JSONB DEFAULT '[]',  -- Array of source URLs/names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_common_problems_equipment ON common_problems(equipment_model_id);
CREATE INDEX idx_common_problems_severity ON common_problems(severity);
CREATE INDEX idx_common_problems_frequency ON common_problems(frequency);
CREATE INDEX idx_common_problems_symptoms ON common_problems USING GIN (symptoms);
```

---

### 4. `customers`

Stores customer/client information.

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(500) NOT NULL,
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    primary_contact_phone VARCHAR(50),
    billing_address TEXT,
    service_address TEXT,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_customers_company_name ON customers(company_name);
CREATE INDEX idx_customers_deleted ON customers(deleted_at) WHERE deleted_at IS NULL;
```

---

### 5. `locations`

Stores customer locations/facilities.

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    location_name VARCHAR(500) NOT NULL,
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    access_notes TEXT,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_locations_customer ON locations(customer_id);
CREATE INDEX idx_locations_coordinates ON locations(latitude, longitude);
CREATE INDEX idx_locations_deleted ON locations(deleted_at) WHERE deleted_at IS NULL;
```

---

### 6. `equipment_inventory`

Stores actual equipment installed at customer locations.

```sql
CREATE TYPE equipment_status AS ENUM ('active', 'inactive', 'replaced', 'removed');

CREATE TABLE equipment_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES locations(id),
    equipment_model_id UUID REFERENCES equipment_models(id),

    -- If model not in our database, store manually
    manual_manufacturer VARCHAR(255),
    manual_model_number VARCHAR(255),

    serial_number VARCHAR(255),
    installation_date DATE,
    status equipment_status DEFAULT 'active',
    location_detail VARCHAR(500),  -- e.g., "Building A, 3rd Floor, Room 301"
    replacement_of_equipment_id UUID REFERENCES equipment_inventory(id),
    replaced_by_equipment_id UUID REFERENCES equipment_inventory(id),

    -- Component details
    components JSONB DEFAULT '{}',  -- filter_size, belt_size, etc.

    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_equipment_inventory_location ON equipment_inventory(location_id);
CREATE INDEX idx_equipment_inventory_model ON equipment_inventory(equipment_model_id);
CREATE INDEX idx_equipment_inventory_serial ON equipment_inventory(serial_number);
CREATE INDEX idx_equipment_inventory_status ON equipment_inventory(status);
CREATE INDEX idx_equipment_inventory_deleted ON equipment_inventory(deleted_at) WHERE deleted_at IS NULL;
```

---

### 7. `jobs`

Stores service jobs/work orders.

```sql
CREATE TYPE job_status AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled');
CREATE TYPE job_priority AS ENUM ('low', 'normal', 'high', 'urgent');
CREATE TYPE job_type AS ENUM ('inspection', 'maintenance', 'repair', 'installation', 'emergency');

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    location_id UUID NOT NULL REFERENCES locations(id),
    assigned_technician_id UUID REFERENCES users(id),

    job_type job_type NOT NULL,
    job_status job_status DEFAULT 'scheduled',
    priority job_priority DEFAULT 'normal',

    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    duration_estimate_minutes INTEGER,
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,

    title VARCHAR(500) NOT NULL,
    description TEXT,
    special_instructions TEXT,

    -- Checklist stored as JSONB
    checklist JSONB DEFAULT '[]',

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_jobs_customer ON jobs(customer_id);
CREATE INDEX idx_jobs_location ON jobs(location_id);
CREATE INDEX idx_jobs_technician ON jobs(assigned_technician_id);
CREATE INDEX idx_jobs_status ON jobs(job_status);
CREATE INDEX idx_jobs_scheduled_date ON jobs(scheduled_date);
CREATE INDEX idx_jobs_job_number ON jobs(job_number);
CREATE INDEX idx_jobs_deleted ON jobs(deleted_at) WHERE deleted_at IS NULL;
```

---

### 8. `job_equipment`

Links jobs to equipment being serviced.

```sql
CREATE TABLE job_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    equipment_id UUID NOT NULL REFERENCES equipment_inventory(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_equipment_job ON job_equipment(job_id);
CREATE INDEX idx_job_equipment_equipment ON job_equipment(equipment_id);
```

---

### 9. `inspection_records`

Stores inspection results and findings.

```sql
CREATE TABLE inspection_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    equipment_id UUID REFERENCES equipment_inventory(id),
    inspector_id UUID REFERENCES users(id),

    inspection_date DATE NOT NULL,
    inspection_type VARCHAR(255),

    -- Results
    passed BOOLEAN,
    findings TEXT,
    deficiencies JSONB DEFAULT '[]',
    recommendations TEXT,

    -- Measurements/readings
    measurements JSONB DEFAULT '{}',

    -- Photos
    photo_urls JSONB DEFAULT '[]',

    next_inspection_due DATE,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_inspection_records_job ON inspection_records(job_id);
CREATE INDEX idx_inspection_records_equipment ON inspection_records(equipment_id);
CREATE INDEX idx_inspection_records_date ON inspection_records(inspection_date);
CREATE INDEX idx_inspection_records_passed ON inspection_records(passed);
CREATE INDEX idx_inspection_records_deleted ON inspection_records(deleted_at) WHERE deleted_at IS NULL;

-- Partition by year for performance
CREATE TABLE inspection_records_2024 PARTITION OF inspection_records
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

---

### 10. `users` / `technicians`

Stores user/technician information.

```sql
CREATE TYPE user_role AS ENUM ('technician', 'manager', 'admin', 'office_staff');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role user_role NOT NULL,

    -- Technician-specific
    certification_numbers JSONB DEFAULT '[]',
    specializations JSONB DEFAULT '[]',
    hire_date DATE,

    -- Authentication (if handling auth)
    password_hash VARCHAR(255),
    last_login TIMESTAMP,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;
```

---

### 11. `data_capture_logs`

Tracks data capture completion for analytics.

```sql
CREATE TABLE data_capture_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    equipment_id UUID REFERENCES equipment_inventory(id),
    technician_id UUID REFERENCES users(id),

    captured_fields JSONB NOT NULL,  -- Fields that were captured
    missing_fields JSONB DEFAULT '[]',  -- Fields that were missing
    completion_percentage FLOAT,

    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_capture_logs_job ON data_capture_logs(job_id);
CREATE INDEX idx_data_capture_logs_completion ON data_capture_logs(completion_percentage);
```

---

### 12. `performance_metrics`

Stores performance metrics for ROI tracking.

```sql
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_name VARCHAR(255) NOT NULL,
    duration_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_metrics_function ON performance_metrics(function_name);
CREATE INDEX idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);
CREATE INDEX idx_performance_metrics_duration ON performance_metrics(duration_ms);

-- Partition by month for performance
CREATE TABLE performance_metrics_2024_10 PARTITION OF performance_metrics
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');
```

---

## Relationships Diagram

```
manufacturers 1----* equipment_models
equipment_models 1----* common_problems
equipment_models 1----* equipment_inventory
customers 1----* locations
locations 1----* equipment_inventory
customers 1----* jobs
locations 1----* jobs
users 1----* jobs (assigned_technician)
jobs 1----* job_equipment *----1 equipment_inventory
jobs 1----* inspection_records
equipment_inventory 1----* inspection_records
users 1----* inspection_records (inspector)
jobs 1----* data_capture_logs
users 1----* performance_metrics (implicit)
```

---

## Migration Strategy

### Phase 1: Database Setup
1. Create PostgreSQL database
2. Create all tables with indexes
3. Create ENUM types
4. Set up partitioning for large tables

### Phase 2: Data Migration
1. Import manufacturers from sample_data.py
2. Import equipment_models from sample_data.py
3. Import common_problems from common_problems.py
4. Import demo customers/locations
5. Import demo jobs from demo_data.py

### Phase 3: Service Integration
1. Update manufacturer service to use PostgreSQL
2. Update job service to use PostgreSQL
3. Update common problems service to use PostgreSQL
4. Add caching layer (Redis) for frequently accessed specs

### Phase 4: External Integrations
1. ServiceTrade API → sync jobs, equipment, inspections
2. ZenFire API → sync fire safety data
3. QuickBooks API → pricing and parts data

---

## Queries for Common Operations

### Get Factory Specifications
```sql
SELECT
    m.name as manufacturer,
    em.model_number,
    em.product_name,
    em.electrical_specs,
    em.pressure_specs,
    em.temperature_specs,
    em.physical_specs
FROM equipment_models em
JOIN manufacturers m ON em.manufacturer_id = m.id
WHERE em.model_number = 'FTXS12WVJU9'
  AND m.name = 'Daikin'
  AND em.deleted_at IS NULL;
```

### Get Equipment History for Job
```sql
SELECT
    ei.*,
    em.model_number,
    m.name as manufacturer,
    json_agg(
        json_build_object(
            'date', ir.inspection_date,
            'findings', ir.findings,
            'passed', ir.passed
        ) ORDER BY ir.inspection_date DESC
    ) as inspection_history
FROM equipment_inventory ei
LEFT JOIN equipment_models em ON ei.equipment_model_id = em.id
LEFT JOIN manufacturers m ON em.manufacturer_id = m.id
LEFT JOIN inspection_records ir ON ei.id = ir.equipment_id
WHERE ei.location_id = (SELECT location_id FROM jobs WHERE id = $job_id)
  AND ei.deleted_at IS NULL
GROUP BY ei.id, em.model_number, m.name;
```

### Check Data Capture Completeness
```sql
SELECT
    COUNT(*) as total_equipment,
    SUM(CASE WHEN serial_number IS NOT NULL THEN 1 ELSE 0 END) as with_serial,
    SUM(CASE WHEN components->>'filter_size' IS NOT NULL THEN 1 ELSE 0 END) as with_filter_size
FROM equipment_inventory ei
JOIN job_equipment je ON ei.id = je.equipment_id
WHERE je.job_id = $job_id
  AND ei.deleted_at IS NULL;
```

---

## Performance Optimization

### 1. Caching Strategy (Redis)
- Cache frequently accessed equipment specifications (TTL: 24 hours)
- Cache common problems (TTL: 24 hours)
- Cache job details (TTL: 1 hour)
- Invalidate on updates

### 2. Database Indexes
- All foreign keys indexed
- JSONB fields with GIN indexes for fast searches
- Partial indexes on deleted_at for soft deletes
- Covering indexes for common queries

### 3. Connection Pooling
- Use PgBouncer for connection pooling
- Pool size: 20-50 connections
- Transaction mode for most operations

### 4. Query Optimization
- Use EXPLAIN ANALYZE for slow queries
- Avoid N+1 queries (use JOINs or batch loading)
- Materialize views for complex reports

---

## Backup & Disaster Recovery

1. **Daily Backups:** Full PostgreSQL backup using pg_dump
2. **Point-in-Time Recovery:** Enable WAL archiving
3. **Replication:** Hot standby for read replicas
4. **Retention:** 30 days of daily backups, 12 months of monthly

---

## Security Considerations

1. **Encryption at Rest:** Enable PostgreSQL encryption
2. **Encryption in Transit:** Require SSL/TLS connections
3. **Row-Level Security:** Enable RLS for multi-tenant data
4. **Audit Logging:** Enable PostgreSQL audit extension
5. **Access Control:** Limit database user permissions (principle of least privilege)

---

## Next Steps

1. **Week 1:** Implement database schema in PostgreSQL
2. **Week 2:** Migrate sample data and test queries
3. **Week 3:** Update Python services to use PostgreSQL
4. **Week 4:** Add Redis caching layer
5. **Week 5-6:** Integrate with ServiceTrade/ZenFire APIs
6. **Week 7-8:** Load testing and performance tuning

---

**Last Updated:** October 2024
**Status:** Design Complete - Ready for Implementation
**Database Size Estimate:** ~10-50GB for 1000 locations, 10,000 equipment items, 100,000 inspections
