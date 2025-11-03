# Clara Backend API

Complete REST API backend for the Clara AI voice assistant system.

## Purpose

This API provides comprehensive backend services for the Clara ecosystem:
- **Jobs Management** - Job listing, scheduling, and details
- **LiveKit Integration** - Token generation and room management
- **Distance Calculations** - Google Maps integration for travel time
- **Daily Briefings** - Intelligent job summaries and recommendations
- **Real-time Communication** - WebRTC rooms and participant management

## Features

- **Jobs API** - Complete CRUD for jobs, equipment, and schedules
- **LiveKit Token Generation** - Secure token creation for voice sessions
- **LiveKit Room Management** - Create, list, update, and delete rooms
- **Google Maps Distance Matrix API** - Real-time distance and duration with traffic data
- **Haversine Fallback** - Offline distance calculation
- **PostgreSQL Backend** - Persistent storage for all data
- **CORS Enabled** - Mobile app and web client support
- **RESTful Design** - Clean, consistent API endpoints

## Setup

### 1. Install Dependencies

```bash
cd clara-server

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install using pyproject.toml (recommended)
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env.local` file in the `api` directory:

```bash
# Google Maps API (for distance calculations)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# LiveKit Configuration (for voice sessions)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Database (PostgreSQL)
DATABASE_URL=postgresql://clara:password@localhost:5432/clara
```

**Note:** Without Google Maps API key, the service falls back to Haversine distance calculation.

### 3. Run the API

```bash
cd clara-server
uvicorn main:app --reload --port 3000
```

Server runs on http://localhost:3000

**API Documentation:** http://localhost:3000/docs (Swagger UI)

## Endpoints

All endpoints return JSON. Full interactive documentation available at `/docs` (Swagger UI).

### Core Endpoints

#### GET /
Health check and endpoint list

**Response:**
```json
{
  "status": "ok",
  "service": "Clara Backend API",
  "version": "2.0.0",
  "endpoints": {
    "jobs": "/jobs",
    "job_by_id": "/jobs/{job_id}",
    "daily_brief": "/daily-brief",
    "health": "/health",
    "token": "/token",
    "rooms": "/rooms"
  },
  "distance_service": "google_maps" | "haversine"
}
```

### GET /health
API health status with jobs count and distance service status

**Response:**
```json
{
  "status": "healthy",
  "jobs_count": 3,
  "distance_service": "google_maps" | "haversine",
  "timestamp": "2025-10-30T..."
}
```

### GET /jobs
Get all jobs with optional distance calculation

**Query Parameters:**
- `latitude` (optional): User's current latitude
- `longitude` (optional): User's current longitude

**Response:**
```json
{
  "jobs": [
    {
      "id": "JOB-2024-1022-001",
      "title": "...",
      "location": {...},
      "distance_km": 5.2,
      "distance_text": "5.2 km",
      "duration_minutes": 12,
      "duration_text": "12 mins",
      "distance_method": "google_maps" | "haversine",
      ...
    }
  ],
  "count": 3,
  "sorted_by": "distance" | "time"
}
```

### GET /jobs/{job_id}
Get specific job by ID with optional distance calculation

**Query Parameters:**
- `latitude` (optional): User's current latitude
- `longitude` (optional): User's current longitude

**Response:**
```json
{
  "job": {
    "id": "JOB-2024-1022-001",
    "distance_km": 5.2,
    "distance_text": "5.2 km",
    "duration_minutes": 12,
    "duration_text": "12 mins",
    "distance_method": "google_maps",
    ...
  }
}
```

### GET /daily-brief
Get today's daily briefing with intelligent summaries

**Query Parameters:**
- `latitude` (optional): User's current latitude
- `longitude` (optional): User's current longitude

