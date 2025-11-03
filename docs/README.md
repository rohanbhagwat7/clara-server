# Clara Backend

**AI-powered voice assistant for fire life safety technicians**

Clara is an intelligent voice and text assistant that helps fire safety technicians access equipment specifications, NFPA standards, manuals, and customer intelligence in real-time.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Infrastructure Setup](#infrastructure-setup)
- [Development](#development)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## Overview

Clara provides:
- 🎙️ **Voice-first interaction** via LiveKit audio streaming
- 📚 **Instant access** to NFPA standards, equipment specs, and manuals
- 🧠 **Customer intelligence** with CRM integration
- 📊 **Analytics tracking** for performance optimization
- 🔄 **Pattern learning** for proactive suggestions
- 💾 **Multi-layer caching** for 15x faster responses

### Key Components

| Component | Purpose |
|-----------|---------|
| **clara-agent** | Python agent with Claude AI integration |
| **api** | FastAPI backend for REST endpoints |
| **clara_token** | Authentication service |

---

## Architecture

```
clara-backend/
├── clara-agent/          # AI Agent (main service)
│   ├── src/
│   │   ├── agent.py                 # Main agent logic
│   │   ├── caching/                 # Multi-layer cache (memory + Redis)
│   │   ├── voice/                   # SSML voice formatting
│   │   ├── context/                 # Conversation memory + preferences
│   │   ├── resilience/              # Retry logic + fallbacks
│   │   ├── analytics/               # Event tracking + metrics
│   │   ├── patterns/                # Pattern learning
│   │   ├── crm/                     # Customer intelligence
│   │   └── config.py                # Configuration management
│   └── data/
│       ├── chroma_db/               # Vector database (NFPA, manuals)
│       └── specifications/          # Equipment spec JSONs
│
├── clara_token/          # Auth service
│
├── docker-compose.yml    # Infrastructure (Redis, PostgreSQL, TimescaleDB)
└── docs/                 # Additional documentation

Note: Database init scripts are now in clara-server repository
Note: clara-server is now a separate repository at https://github.com/rohanbhagwat7/clara-server
```

---

## Prerequisites

### Required

- **Python 3.11+** (for both Agent and API)
- **Docker & Docker Compose** (for infrastructure)

### API Keys Required

- **LiveKit** (audio streaming)
  - Get from: https://cloud.livekit.io
  - Required: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

- **Google AI / Gemini** (AI model)
  - Get from: https://ai.google.dev
  - Required: `GOOGLE_API_KEY`

- **Tavily** (web search)
  - Get from: https://tavily.com
  - Required: `TAVILY_API_KEY`

- **Firecrawl** (manual extraction)
  - Get from: https://firecrawl.dev
  - Required: `FIRECRAWL_API_KEY`

### Optional

- **Redis** (for persistent caching - can use memory storage)
- **PostgreSQL** (for database storage - can use memory storage)
- **TimescaleDB** (for time-series analytics - can use memory storage)

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd clara-backend
```

### 2. Setup Infrastructure (Optional but Recommended)

**Start Redis, PostgreSQL, and TimescaleDB:**

```bash
# Windows
docker-setup.bat

# Linux/Mac
./docker-setup.sh

# Or using Make
make setup

# Or using docker-compose directly
cp .env.docker .env
docker-compose up -d
```

This starts:
- Redis on port 6379
- PostgreSQL on port 5432
- TimescaleDB on port 5433

**Note:** If you skip this step, Clara will use in-memory storage (data lost on restart).

### 3. Setup Clara Agent

```bash
cd clara-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cd clara-agent
cp .env.example .env.local
```

**Edit `.env.local` with your API keys:**

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Google AI (Gemini)
GOOGLE_API_KEY=your-google-api-key

# Tavily Search
TAVILY_API_KEY=your-tavily-key

# Firecrawl (manual extraction)
FIRECRAWL_API_KEY=your-firecrawl-key

# Backend URL
BACKEND_URL=http://localhost:3000

# Feature Flags
USE_GOOGLE_SEARCH_GROUNDING=false

# ============================================================================
# Storage Configuration (if using Docker infrastructure)
# ============================================================================

# Connection URLs (uncomment if Docker is running)
# REDIS_URL=redis://localhost:6379
# DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara
# TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics

# Storage backends (change to redis/database if using Docker)
CACHE_STORAGE_BACKEND=memory
ANALYTICS_STORAGE_BACKEND=memory
PREFERENCES_STORAGE_BACKEND=memory

# Analytics
ANALYTICS_ENABLED=true
ANALYTICS_TRACK_TOOL_CALLS=true

# Pattern Learning
PATTERN_LEARNING_ENABLED=true
```

### 5. Run Clara Agent

```bash
cd clara-agent
python -m src.agent
```

You should see:
```
[Agent] Clara Agent initialized
[LiveKit] Connected to LiveKit server
[Agent] Ready to receive requests
```

### 6. Setup API (Optional)

```bash
cd clara-server

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies (choose one method)
# Method 1: Using pyproject.toml (recommended)
pip install -e .

# Method 2: Using requirements.txt
# pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --reload --port 3000
```

API runs on http://localhost:3000

---

## Project Structure

### clara-agent/

```
clara-agent/
├── src/
│   ├── agent.py                    # Main agent entry point
│   │
│   ├── caching/                    # Response caching (15x faster)
│   │   ├── response_cache.py       # Multi-layer cache (memory + Redis)
│   │   └── request_deduper.py      # Prevent duplicate requests
│   │
│   ├── voice/                      # Voice optimization
│   │   └── ssml_formatter.py       # SSML formatting for clarity
│   │
│   ├── context/                    # Intelligence systems
│   │   ├── conversation_memory.py  # Conversation tracking
│   │   └── user_preferences.py     # User profiles + skill levels
│   │
│   ├── resilience/                 # Error handling
│   │   ├── fallback_manager.py     # Multi-source fallbacks
│   │   └── retry_manager.py        # Exponential backoff
│   │
│   ├── analytics/                  # Analytics & metrics
│   │   └── analytics_engine.py     # Event tracking
│   │
│   ├── patterns/                   # Pattern learning
│   │   └── pattern_learner.py      # Sequence mining + anomaly detection
│   │
│   ├── crm/                        # Customer intelligence
│   │   └── crm_service.py          # CRM integration (mock data)
│   │
│   └── config.py                   # Configuration loader
│
├── data/
│   ├── chroma_db/                  # Vector database
│   │   └── (NFPA standards, manuals indexed here)
│   │
│   └── specifications/             # Equipment specs (JSON)
│       ├── carrier_48tcd_series.json
│       ├── carrier_50tcqa_series.json
│       └── ...
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── .env.local                      # Your config (gitignored)
```

---

## Environment Variables

### Core Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `LIVEKIT_URL` | ✅ | LiveKit server URL | - |
| `LIVEKIT_API_KEY` | ✅ | LiveKit API key | - |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit API secret | - |
| `GOOGLE_API_KEY` | ✅ | Google AI/Gemini key | - |
| `TAVILY_API_KEY` | ✅ | Tavily search key | - |
| `FIRECRAWL_API_KEY` | ✅ | Firecrawl extraction key | - |
| `BACKEND_URL` | ✅ | API backend URL | `http://localhost:3000` |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_GOOGLE_SEARCH_GROUNDING` | `false` | Use Google search (conflicts with custom tools) |

### Storage Configuration

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `CACHE_STORAGE_BACKEND` | `memory` | `memory`, `redis`, `database` | Cache storage |
| `ANALYTICS_STORAGE_BACKEND` | `memory` | `memory`, `redis`, `timescale` | Analytics storage |
| `PREFERENCES_STORAGE_BACKEND` | `memory` | `memory`, `redis`, `database` | User prefs storage |

### Analytics & Learning

| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYTICS_ENABLED` | `true` | Enable analytics tracking |
| `ANALYTICS_TRACK_TOOL_CALLS` | `true` | Track tool performance |
| `PATTERN_LEARNING_ENABLED` | `true` | Enable pattern learning |
| `PATTERN_MIN_CONFIDENCE` | `0.5` | Min confidence for suggestions |

### Connection URLs (when using Docker)

| Variable | Example | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `DATABASE_URL` | `postgresql://clara:pass@localhost:5432/clara` | PostgreSQL connection |
| `TIMESCALE_URL` | `postgresql://clara:pass@localhost:5433/clara_analytics` | TimescaleDB connection |

See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for complete reference.

---

## Infrastructure Setup

### Option 1: Memory Storage (Development)

**No setup required!** Works out of the box with in-memory storage.

**Pros:**
- ✅ Zero configuration
- ✅ Fastest performance
- ✅ No dependencies

**Cons:**
- ❌ Data lost on restart
- ❌ Single instance only

### Option 2: Docker Infrastructure (Recommended)

**Start persistent storage:**

```bash
./docker-setup.sh  # or docker-setup.bat on Windows
```

This starts:
- **Redis** (cache, preferences)
- **PostgreSQL** (database)
- **TimescaleDB** (time-series analytics)

**Update `.env.local`:**

```bash
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://clara:clara_dev_password@localhost:5432/clara
TIMESCALE_URL=postgresql://clara:clara_analytics_password@localhost:5433/clara_analytics

CACHE_STORAGE_BACKEND=redis
ANALYTICS_STORAGE_BACKEND=timescale
PREFERENCES_STORAGE_BACKEND=database
```

**Pros:**
- ✅ Data persists across restarts
- ✅ Production-ready
- ✅ Scalable

**Cons:**
- Requires Docker

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for complete guide.

---

## Development

### Running the Agent

```bash
cd clara-agent
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m src.agent
```

### Running the API

```bash
cd clara-server
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .  # If not already installed
uvicorn main:app --reload --port 3000
```

### Running with Docker Infrastructure

```bash
# Start infrastructure
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop infrastructure
docker-compose stop
```

### Useful Commands

```bash
# Using Makefile (if Docker infrastructure running)
make status          # Check service status
make logs            # View all logs
make redis-cli       # Connect to Redis
make psql            # Connect to PostgreSQL
make backup          # Backup all databases
make clean           # Stop and remove containers
```

### Adding Equipment Specifications

Add JSON files to `clara-agent/data/specifications/`:

```json
{
  "model": "Carrier 50TCQA06",
  "type": "Compressor",
  "specifications": {
    "cooling_capacity_tons": 5.0,
    "voltage": "230V",
    "amp_draw": 18.2
  }
}
```

Agent automatically loads specs on startup.

---

## API Reference

### LiveKit Integration

Clara uses LiveKit for real-time audio streaming:

1. Mobile app connects to LiveKit room
2. Agent joins room and listens for audio
3. User speaks → Agent processes → Responds with voice

### REST Endpoints (API Service)

**Base URL:** `http://localhost:3000`

#### Get Job Token
```http
POST /clara-server/jobs/get-token
Content-Type: application/json

{
  "userId": "user123",
  "jobId": "job456"
}

Response: {
  "token": "eyJ...",
  "room": "job-job456"
}
```

#### Travel Time
```http
POST /clara-server/travel-time
Content-Type: application/json

{
  "origin": "123 Main St",
  "destination": "456 Oak Ave"
}

Response: {
  "duration": 1800,
  "distance": 15.5
}
```

---

## Testing

### Manual Testing

1. **Start Clara Agent:**
   ```bash
   cd clara-agent
   python -m src.agent
   ```

2. **Connect mobile app** (see clara-react-native README)

3. **Test voice interaction:**
   - "What's the amp draw for Carrier 50TCQA06?"
   - "Show me NFPA 25 requirements"
   - "Who is the customer at this location?"

### Test Customer Intelligence

The mock CRM includes 2 customers:

**WeWork (123 Main St, San Francisco)**
- High-value commercial ($450K lifetime)
- 2 opportunities ($45K + $95K)
- Special requirements

**ABC Manufacturing (456 Industrial Pkwy, Oakland)**
- Industrial facility ($280K lifetime)
- 1 opportunity ($65K)
- Weekend service required

Test: "Tell me about the customer at WeWork"

### Verify Infrastructure

```bash
# Test Redis
docker-compose exec redis redis-cli ping

# Test PostgreSQL
docker-compose exec postgres psql -U clara -d clara -c "SELECT COUNT(*) FROM user_profiles;"

# Test TimescaleDB
docker-compose exec timescaledb psql -U clara -d clara_analytics -c "SELECT COUNT(*) FROM analytics_events;"
```

---

## Deployment

### Production Checklist

**Security:**
- [ ] Change all default passwords in `.env`
- [ ] Enable Redis authentication
- [ ] Use SSL/TLS for all connections
- [ ] Restrict network access (firewall)
- [ ] Use secrets management (Vault, etc.)

**Infrastructure:**
- [ ] Use Redis cluster (multi-node)
- [ ] PostgreSQL replication
- [ ] TimescaleDB multi-node
- [ ] Load balancer for agents
- [ ] Automated backups

**Monitoring:**
- [ ] Set up logging (structured logs)
- [ ] Metrics collection (Prometheus)
- [ ] Alerts (PagerDuty)
- [ ] Dashboards (Grafana)

**Performance:**
- [ ] Review cache hit rates (target: >70%)
- [ ] Monitor response times
- [ ] Check database indexes
- [ ] Optimize vector DB

### Environment-Specific Configs

**Development:**
```bash
CACHE_STORAGE_BACKEND=memory
ANALYTICS_ENABLED=true
```

**Staging:**
```bash
REDIS_URL=redis://staging-redis:6379
CACHE_STORAGE_BACKEND=redis
ANALYTICS_STORAGE_BACKEND=timescale
```

**Production:**
```bash
REDIS_URL=rediss://prod-redis-cluster:6380
DATABASE_URL=postgresql://user:pass@prod-db:5432/clara?sslmode=require
TIMESCALE_URL=postgresql://user:pass@prod-analytics:5432/analytics?sslmode=require
CACHE_STORAGE_BACKEND=redis
ANALYTICS_STORAGE_BACKEND=timescale
PREFERENCES_STORAGE_BACKEND=database
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | Complete configuration reference |
| [DOCKER_SETUP.md](DOCKER_SETUP.md) | Docker infrastructure guide |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Database schema reference |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Demo and testing guide |

---

## Troubleshooting

### Agent won't start

**Error:** `ModuleNotFoundError: No module named 'livekit'`

**Solution:**
```bash
cd clara-agent
pip install -r requirements.txt
```

---

### LiveKit connection failed

**Error:** `Failed to connect to LiveKit server`

**Solution:**
1. Check `LIVEKIT_URL` is correct
2. Verify API key and secret
3. Check network connectivity

---

### Redis connection refused

**Error:** `Connection refused: redis://localhost:6379`

**Solution:**
```bash
# Check if Redis is running
docker-compose ps

# Start Redis
docker-compose up -d redis

# Or use memory storage instead
CACHE_STORAGE_BACKEND=memory
```

---

### No data in vector database

**Error:** `No NFPA results found`

**Solution:**
Check that `data/chroma_db/` exists and contains vector data. The database should be pre-populated with NFPA standards and manuals.

---

## Performance

### Benchmarks

| Operation | Before Cache | With Cache | Improvement |
|-----------|--------------|------------|-------------|
| NFPA search | 2-3s | 100-200ms | **15x faster** |
| Manual lookup | 15-30s | <1s | **30x faster** |
| Equipment spec | 500ms | 50ms | **10x faster** |

### Optimization Tips

1. **Enable Redis caching** for 15x faster responses
2. **Use TimescaleDB** for advanced analytics
3. **Monitor cache hit rate** (target: >70%)
4. **Pre-populate vector DB** with common queries

---

## Contributing

### Adding New Features

1. Create feature branch
2. Implement with tests
3. Update documentation
4. Submit pull request

### Code Style

- Python: PEP 8
- Type hints required
- Docstrings for all functions
- Logging for debugging

### Architecture Principles

- **Lazy loading** for all services
- **Singleton pattern** for global instances
- **Graceful degradation** (fallbacks)
- **Error handling** with retries

---

## License

Copyright © 2024 Clara

---

## Support

For issues, questions, or feature requests:
- Check [DOCKER_SETUP.md](DOCKER_SETUP.md) for infrastructure help
- Review [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for config help
- Check logs: `docker-compose logs -f`
- Review error messages in agent output

---

## Architecture Highlights

### Multi-Layer Caching
```
Request → Memory (100ms) → Redis (200ms) → Database → Source
          ↓ 80% hit       ↓ 15% hit        ↓ 5% hit
```

### Intelligence Systems
- **Conversation Memory:** 20-turn history with entity tracking
- **User Preferences:** Skill-based responses (beginner/expert)
- **Pattern Learning:** Proactive suggestions from behavior
- **Analytics:** 12 event types, success tracking, tool metrics
- **CRM Integration:** 360° customer intelligence

### Voice Optimization
- **SSML formatting** for model numbers (spell out)
- **Abbreviation replacement** (ft → feet, psi → P-S-I)
- **Measurement emphasis** for clarity

---

**Clara Backend** - Built with ❤️ for fire safety technicians
