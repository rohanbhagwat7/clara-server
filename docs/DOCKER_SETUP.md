# Clara Infrastructure - Docker Setup Guide

**Quick start for Redis, PostgreSQL, and TimescaleDB**

---

## Quick Start (3 Commands)

```bash
# 1. Copy environment file
cp .env.docker .env

# 2. Start infrastructure
docker-compose up -d

# 3. Verify everything is running
docker-compose ps
```

**That's it!** Redis, PostgreSQL, and TimescaleDB are now running.

---

## What Gets Installed

| Service | Port | Purpose | Required? |
|---------|------|---------|-----------|
| **Redis** | 6379 | Cache, preferences, analytics | ✅ Recommended |
| **PostgreSQL** | 5432 | Database backend | ⚠️ Optional |
| **TimescaleDB** | 5433 | Time-series analytics | ⚠️ Optional |
| **Redis Commander** | 8081 | Redis UI (dev tool) | ⏸️ Profile: tools |
| **pgAdmin** | 5050 | PostgreSQL UI (dev tool) | ⏸️ Profile: tools |

---

## Installation Options

### Option 1: Core Services Only (Recommended for Development)

**Starts:** Redis + PostgreSQL + TimescaleDB

```bash
docker-compose up -d
```

**Why?** Perfect for development - you get persistent storage without complexity.

---

### Option 2: Core + Management Tools (Recommended for Exploration)

**Starts:** Everything + Redis Commander + pgAdmin

```bash
docker-compose --profile tools up -d
```

**Why?** Adds web UIs for managing databases (useful for debugging).

**Access:**
- Redis Commander: http://localhost:8081
- pgAdmin: http://localhost:5050 (login: admin@clara.local / admin)

---

### Option 3: Only What You Need

**Just Redis:**
```bash
docker-compose up -d redis
```

**Redis + PostgreSQL (no TimescaleDB):**
```bash
docker-compose up -d redis postgres
```

**Redis + TimescaleDB (no regular PostgreSQL):**
```bash
docker-compose up -d redis timescaledb
```

---

## Configuration

### 1. Copy Environment File

```bash
cp .env.docker .env
```

### 2. Customize (Optional)

Edit `.env` to change passwords:

```bash
# PostgreSQL
POSTGRES_USER=clara
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=clara

# TimescaleDB
TIMESCALE_USER=clara
TIMESCALE_PASSWORD=your-analytics-password-here
TIMESCALE_DB=clara_analytics

# pgAdmin (optional)
PGADMIN_EMAIL=admin@clara.local
PGADMIN_PASSWORD=your-admin-password
```

---

## Connecting Clara Agent

### Update `clara-agent/.env.local`

After starting Docker Compose, add these to your Clara agent configuration:

```bash
# Redis (for caching, preferences, analytics)
REDIS_URL=redis://localhost:6379

# PostgreSQL (for database storage)
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara

# TimescaleDB (for time-series analytics)
TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics

# Storage backends (switch from memory to persistent)
CACHE_STORAGE_BACKEND=redis
ANALYTICS_STORAGE_BACKEND=timescale
PREFERENCES_STORAGE_BACKEND=database
```

**Restart Clara agent** - it will now use persistent storage!

---

## Useful Commands

### Start/Stop

```bash
# Start all services
docker-compose up -d

# Start with management tools
docker-compose --profile tools up -d

# Stop all services (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove EVERYTHING including data
docker-compose down -v  # ⚠️ DELETES ALL DATA
```

---

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f redis
docker-compose logs -f postgres
docker-compose logs -f timescaledb

# Last 100 lines
docker-compose logs --tail=100 redis
```

---

### Check Status

```bash
# List running services
docker-compose ps

# Check health
docker-compose ps --services --filter "status=running"

# Resource usage
docker stats
```

---

### Database Access

**PostgreSQL:**
```bash
# CLI access
docker-compose exec postgres psql -U clara -d clara

# Or from host (if psql installed)
psql -h localhost -p 5432 -U clara -d clara
```

**TimescaleDB:**
```bash
# CLI access
docker-compose exec timescaledb psql -U clara -d clara_analytics

# Or from host
psql -h localhost -p 5433 -U clara -d clara_analytics
```

**Redis:**
```bash
# CLI access
docker-compose exec redis redis-cli

