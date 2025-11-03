# 🚀 Clara Backend - Quick Start Guide

Complete guide to get Clara running in 5 minutes!

## Prerequisites

- ✅ Python 3.11+
- ✅ Docker Desktop (for infrastructure)
- ✅ Git
- ✅ LiveKit account (for voice)

## Step-by-Step Setup

### 1. Start Infrastructure (30 seconds)

```bash
cd D:/lean/clara-backend

# Start all infrastructure containers
docker-compose up -d

# Verify containers are running (should see 4 containers)
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE              STATUS         PORTS                    NAMES
xxx            postgres:14        Up 5 seconds   0.0.0.0:5432->5432/tcp  clara-postgres
xxx            redis:7            Up 5 seconds   0.0.0.0:6381->6379/tcp  clara-redis
xxx            timescale/...      Up 5 seconds   0.0.0.0:5433->5432/tcp  clara-timescaledb
xxx            chromadb/...       Up 5 seconds   0.0.0.0:8000->8000/tcp  clara-chromadb
```

### 2. Start Clara Server (1 minute)

**Terminal 1:**
```bash
cd D:/lean/clara-backend/clara-server

# Install dependencies
pip install -e .

# Start server
uvicorn main:app --reload --port 3000
```

**Verify server is running:**

Open new terminal:
```bash
curl http://localhost:3000/health
```

Should return:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

**View API documentation:**
Open browser: http://localhost:3000/docs

### 3. Start Clara Agent (1 minute)

**Terminal 2:**
```bash
cd D:/lean/clara-backend/clara-agent

# Install dependencies (lightweight now!)
pip install -e .

# Start agent
python -m src.agent
```

**Verify agent is running:**

You should see:
```
INFO:agent:Clara Agent starting...
INFO:agent:Initializing API client for backend communication...
INFO:api_client:Connected to Clara Server at http://localhost:3000
INFO:agent:LiveKit connection established
INFO:agent:Agent ready for voice interactions
```

### 4. Test the System (2 minutes)

#### Test 1: Server API Endpoints

```bash
# Get all jobs
curl http://localhost:3000/jobs

# Get customers
curl http://localhost:3000/api/crm/customers

# Search knowledge base
curl "http://localhost:3000/api/knowledge/search?query=sprinkler&n_results=3"

# Get analytics
curl http://localhost:3000/api/analytics/stats
```

#### Test 2: Agent-Server Communication

Watch the agent logs - you should see API calls when agent needs data:

```
INFO:api_client:GET http://localhost:3000/jobs → 200 OK
INFO:api_client:GET http://localhost:3000/api/crm/customers → 200 OK
```

#### Test 3: Voice Interactions (if LiveKit configured)

Connect via LiveKit and say:
- "What are today's jobs?"
- "Tell me about this customer"
- "Search NFPA requirements"

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      USER (Voice)                        │
└────────────────────────┬────────────────────────────────┘
                         │ LiveKit Audio
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   CLARA AGENT                            │
│  - AI/Voice Processing (Gemini, Claude)                 │
│  - Tool Orchestration                                    │
│  - SSML Voice Formatting                                 │
│  - External APIs (Tavily, Firecrawl)                    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST API
                         │ (api_client.py)
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   CLARA SERVER                           │
│  - REST API (FastAPI)                                    │
│  - Business Logic                                        │
│  - Data Management                                       │
└────────────────────────┬────────────────────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      ↓                  ↓                   ↓
┌──────────┐      ┌──────────┐       ┌──────────┐
│PostgreSQL│      │  Redis   │       │ ChromaDB │
│ (Jobs,   │      │ (Cache,  │       │(Knowledge│
│  CRM)    │      │  Prefs)  │       │  Base)   │
└──────────┘      └──────────┘       └──────────┘
```

## System Components

### Clara Server (clara-server/)
**Role**: Complete backend - all data and business logic

**Owns:**
- ✅ PostgreSQL, Redis, TimescaleDB, ChromaDB connections
- ✅ Business logic (CRM, Analytics, Jobs, Manufacturer)
- ✅ Data validation and history
- ✅ Pattern learning and monitoring
- ✅ User preferences and caching
- ✅ Google Maps integration
- ✅ LiveKit token generation

**Modules:**
- `caching/` - Response caching
- `context/` - User preferences
- `jobs/` - Data validation, history
- `knowledge/` - RAG/ChromaDB searches
- `manufacturer/` - Equipment catalog
- `monitoring/` - Metrics collection
- `nudges/` - Nudge business logic
- `patterns/` - Pattern learning/ML

### Clara Agent (clara-agent/)
**Role**: Lightweight AI/voice interface

**Owns:**
- ✅ LiveKit audio streaming
- ✅ AI integrations (Claude, Gemini)
- ✅ Voice-specific processing (SSML)
- ✅ Tool definitions for AI
- ✅ External API calls (Tavily, Firecrawl)
- ✅ Agent error handling
- ✅ Conversation memory

**Modules:**
- `config/` - Configuration
- `context/` - Conversation memory
- `estimates/` - AI estimate generation
- `jobs/` - Voice data capture
- `manuals/` - External APIs
- `resilience/` - Error handling
- `training/` - AI training
- `voice/` - SSML formatting

## Configuration Files

### clara-server/.env.local
```bash
# Infrastructure
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara
REDIS_URL=redis://localhost:6381
TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics
CHROMADB_URL=http://localhost:8000