**Response:**
```json
{
  "date": "2025-10-30",
  "greeting": "Good morning! Here's your daily brief for Wednesday, October 30.",
  "summary": {
    "total_jobs": 3,
    "total_estimated_hours": "14h 0m",
    "earliest_job": "08:00 AM",
    "latest_job": "02:00 PM"
  },
  "jobs": [...],
  "tips": [
    "You have 2 high-priority jobs today.",
    "Long inspection day ahead (14h 0m total) - plan for breaks and hydration.",
    "Multiple sites today - verify you have all necessary equipment and tools."
  ],
  "historical_alerts": [
    "⚠ WeWork Eleven West: Zone 3 sprinkler head leak (repaired) (2024-04-15)",
    "⚠ Bharat Forge MIDC Unit 3: Extinguisher FE-38 (Bay C, near CNC-5) low pressure - recharged (2024-07-20)"
  ],
  "equipment_needed": [
    "Fire extinguisher pressure gauge and inspection tags",
    "Sprinkler system test equipment",
    "Fire pump flow test equipment"
  ]
}
```

### LiveKit Integration Endpoints

#### POST /token/job
Generate LiveKit token for a specific job session

**Request Body:**
```json
{
  "userId": "user123",
  "jobId": "JOB-2024-1022-001"
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "room": "job-JOB-2024-1022-001",
  "url": "wss://your-project.livekit.cloud"
}
```

#### POST /token
Generate LiveKit token for a custom room

**Request Body:**
```json
{
  "identity": "user123",
  "room": "custom-room"
}
```

#### GET /rooms
List all active LiveKit rooms

#### POST /rooms
Create a new LiveKit room

#### GET /rooms/{room_name}
Get details of a specific room

#### DELETE /rooms/{room_name}
Delete a room

#### GET /rooms/{room_name}/participants/{identity}
Get participant information

#### DELETE /rooms/{room_name}/participants/{identity}
Remove a participant from a room

#### POST /rooms/{room_name}/participants/{identity}/mute
Mute/unmute a participant

#### POST /rooms/{room_name}/data
Send data message to room participants

#### POST /webhook
LiveKit webhook handler for room events

## Data Storage

### PostgreSQL Database

Jobs, customers, and equipment are stored in PostgreSQL database. The database includes:
- **Customers** - CRM profiles with contracts and opportunities
- **Jobs** - Scheduled inspections with full details
- **Equipment** - Assets to inspect with specifications
- **Historical Data** - Past inspections and findings

### Demo Data

Sample jobs included:
- WeWork Eleven West (Semi-Annual Fire Safety Inspection)
- Bharat Forge MIDC Unit 3 (Quarterly Fire Safety Inspection)
- Mahindra Logistics Nigdi (Annual Sprinkler & Fire Pump Inspection)

Data can be seeded using `clara-agent/database/seed_demo_data.py`

## Distance Calculation

When latitude and longitude are provided, the API calculates:

### With Google Maps API Key:
- **Real road distance** via Google Maps Distance Matrix API
- **Real-time traffic data** for accurate duration estimates
- **Driving directions** optimized for current conditions

### Without Google Maps (Haversine fallback):
- **Straight-line distance** using Haversine formula
- **Estimated travel time** (50 km/h average + 5 min buffer)

Jobs are sorted by distance when location is provided.

## CORS

CORS is enabled for all origins (for development). Restrict in production.

## Architecture

### Backend Services

This FastAPI backend provides:
1. **Data Layer** - PostgreSQL database for jobs, customers, equipment
2. **LiveKit Integration** - Token generation and room management for voice sessions
3. **Distance Services** - Google Maps integration with Haversine fallback
4. **Business Logic** - Job scheduling, briefings, and recommendations

### Agent Intelligence

Clara's AI capabilities (equipment diagnosis, NFPA standards, troubleshooting, training) are handled by the **clara-agent** Python service running on LiveKit. The agent connects to this API for:
- Job data retrieval
- Customer information lookup
- Database queries

### Mobile App Integration

The React Native mobile app uses:
- **REST API** (this service) for jobs listing, daily briefings, and LiveKit tokens
- **LiveKit WebRTC** for real-time voice communication with the Clara agent
- **PostgreSQL Backend** via this API for persistent data storage