# Or from host (if redis-cli installed)
redis-cli -h localhost -p 6379
```

---

### Redis Commands (Quick Reference)

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Inside redis-cli:
PING                    # Test connection (returns PONG)
KEYS *                  # List all keys
GET key_name            # Get value
DEL key_name            # Delete key
FLUSHALL                # Clear everything (⚠️ DELETES ALL DATA)
INFO stats              # Stats
DBSIZE                  # Count keys
MONITOR                 # Watch commands in real-time
```

---

### PostgreSQL Commands (Quick Reference)

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U clara -d clara

# Inside psql:
\l                      # List databases
\dt                     # List tables
\d table_name           # Describe table
\q                      # Quit

# Useful queries:
SELECT * FROM user_profiles;
SELECT * FROM user_preferences WHERE user_id = 'test_user_001';
SELECT * FROM response_cache ORDER BY created_at DESC LIMIT 10;
SELECT * FROM customers;
SELECT * FROM contracts WHERE status = 'active';
```

---

### TimescaleDB Commands (Quick Reference)

```bash
# Connect to TimescaleDB
docker-compose exec timescaledb psql -U clara -d clara_analytics

# Inside psql:
\dx                     # List extensions (should see timescaledb)
\d+                     # List tables and hypertables

# Useful analytics queries:
SELECT * FROM recent_tool_performance;
SELECT * FROM user_engagement_7d;
SELECT * FROM error_patterns_24h;

# Raw time-series data:
SELECT * FROM tool_metrics ORDER BY metric_time DESC LIMIT 20;
SELECT * FROM analytics_events ORDER BY event_time DESC LIMIT 20;

# Aggregated data (pre-computed):
SELECT * FROM tool_performance_hourly ORDER BY hour DESC LIMIT 24;
SELECT * FROM user_activity_daily ORDER BY day DESC LIMIT 7;
```

---

## Data Persistence

### Where Data is Stored

```bash
# Docker volumes (persistent across restarts)
docker volume ls | grep clara

# Output:
clara-redis-data        # Redis data
clara-postgres-data     # PostgreSQL data
clara-timescale-data    # TimescaleDB data
clara-pgadmin-data      # pgAdmin settings
```

**Data persists** even when containers are stopped/removed (unless you use `-v` flag).

---

### Backup Data

**Redis:**
```bash
# Create backup
docker-compose exec redis redis-cli SAVE
docker cp clara-redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb

# Restore backup
docker cp ./backups/redis-20251102.rdb clara-redis:/data/dump.rdb
docker-compose restart redis
```

**PostgreSQL:**
```bash
# Create backup
docker-compose exec postgres pg_dump -U clara clara > backups/clara-$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U clara clara < backups/clara-20251102.sql
```

**TimescaleDB:**
```bash
# Create backup
docker-compose exec timescaledb pg_dump -U clara clara_analytics > backups/analytics-$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T timescaledb psql -U clara clara_analytics < backups/analytics-20251102.sql
```

---

### Reset Data

**⚠️ Warning: This deletes all data!**

```bash
# Stop containers and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:6379 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
lsof -i :6379  # macOS/Linux
netstat -ano | findstr :6379  # Windows

# Either:
# 1. Stop the conflicting service
# 2. Or change port in docker-compose.yml:
#    ports:
#      - "6380:6379"  # External:Internal
```

---

### Container Won't Start

```bash
# Check logs
docker-compose logs redis
docker-compose logs postgres

# Check service health
docker-compose ps

# Restart specific service
docker-compose restart redis
```

---

### Connection Refused

**Clara agent can't connect to Redis/PostgreSQL**

**Check 1: Are services running?**
```bash
docker-compose ps
```

**Check 2: Can you connect manually?**
```bash
# Redis
redis-cli -h localhost -p 6379 ping  # Should return PONG

# PostgreSQL
psql -h localhost -p 5432 -U clara -d clara
```

**Check 3: Firewall blocking?**
- On Windows: Allow Docker Desktop through firewall
- On Linux: Check `ufw status`

**Check 4: Wrong connection URL?**
- From host: `redis://localhost:6379`
- From Docker container: `redis://redis:6379`

---

### Database Schema Not Created

**Schema files didn't run**

```bash
# Re-run init scripts manually:

# PostgreSQL
docker-compose exec postgres psql -U clara -d clara < ../clara-server/init-scripts/01-init-schema.sql

# TimescaleDB
docker-compose exec timescaledb psql -U clara -d clara_analytics < ../clara-server/init-scripts-timescale/01-init-timescale.sql
```