# External Services
GOOGLE_MAPS_API_KEY=<your-key>
LIVEKIT_URL=<your-livekit-url>
LIVEKIT_API_KEY=<your-key>
LIVEKIT_API_SECRET=<your-secret>
```

### clara-agent/.env.local
```bash
# Clara Server connection (CRITICAL!)
BACKEND_URL=http://localhost:3000

# LiveKit
LIVEKIT_URL=wss://claranew-00jbylxr.livekit.cloud
LIVEKIT_API_KEY=<your-key>
LIVEKIT_API_SECRET=<your-secret>

# AI Services
GOOGLE_API_KEY=<your-gemini-key>

# External APIs (optional)
TAVILY_API_KEY=<your-key>
FIRECRAWL_API_KEY=<your-key>

# ChromaDB (for agent-specific local searches)
CHROMADB_URL=http://localhost:8000
```

## Common Issues & Solutions

### Issue 1: "Port 3000 already in use"

```bash
# Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use different port
uvicorn main:app --reload --port 8000
# Update BACKEND_URL in agent .env.local to match
```

### Issue 2: "Database connection failed"

```bash
# Check Docker containers
docker ps

# Restart database
docker-compose restart postgres

# Check if initialized
docker exec -it clara-postgres psql -U clara -d clara -c "\dt"
```

### Issue 3: "Agent can't connect to server"

```bash
# Verify server is running
curl http://localhost:3000/health

# Check BACKEND_URL in clara-agent/.env.local
cat clara-agent/.env.local | grep BACKEND_URL

# Should be: BACKEND_URL=http://localhost:3000
```

### Issue 4: "ModuleNotFoundError" in agent

```bash
cd clara-agent

# Clean reinstall (dependencies changed!)
pip uninstall agent-starter-python -y
pip install -e .

# If psycopg/sqlalchemy errors (these are removed):
pip freeze | grep -E "(psycopg|sqlalchemy|redis)" | xargs pip uninstall -y
pip install -e .
```

### Issue 5: "ChromaDB not accessible"

```bash
# Restart ChromaDB
docker-compose restart chromadb

# Test connection
curl http://localhost:8000/api/v1/heartbeat
```

## Verification Checklist

Before using Clara in production:

- [ ] Docker containers running (4 total)
- [ ] Server health check passes: `curl http://localhost:3000/health`
- [ ] Server API docs accessible: http://localhost:3000/docs
- [ ] Agent starts without errors
- [ ] Agent logs show "Connected to Clara Server"
- [ ] Test job retrieval: `curl http://localhost:3000/jobs`
- [ ] Test CRM: `curl http://localhost:3000/api/crm/customers`
- [ ] Test knowledge: `curl http://localhost:3000/api/knowledge/search?query=test`
- [ ] Voice connection works (if LiveKit configured)

## Performance Expectations

After restructuring:

**Clara Server:**
- Startup: 2-3 seconds
- Memory: ~300MB
- Handles: Database, business logic, infrastructure

**Clara Agent:**
- Startup: <1 second (was 3-5s!)
- Memory: ~200MB (was ~500MB!)
- Dependencies: 15 packages (was 50+!)
- API latency: +50-100ms (acceptable for voice)

## Next Steps

1. ✅ **Test the system** - Run through verification checklist
2. ✅ **Configure LiveKit** - For voice interactions
3. ✅ **Add your data** - Customize jobs, customers, equipment
4. ✅ **Monitor** - Watch logs for API calls and errors
5. ✅ **Scale** - Run multiple agent instances if needed

## Detailed Documentation

- **START_SERVER.md** - Detailed server setup
- **START_AGENT.md** - Detailed agent setup
- **ARCHITECTURE.md** - System architecture
- **RESTRUCTURING_COMPLETE.md** - Restructuring details
- **MIGRATION_COMPLETE.md** - Agent migration details

## Support

For issues or questions:
1. Check logs in both server and agent terminals
2. Verify Docker containers are running: `docker ps`
3. Test server health: `curl http://localhost:3000/health`
4. Check environment variables in .env.local files

---

**You're all set!** 🎉

The Clara system is now running with:
- ✅ Clean microservices architecture
- ✅ clara-server handling all data/infrastructure
- ✅ clara-agent handling AI/voice
- ✅ Complete separation of concerns
