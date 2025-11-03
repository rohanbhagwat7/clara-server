# Clara Backend Architecture

## Overview

Clara uses a **microservices architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Clara Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Frontend   │◄────────┤  Clara Server  │◄────┐           │
│  │ (React Native│  REST   │  (FastAPI)   │     │           │
│  │   Mobile)    │         │              │     │           │
│  └──────────────┘         │  Port 3000   │     │           │
│                           └──────┬───────┘     │           │
│                                  │             │           │
│  ┌──────────────┐                │             │           │
│  │  Clara Agent │────────────────┘             │           │
│  │  (LiveKit)   │  HTTP Calls                  │           │
│  │              │  via API Client               │           │
│  └──────┬───────┘                              │           │
│         │                                       │           │
│         │ LiveKit WebRTC                        │           │
│         │                                       │           │
│  ┌──────▼───────┐                              │           │
│  │   End User   │                              │           │
│  │(Technician)  │                              │           │
│  └──────────────┘                              │           │
│                                                 │           │
│  ┌──────────────────────────────────────────┐  │           │
│  │         Infrastructure Layer             │  │           │
│  ├──────────────────────────────────────────┤  │           │
│  │  PostgreSQL  │  Redis  │ TimescaleDB     │◄─┘           │
│  │  ChromaDB    │  Google Maps │ LiveKit    │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Clara Server (`clara-server/`)
**Role**: Complete backend - data layer, business logic, infrastructure management

**Responsibilities**:
- ✅ All database connections (PostgreSQL, Redis, TimescaleDB, ChromaDB)
- ✅ Business logic (CRM, Analytics, Jobs management)
- ✅ REST API endpoints for frontend and agent
- ✅ Infrastructure health monitoring
- ✅ Data validation and persistence
- ✅ LiveKit token generation
- ✅ Google Maps integration
- ✅ Knowledge base queries (NFPA, HVAC)

**Technology Stack**:
- FastAPI (Python web framework)
- PostgreSQL (relational data)
- Redis (caching, preferences)
- TimescaleDB (time-series analytics)
- ChromaDB (vector database for knowledge)
- Google Maps API
- LiveKit API

**What it DOES**:
```python
# Handles ALL data operations
GET  /jobs                       # Jobs from PostgreSQL
GET  /clara-server/crm/customers          # CRM from PostgreSQL
GET  /clara-server/knowledge/search       # Knowledge from ChromaDB
POST /clara-server/analytics/event        # Analytics to TimescaleDB
GET  /clara-server/cache/stats            # Cache from Redis
```

### 2. Clara Agent (`clara-agent/`)
**Role**: AI intelligence, voice interface, tool execution

**Responsibilities**:
- ✅ LiveKit audio streaming and real-time communication
- ✅ Claude AI integration (Gemini)
- ✅ Tool/function definitions for AI
- ✅ MCP (Model Context Protocol) integrations
- ✅ Voice optimization (SSML formatting)
- ✅ Conversation flow and context management
- ✅ Calls API server for ALL data needs

**Technology Stack**:
- LiveKit Agents SDK
- Google Gemini API
- Python async/await
- API Client (HTTP calls to backend)

**What it DOES**:
```python
# Defines tools for Claude
@tool
async def get_customer_info(location: str):
    # Calls API server
    api = get_api_client()
    customer = await api.get_customer_by_location(location)
    return format_customer_info(customer)

@tool
async def search_nfpa(query: str):
    # Calls API server
    api = get_api_client()
    results = await api.search_nfpa_standards(query)
    return results
```

**What it DOES NOT do**:
- ❌ Direct database connections
- ❌ Business logic (handled by API)
- ❌ Data persistence (handled by API)
- ❌ Infrastructure management

### 3. Frontend (`clara-react-native/`)
**Role**: User interface for technicians

**Responsibilities**:
- ✅ Display jobs, schedules, daily briefings
- ✅ Show customer information
- ✅ LiveKit voice session UI
- ✅ Offline support
- ✅ Camera, location services

**What it DOES**:
```typescript
// Calls API server for data
const jobs = await fetch('http://localhost:3000/jobs')
const dailyBrief = await fetch('http://localhost:3000/daily-brief')

// Connects to LiveKit for voice
const room = await connectToLiveKit(token)
```

## Data Flow Examples

### Example 1: User asks "Who is the customer at this location?"

```
1. User speaks to Clara Agent via LiveKit
   ↓
2. Agent receives audio, transcribes with LiveKit
   ↓
3. Claude AI determines tool to call: get_customer_info(location="WeWork")
   ↓
4. Agent's tool calls Clara Server:
   GET http://localhost:3000/clara-server/crm/customers/by-location/WeWork
   ↓
5. Clara Server queries PostgreSQL database
   ↓
6. Clara Server returns customer data
   ↓
7. Agent formats response for voice
   ↓
8. Agent speaks response via LiveKit
   ↓
9. User hears: "This is WeWork, a commercial office space..."
```

### Example 2: User asks "What are the NFPA requirements for sprinkler testing?"

