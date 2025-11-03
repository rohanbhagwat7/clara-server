# Clara Server

**REST API and Infrastructure for Clara Voice Assistant**

Clara Server provides the REST API, database infrastructure, and job management system for Clara, an AI-powered voice assistant for fire life safety technicians.

---

## Overview

Clara Server handles:
- 🔌 **REST API** for job management and LiveKit integration
- 🗄️ **Database infrastructure** (PostgreSQL, TimescaleDB, Redis)
- 📊 **Analytics tracking** and performance monitoring
- 🧠 **Customer intelligence** and CRM integration
- 🎯 **Proactive nudges** and sales opportunity detection

---

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager
- Docker & Docker Compose (for infrastructure)

### 1. Start Infrastructure

```bash
docker-compose up -d                  # Start services
docker-compose ps                     # Verify running
make init-schemas                     # Initialize DB (first time)
```

### 2. Configure Environment

```bash
cp .env.example .env.local
# Edit .env.local with your DATABASE_URL, REDIS_URL, LIVEKIT credentials, etc.
```

### 3. Start Server

```bash
.\start_server.bat                    # Windows
# OR
uv run python -m uvicorn main:app --port 3000 --host 0.0.0.0 --reload
```

Server: `http://localhost:3000`  
API Docs: `http://localhost:3000/docs`

---

## Related Repositories

| Repository | Purpose |
|------------|---------|
| **[clara-server](https://github.com/rohanbhagwat7/clara-server)** | REST API & Infrastructure (this repo) |
| **[clara-agent](https://github.com/rohanbhagwat7/clara-agent)** | AI Voice Agent with Claude |
| **[clara-react-native](https://github.com/rohanbhagwat7/clara-react-native)** | Mobile Application |

---

## Documentation

See `docs/` directory for detailed documentation:
- `ARCHITECTURE.md` - System architecture
- `DATABASE_SCHEMA.md` - Database schema
- `DOCKER_SETUP.md` - Infrastructure setup
- `QUICK_START.md` - Getting started

---

**Version**: v3.0.0