---

### Out of Memory

**Error:** Container stopped unexpectedly

**Solution:**
```bash
# Check Docker resources
docker stats

# Increase Docker memory:
# Docker Desktop → Settings → Resources → Memory (increase to 4GB+)
```

---

## Performance Tuning

### Redis (Memory-Limited)

Edit `docker-compose.yml`:
```yaml
redis:
  command: >
    redis-server
    --maxmemory 1gb           # Increase from 512mb
    --maxmemory-policy allkeys-lru
```

### PostgreSQL (More Connections)

Edit `docker-compose.yml`:
```yaml
postgres:
  command: >
    postgres
    -c max_connections=200
    -c shared_buffers=256MB
```

### TimescaleDB (Performance)

```bash
# Connect and tune:
docker-compose exec timescaledb psql -U clara -d clara_analytics

# Inside psql:
ALTER DATABASE clara_analytics SET timescaledb.max_background_workers = 4;
SELECT set_chunk_time_interval('analytics_events', INTERVAL '1 day');
```

---

## Security for Production

### Change Default Passwords

```bash
# Edit .env BEFORE first run:
POSTGRES_PASSWORD=$(openssl rand -base64 32)
TIMESCALE_PASSWORD=$(openssl rand -base64 32)
```

### Enable Redis Authentication

Edit `docker-compose.yml`:
```yaml
redis:
  command: >
    redis-server
    --requirepass your-secure-password-here
```

Update connection URL:
```bash
REDIS_URL=redis://:your-secure-password-here@localhost:6379
```

### Use SSL/TLS

For production, use reverse proxy (nginx/Traefik) with SSL certificates.

---

## Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats clara-redis
```

### Disk Usage

```bash
# Check volume sizes
docker system df -v

# Clean up unused data
docker system prune
docker volume prune  # ⚠️ DELETES UNUSED VOLUMES
```

---

## Migration from Memory to Docker

### Current State (Memory Storage)
```bash
# clara-agent/.env.local
CACHE_STORAGE_BACKEND=memory
ANALYTICS_STORAGE_BACKEND=memory
PREFERENCES_STORAGE_BACKEND=memory
```

### New State (Docker Persistent Storage)

**1. Start Docker Compose:**
```bash
docker-compose up -d
```

**2. Update clara-agent/.env.local:**
```bash
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara
TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics

CACHE_STORAGE_BACKEND=redis
ANALYTICS_STORAGE_BACKEND=timescale
PREFERENCES_STORAGE_BACKEND=database
```

**3. Restart Clara agent**

**4. Verify:**
```bash
# Check Redis has data
docker-compose exec redis redis-cli DBSIZE

# Check PostgreSQL has tables
docker-compose exec postgres psql -U clara -d clara -c "\dt"

# Check TimescaleDB has analytics
docker-compose exec timescaledb psql -U clara -d clara_analytics -c "SELECT COUNT(*) FROM analytics_events;"
```

✅ **Migration complete!** Data now persists across restarts.

---

## Summary

### Minimal Setup (Development)
```bash
cp .env.docker .env
docker-compose up -d
```

### Production Setup (with all features)
```bash
# 1. Configure
cp .env.docker .env
# Edit .env with secure passwords

# 2. Start
docker-compose up -d

# 3. Configure Clara agent
# Update clara-agent/.env.local with connection URLs

# 4. Verify
docker-compose ps
docker-compose logs
```

### Daily Usage
```bash
# Start
docker-compose start

# Stop
docker-compose stop

# View logs
docker-compose logs -f redis

# Check status
docker-compose ps
```

---

## Support

**Common Issues:**
- Port conflicts → Change ports in docker-compose.yml
- Connection refused → Check `docker-compose ps` and firewall
- Out of memory → Increase Docker Desktop memory limit
- Data loss → Never use `docker-compose down -v` in production

**Data Locations:**
- Redis: `/data` (inside container)
- PostgreSQL: `/var/lib/postgresql/data` (inside container)
- All data persists in Docker volumes (survives container restarts)

**Need help?** Check logs: `docker-compose logs <service-name>`

---

🚀 **Ready!** Your Clara infrastructure is now running in Docker with automatic persistence, backups, and scaling capabilities.