```
1. User speaks to Clara Agent via LiveKit
   ↓
2. Agent receives audio, transcribes
   ↓
3. Claude AI determines tool: search_nfpa("sprinkler testing requirements")
   ↓
4. Agent's tool calls Clara Server:
   GET http://localhost:3000/clara-server/knowledge/search?query=sprinkler+testing
   ↓
5. Clara Server queries ChromaDB vector database
   ↓
6. Clara Server returns relevant NFPA standards
   ↓
7. Agent formats and speaks response
```

### Example 3: Frontend loads jobs list

```
1. Mobile app opens Jobs screen
   ↓
2. App calls Clara Server:
   GET http://localhost:3000/jobs?latitude=37.7&longitude=-122.4
   ↓
3. Clara Server queries PostgreSQL for jobs
   ↓
4. Clara Server calculates distances via Google Maps
   ↓
5. Clara Server returns sorted jobs with travel times
   ↓
6. App displays jobs list with distances
```

## Infrastructure Access

### Clara Server Connects To:
```yaml
PostgreSQL:
  - Host: localhost:5432
  - Database: clara
  - Purpose: Jobs, customers, contracts, equipment

Redis:
  - Host: localhost:6381
  - Purpose: Caching, user preferences

TimescaleDB:
  - Host: localhost:5433
  - Database: clara_analytics
  - Purpose: Time-series analytics

ChromaDB:
  - Host: localhost:8000
  - Purpose: NFPA knowledge, HVAC manuals

Google Maps API:
  - Purpose: Distance calculations

LiveKit API:
  - Purpose: Token generation, room management
```

### Agent Connects To:
```yaml
Clara Server:
  - Host: localhost:3000
  - Purpose: ALL data operations

LiveKit Server:
  - Host: wss://claranew-00jbylxr.livekit.cloud
  - Purpose: Real-time audio streaming

Google Gemini API:
  - Purpose: AI inference
```

## Migration Path

### Current State Issues:
- ❌ Agent has direct database connections (should be removed)
- ❌ Agent has CRM, Analytics, Jobs services (should use API)
- ❌ Agent manages Redis, PostgreSQL directly (should use API)
- ❌ Duplicated business logic between agent and API

### Target State:
- ✅ Agent only has tools, MCP integrations, LiveKit
- ✅ Agent calls API for ALL data via `api_client.py`
- ✅ Clara Server is single source of truth for data
- ✅ Clean separation of concerns

### Files to Refactor in Agent:

**Remove/Refactor** (use API instead):
```
clara-agent/src/
├── crm/crm_service.py          → Use api_client.get_customer_*()
├── analytics/analytics_engine.py → Use api_client.track_event()
├── jobs/service.py              → Use api_client.get_all_jobs()
├── database/db_helper.py        → Remove (API handles this)
├── caching/response_cache.py    → Use api_client.get_cache_stats()
└── context/user_preferences.py  → Use api_client.get_user_preferences()
```

**Keep** (agent-specific):
```
clara-agent/src/
├── agent.py                     → Main agent logic
├── api_client.py                → NEW: API communication
├── voice/ssml_formatter.py      → Voice optimization
├── context/conversation_memory.py → Conversation tracking
├── knowledge/nfpa_service.py    → RAG queries (via API)
└── tools/                       → Tool definitions for Claude
```

## Configuration

### Clara Server (`.env.local` in `clara-server/`)
```bash
# Infrastructure
DATABASE_URL=postgresql://clara:password@localhost:5432/clara
REDIS_URL=redis://localhost:6381
TIMESCALE_URL=postgresql://clara:password@localhost:5433/clara_analytics
CHROMADB_URL=http://localhost:8000

# External Services
GOOGLE_MAPS_API_KEY=...
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

### Agent (`.env.local` in `clara-agent/`)
```bash
# Clara Server connection
BACKEND_URL=http://localhost:3000

# AI Services
GOOGLE_API_KEY=...         # Gemini
TAVILY_API_KEY=...         # Web search
FIRECRAWL_API_KEY=...      # Manual extraction

# LiveKit (for voice)
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

# Feature Flags
USE_GOOGLE_SEARCH_GROUNDING=false
```

## Benefits of This Architecture

### 1. **Separation of Concerns**
- API handles data, Agent handles AI
- Clear boundaries between components

### 2. **Scalability**
- Scale API and Agent independently
- Multiple agents can share one API server

### 3. **Maintainability**
- Changes to data layer don't affect agent
- Changes to AI logic don't affect API

### 4. **Testing**
- Mock API for agent testing
- Test API endpoints independently

### 5. **Security**
- Database credentials only in API server
- Agent has no direct infrastructure access

### 6. **Flexibility**
- Can add web frontend using same API
- Can add additional agents (e.g., supervisor agent)

## Development Workflow

### Starting Services:

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Start Clara Server
cd clara-server
pip install -e .
uvicorn main:app --reload --port 3000

# 3. Start Agent
cd clara-agent
pip install -e .
python -m src.agent
```

### Testing:

```bash
# Test Clara Server
curl http://localhost:3000/health

# Test specific endpoints
curl http://localhost:3000/clara-server/crm/customers
curl http://localhost:3000/clara-server/knowledge/stats

# API Documentation
open http://localhost:3000/docs
```

## Summary

**Clara Server** = The brain (data & logic)
**Clara Agent** = The voice (AI & communication)
**Frontend** = The eyes (user interface)

Each component does what it does best, with clear interfaces between them.
