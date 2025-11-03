"""
Clara Backend REST API
Complete backend service providing:
- Jobs management and scheduling
- Distance/travel time calculations (Google Maps)
- LiveKit token generation and room management
- Daily briefings and technician dashboard
- Real-time communication and webhooks
"""
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
import sys
import os
import uuid
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()  # Loads .env file if it exists
load_dotenv('.env.local')  # Also try .env.local for local overrides

# Import server-local services (all moved from agent to server)
from distance_service import initialize_distance_service, get_distance_service
from livekit_service import initialize_livekit_service, get_livekit_service
from context.user_preferences import get_preferences_manager
from knowledge.nfpa_service import get_knowledge_service
from caching.response_cache import get_cache
from jobs.service import get_job_service
from manufacturer.service import get_manufacturer_service
from nudges import Nudge, NudgeAction, NudgeType, NudgePriority
from jobs.data_capture import DataCaptureValidator, DataCaptureField

# Initialize services
distance_service = initialize_distance_service(os.getenv('GOOGLE_MAPS_API_KEY'))
livekit_service = initialize_livekit_service(
    os.getenv('LIVEKIT_URL'),
    os.getenv('LIVEKIT_API_KEY'),
    os.getenv('LIVEKIT_API_SECRET')
)
user_preferences = get_preferences_manager()
knowledge_service = get_knowledge_service()
response_cache = get_cache(redis_url=os.getenv('REDIS_URL'))
job_service = get_job_service()  # Real PostgreSQL job service
manufacturer_service = get_manufacturer_service()  # Manufacturer specifications service
data_validator = DataCaptureValidator()  # Data validation service

# Note: CRM, Analytics will be added as new server endpoints

# Temporary mock services until we implement proper server-side versions

class MockCRMService:
    def get_all_customers(self): return []
    def get_customer_by_id(self, customer_id): return None
    def get_customer_by_location(self, location): return None
    def get_all_contracts(self): return []
    def get_customer_contracts(self, customer_id): return []
    def get_all_opportunities(self): return []
    def get_customer_opportunities(self, customer_id): return []
    def get_customer_context(self, customer_id): return {}

class MockAnalyticsEngine:
    def track_event(self, **kwargs): pass
    def get_stats(self): return {"total_events": 0, "tool_calls": 0}

class MockDBHelper:
    def test_connection(self): return True

# Initialize mock services (job_service is real PostgreSQL now!)
crm_service = MockCRMService()
analytics_engine = MockAnalyticsEngine()
db_helper = MockDBHelper()

app = FastAPI(
    title="Clara Backend API",
    version="2.0.0",
    description="Complete backend service for Clara - AI voice assistant for fire safety technicians"
)

# CORS middleware for React Native app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event handler to initialize async services
@app.on_event("startup")
async def startup_event():
    """Initialize async services on application startup"""
    logger.info("Initializing async services...")

    # Initialize Redis cache connection
    try:
        await response_cache.initialize()
        logger.info("✓ Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"⚠ Redis cache initialization failed: {e}. Will use memory cache only.")


def job_to_dict(job):
    """Convert Job object to dictionary for API response"""
    return {
        "id": job.id,
        "title": job.title,
        "type": job.type.value if hasattr(job.type, 'value') else job.type,
        "scheduled_time": job.scheduled_time,
        "duration_estimate": job.duration_estimate,
        "status": job.status.value if hasattr(job.status, 'value') else job.status,
        "priority": job.priority,
        "assigned_technician": job.assigned_technician,
        "location": {
            "name": job.location.name,
            "address": job.location.address,
            "latitude": job.location.latitude,
            "longitude": job.location.longitude,
            "access_notes": job.location.access_notes,
        },
        "customer": {
            "name": job.customer.name,
            "contact": job.customer.contact,
            "email": job.customer.email if hasattr(job.customer, 'email') else None,
            "notes": job.customer.notes,
        },
        "equipment_to_inspect": job.equipment_to_inspect,
        "notes": job.notes,
        "checklist": [
            {
                "id": item.id,
                "category": item.category,
                "description": item.description,
                "completed": item.completed,
                "photo_required": item.photo_required,
                "notes": item.notes if hasattr(item, 'notes') else None,
            }
            for item in job.checklist
        ],
        "history": [
            {
                "date": h.date,
                "technician": h.technician,
                "findings": h.findings,
                "issues": h.issues,
                "photos": h.photos if hasattr(h, 'photos') else [],
            }
            for h in job.history
        ],
    }


def calculate_distance_and_duration(job, latitude: float, longitude: float) -> Dict:
    """Calculate distance and duration to job location using Google Maps or Haversine"""
    try:
        result = distance_service.calculate_distance(
            latitude, longitude,
            job.location.latitude, job.location.longitude
        )
        return result
    except Exception as e:
        print(f"Error calculating distance for job {job.id}: {e}")
        # Fallback to Haversine calculation
        from math import radians, sin, cos, sqrt, atan2

        lat1, lon1 = radians(latitude), radians(longitude)
        lat2, lon2 = radians(job.location.latitude), radians(job.location.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_km = 6371 * c
        duration_minutes = int((distance_km / 50) * 60) + 5  # Assume 50 km/h average speed

        return {
            "distance_km": round(distance_km, 1),
            "distance_text": f"{distance_km:.1f} km",
            "duration_minutes": duration_minutes,
            "duration_text": f"{duration_minutes} mins",
            "distance_method": "haversine",
        }


@app.get("/")
async def root():
    """API root - lists all available endpoint categories"""
    return {
        "status": "ok",
        "service": "Clara Backend API",
        "version": "2.0.0",
        "description": "Complete backend service for Clara AI assistant",
        "documentation": "/docs",
        "endpoint_categories": {
            "health": "/health",
            "jobs": {
                "all_jobs": "/jobs",
                "job_by_id": "/jobs/{job_id}",
                "daily_brief": "/daily-brief"
            },
            "crm": {
                "customers": "/api/crm/customers",
                "customer_by_id": "/api/crm/customers/{customer_id}",
                "customer_by_location": "/api/crm/customers/by-location/{location}",
                "contracts": "/api/crm/contracts",
                "customer_contracts": "/api/crm/contracts/customer/{customer_id}",
                "opportunities": "/api/crm/opportunities",
                "customer_opportunities": "/api/crm/opportunities/customer/{customer_id}",
                "customer_context": "/api/crm/context/{customer_id}"
            },
            "knowledge": {
                "search_nfpa": "/api/knowledge/search?query={query}",
                "search_hvac": "/api/knowledge/hvac?query={query}",
                "stats": "/api/knowledge/stats"
            },
            "analytics": {
                "track_event": "POST /api/analytics/event",
                "stats": "/api/analytics/stats"
            },
            "preferences": {
                "get": "/api/preferences/{user_id}",
                "update": "POST /api/preferences/{user_id}"
            },
            "cache": {
                "stats": "/api/cache/stats",
                "clear": "DELETE /api/cache/clear"
            },
            "livekit": {
                "job_token": "POST /token/job",
                "custom_token": "POST /token",
                "rooms": "/rooms",
                "room_details": "/rooms/{room_name}",
                "participants": "/rooms/{room_name}/participants/{identity}"
            },
            "distance": "/distance"
        },
        "infrastructure": {
            "distance_service": "google_maps" if distance_service.is_google_maps_available() else "haversine",
            "livekit": "enabled" if livekit_service else "disabled",
            "database": "postgresql",
            "cache": "redis",
            "knowledge_base": "chromadb"
        }
    }


@app.get("/health")
async def health():
    """Comprehensive health check for all backend services and infrastructure"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "infrastructure": {}
    }

    # Check Jobs Service
    try:
        jobs_count = len(job_service.get_all_jobs())
        health_status["services"]["jobs"] = {"status": "healthy", "count": jobs_count}
    except Exception as e:
        health_status["services"]["jobs"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Check CRM Service
    try:
        customers = crm_service.get_all_customers()
        health_status["services"]["crm"] = {"status": "healthy", "customers": len(customers)}
    except Exception as e:
        health_status["services"]["crm"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Knowledge Service
    try:
        stats = knowledge_service.get_stats()
        health_status["services"]["knowledge"] = {"status": "healthy", "stats": stats}
    except Exception as e:
        health_status["services"]["knowledge"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Distance Service
    health_status["services"]["distance"] = {
        "status": "healthy",
        "provider": "google_maps" if distance_service.is_google_maps_available() else "haversine"
    }

    # Check LiveKit Service
    health_status["services"]["livekit"] = {
        "status": "healthy" if livekit_service else "disabled",
        "configured": livekit_service is not None
    }

    # Check Database (PostgreSQL)
    try:
        if db_helper.test_connection():
            health_status["infrastructure"]["postgresql"] = {"status": "healthy"}
        else:
            health_status["infrastructure"]["postgresql"] = {"status": "unhealthy", "error": "Connection failed"}
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["infrastructure"]["postgresql"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Redis
    try:
        cache_stats = response_cache.stats()
        health_status["infrastructure"]["redis"] = {"status": "healthy", "cache_stats": cache_stats}
    except Exception as e:
        health_status["infrastructure"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Analytics Engine
    try:
        analytics_stats = analytics_engine.get_stats()
        health_status["services"]["analytics"] = {"status": "healthy", "stats": analytics_stats}
    except Exception as e:
        health_status["services"]["analytics"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status


@app.get("/distance")
async def calculate_distance(
    fromLat: float = Query(..., description="Starting latitude"),
    fromLon: float = Query(..., description="Starting longitude"),
    toLat: float = Query(..., description="Destination latitude"),
    toLon: float = Query(..., description="Destination longitude"),
):
    """
    Calculate distance and duration between two GPS coordinates

    Uses Google Maps Distance Matrix API if available, falls back to Haversine formula.
    Returns distance in kilometers and estimated travel time.
    """
    try:
        result = distance_service.calculate_distance(fromLat, fromLon, toLat, toLon)
        return {
            "success": True,
            "distance_km": result.get("distance_km"),
            "distance_text": result.get("distance_text"),
            "duration_minutes": result.get("duration_minutes"),
            "duration_text": result.get("duration_text"),
            "method": result.get("method"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate distance: {str(e)}")


@app.get("/jobs")
async def get_all_jobs(
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get all jobs with optional distance calculation

    If latitude and longitude are provided, calculates distance and duration
    to each job and sorts by distance.
    """
    # Real PostgreSQL service - returns dicts with distance already calculated
    jobs_data = job_service.get_all_jobs(latitude=latitude, longitude=longitude)

    # Sort by distance if location provided, otherwise by scheduled time
    if latitude is not None and longitude is not None:
        jobs_data.sort(key=lambda j: j.get("distance_km") or float('inf'))
        sorted_by = "distance"
    else:
        jobs_data.sort(key=lambda j: j.get("scheduled_time", ""))
        sorted_by = "time"

    return {
        "jobs": jobs_data,
        "count": len(jobs_data),
        "sorted_by": sorted_by,
    }


@app.get("/jobs/past-due")
async def get_past_due_jobs(
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get past due jobs (scheduled jobs with scheduled_time in the past)

    If latitude and longitude are provided, calculates distance and duration
    to each job and sorts by distance.
    """
    # Get only past due jobs
    past_due_data = job_service.get_past_due_jobs(latitude=latitude, longitude=longitude)

    # Sort by distance if location provided, otherwise by scheduled time
    if latitude is not None and longitude is not None:
        past_due_data.sort(key=lambda j: j.get("distance_km") or float('inf'))
        sorted_by = "distance"
    else:
        past_due_data.sort(key=lambda j: j.get("scheduled_time", ""))
        sorted_by = "time"

    return {
        "jobs": past_due_data,
        "count": len(past_due_data),
        "sorted_by": sorted_by,
    }


@app.get("/jobs/history")
async def get_job_history(
    limit: int = Query(50, description="Maximum number of jobs to return"),
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get completed jobs (job history)

    Returns completed jobs sorted by completion time (most recent first).
    Useful for viewing past inspections and accessing historical reports.
    """
    # Get completed jobs
    history_data = job_service.get_completed_jobs(limit=limit, latitude=latitude, longitude=longitude)

    return {
        "jobs": history_data,
        "count": len(history_data),
        "limit": limit,
    }


@app.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: str,
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get a specific job by ID with optional distance calculation
    """
    # Real PostgreSQL service - returns dict with distance already calculated
    job_dict = job_service.get_job_by_id(job_id, latitude=latitude, longitude=longitude)

    if not job_dict:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {"job": job_dict}


# ============================================================================
# Specifications API - Equipment manufacturer specifications
# ============================================================================

@app.get("/api/specifications/search")
async def search_specifications(
    query: str = Query(..., description="Search query (model number or description)"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    limit: int = Query(5, description="Maximum results to return", ge=1, le=20)
):
    """
    Search for equipment specifications using fuzzy matching

    Returns specifications sorted by relevance score
    """
    results = manufacturer_service.search_specifications(query, manufacturer, limit)

    return {
        "query": query,
        "manufacturer_filter": manufacturer,
        "count": len(results),
        "specifications": [spec.to_dict() for spec in results]
    }


@app.get("/api/specifications/{model_number}")
async def get_specification(
    model_number: str,
    manufacturer: Optional[str] = Query(None, description="Manufacturer name for disambiguation")
):
    """
    Get exact specification for a specific model number

    Returns complete factory specifications including:
    - Electrical specs (amp draw, voltage, capacitor)
    - Pressure specs (operating pressure, test pressure)
    - Temperature specs (operating range, delta)
    - Flow specs (GPM ratings)
    - Physical specs (filter size, belt size, dimensions)
    - Common issues and maintenance notes
    """
    spec = manufacturer_service.get_specification(model_number, manufacturer)

    if not spec:
        raise HTTPException(
            status_code=404,
            detail=f"Specification not found for model {model_number}" +
                   (f" from manufacturer {manufacturer}" if manufacturer else "")
        )

    return {
        "specification": spec.to_dict()
    }


@app.get("/api/specifications/manufacturer/{manufacturer}")
async def get_specs_by_manufacturer(manufacturer: str):
    """
    Get all specifications for a specific manufacturer

    Useful for browsing available equipment from a manufacturer
    """
    specs = manufacturer_service.get_specs_by_manufacturer(manufacturer)

    if not specs:
        raise HTTPException(
            status_code=404,
            detail=f"No specifications found for manufacturer: {manufacturer}"
        )

    return {
        "manufacturer": manufacturer,
        "count": len(specs),
        "specifications": [spec.to_dict() for spec in specs]
    }


# ============================================================================
# Nudges/Proactive Alerts API - Smart notifications and reminders
# ============================================================================

@app.get("/api/nudges")
async def get_nudges(
    job_id: Optional[str] = Query(None, description="Filter nudges for specific job"),
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get contextual proactive nudges based on current state

    Returns smart alerts including:
    - Jobs starting soon reminders
    - Proximity alerts when near job sites
    - Data capture reminders for incomplete readings
    - Safety and compliance alerts
    - Sales opportunity suggestions
    """
    now = datetime.now()
    nudges_list = []

    # Get all jobs for context
    all_jobs = job_service.get_all_jobs(latitude=latitude, longitude=longitude)

    # Filter to specific job if requested
    if job_id:
        all_jobs = [j for j in all_jobs if j.get("id") == job_id]

    # Generate contextual nudges based on job data
    for job in all_jobs:
        try:
            # Parse scheduled time
            scheduled_str = job.get("scheduled_time", "")
            if not scheduled_str:
                continue

            # Parse "2024-10-22 10:00 AM" format
            scheduled_time = datetime.strptime(scheduled_str, "%Y-%m-%d %I:%M %p")

            # 1. Job Starting Soon (within next hour)
            time_until = (scheduled_time - now).total_seconds() / 60  # minutes
            if 0 < time_until <= 60 and job.get("status") != "completed":
                nudge = Nudge(
                    id=f"starting_soon_{job['id']}_{int(now.timestamp())}",
                    type=NudgeType.JOB_STARTING_SOON,
                    priority=NudgePriority.HIGH,
                    message=f"{job['title']} starts in {int(time_until)} minutes. Ready to go?",
                    actions=[
                        NudgeAction(
                            label="View Job",
                            action="view_job",
                            data={"job_id": job["id"]}
                        ),
                        NudgeAction(
                            label="Get Directions",
                            action="get_directions",
                            data={"job_id": job["id"], "address": job.get("location", {}).get("address")}
                        ),
                        NudgeAction(
                            label="Dismiss",
                            action="dismiss"
                        )
                    ],
                    context={
                        "job_id": job["id"],
                        "job_title": job["title"],
                        "scheduled_time": scheduled_str,
                        "minutes_until": int(time_until)
                    },
                    expires_at=int((now + timedelta(hours=1)).timestamp())
                )
                nudges_list.append(nudge)

            # 2. Proximity Alert (within 2km if location provided)
            if latitude and longitude and "distance_km" in job:
                distance_km = job["distance_km"]
                if distance_km < 2.0 and job.get("status") != "completed":
                    nudge = Nudge(
                        id=f"proximity_{job['id']}_{int(now.timestamp())}",
                        type=NudgeType.PROXIMITY_TO_JOBSITE,
                        priority=NudgePriority.MEDIUM,
                        message=f"You're {distance_km:.1f}km from {job['title']}. Need a quick briefing?",
                        actions=[
                            NudgeAction(
                                label="Get Briefing",
                                action="get_job_briefing",
                                data={"job_id": job["id"]}
                            ),
                            NudgeAction(
                                label="View Equipment",
                                action="show_equipment_list",
                                data={"job_id": job["id"]}
                            ),
                            NudgeAction(
                                label="Dismiss",
                                action="dismiss"
                            )
                        ],
                        context={
                            "job_id": job["id"],
                            "job_title": job["title"],
                            "distance_km": distance_km,
                            "eta_minutes": job.get("duration_minutes", 0)
                        },
                        expires_at=int((now + timedelta(minutes=30)).timestamp())
                    )
                    nudges_list.append(nudge)

            # 3. Job Running Late (past scheduled time and not completed)
            if time_until < -15 and job.get("status") not in ["completed", "in_progress"]:
                nudge = Nudge(
                    id=f"running_late_{job['id']}_{int(now.timestamp())}",
                    type=NudgeType.JOB_RUNNING_LATE,
                    priority=NudgePriority.CRITICAL,
                    message=f"{job['title']} was scheduled for {scheduled_str}. Update status?",
                    actions=[
                        NudgeAction(
                            label="Mark In Progress",
                            action="update_job_status",
                            data={"job_id": job["id"], "status": "in_progress"}
                        ),
                        NudgeAction(
                            label="Mark Completed",
                            action="update_job_status",
                            data={"job_id": job["id"], "status": "completed"}
                        ),
                        NudgeAction(
                            label="Reschedule",
                            action="reschedule_job",
                            data={"job_id": job["id"]}
                        )
                    ],
                    context={
                        "job_id": job["id"],
                        "job_title": job["title"],
                        "scheduled_time": scheduled_str,
                        "minutes_late": int(-time_until)
                    },
                    expires_at=int((now + timedelta(hours=2)).timestamp())
                )
                nudges_list.append(nudge)

        except Exception as e:
            logger.error(f"Error generating nudges for job {job.get('id')}: {e}")
            continue

    # 4. End of Day Summary (after 4 PM)
    if now.hour >= 16 and len(all_jobs) > 0:
        completed_jobs = len([j for j in all_jobs if j.get("status") == "completed"])
        pending_jobs = len([j for j in all_jobs if j.get("status") != "completed"])

        nudge = Nudge(
            id=f"end_of_day_{now.strftime('%Y%m%d')}",
            type=NudgeType.END_OF_DAY_SUMMARY,
            priority=NudgePriority.LOW,
            message=f"Daily summary: {completed_jobs} jobs completed, {pending_jobs} pending. Ready to wrap up?",
            actions=[
                NudgeAction(
                    label="View Summary",
                    action="view_daily_summary"
                ),
                NudgeAction(
                    label="Complete Remaining",
                    action="show_pending_jobs"
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "completed_count": completed_jobs,
                "pending_count": pending_jobs,
                "date": now.strftime("%Y-%m-%d")
            },
            expires_at=int((now + timedelta(hours=3)).timestamp())
        )
        nudges_list.append(nudge)

    # Convert nudges to dicts for JSON response
    nudges_response = []
    for nudge in nudges_list:
        nudges_response.append({
            "id": nudge.id,
            "type": nudge.type.value,
            "priority": nudge.priority.value,
            "message": nudge.message,
            "actions": [
                {
                    "label": action.label,
                    "action": action.action,
                    "data": action.data
                }
                for action in nudge.actions
            ],
            "context": nudge.context,
            "expires_at": nudge.expires_at,
            "created_at": nudge.created_at
        })

    return {
        "nudges": nudges_response,
        "count": len(nudges_response),
        "generated_at": int(now.timestamp())
    }


# ============================================================================
# Validation API - Equipment data capture validation
# ============================================================================

@app.post("/api/validation/equipment")
async def validate_equipment(equipment: Dict = Body(...)):
    """
    Validate equipment data completeness

    Checks if all required fields are captured for the equipment type.

    Request body:
    ```json
    {
        "name": "HVAC Unit #1",
        "type": "hvac",
        "manufacturer": "Carrier",
        "model_number": "50A4-030",
        "serial_number": "ABC123",
        "filter_size": "24x24x4",
        "location": "Rooftop Unit 1",
        "photo": "photo_url_here"
    }
    ```

    Returns:
    - is_complete: Whether all required fields are captured
    - missing_fields: List of missing field names
    - captured_fields: List of captured field names
    - completion_percentage: Percentage of completion (0-100)
    - prompt_message: Friendly message for technician
    """
    validation_result = data_validator.check_equipment_data_completeness(equipment)

    return {
        "equipment_name": equipment.get("name", "Unknown"),
        "equipment_type": equipment.get("type", "default"),
        **validation_result
    }


@app.post("/api/validation/job")
async def validate_job(equipment_list: List[Dict] = Body(...)):
    """
    Validate data completeness for all equipment in a job

    Checks all equipment and returns summary of what's missing.

    Request body:
    ```json
    [
        {
            "name": "HVAC Unit #1",
            "type": "hvac",
            "manufacturer": "Carrier",
            "model_number": "50A4-030",
            ...
        },
        {
            "name": "Fire Pump",
            "type": "fire_pump",
            ...
        }
    ]
    ```

    Returns:
    - overall_complete: Whether all equipment has complete data
    - total_equipment: Total number of equipment
    - complete_equipment: Number of equipment with complete data
    - incomplete_equipment: List of incomplete equipment with details
    - summary_message: Friendly summary message for technician
    """
    validation_result = data_validator.check_job_data_completeness(equipment_list)

    return validation_result


@app.get("/api/validation/requirements/{equipment_type}")
async def get_validation_requirements(equipment_type: str):
    """
    Get required fields for a specific equipment type

    Returns list of field names that must be captured for this equipment type.

    Supported equipment types:
    - fire_pump
    - backflow_preventer
    - sprinkler_head
    - fire_extinguisher
    - hvac
    - hvac_with_belt
    - default (for unknown types)
    """
    # Normalize equipment type
    normalized_type = equipment_type.lower().replace(' ', '_').replace('-', '_')

    # Get required fields
    required_fields = data_validator.REQUIRED_FIELDS_BY_TYPE.get(
        normalized_type,
        data_validator.REQUIRED_FIELDS_BY_TYPE.get('default')
    )

    if not required_fields:
        raise HTTPException(
            status_code=404,
            detail=f"No validation requirements found for equipment type: {equipment_type}"
        )

    # Convert to list of field names
    field_names = [field.value for field in required_fields]

    return {
        "equipment_type": equipment_type,
        "normalized_type": normalized_type,
        "required_fields": field_names,
        "field_count": len(field_names),
        "description": f"Required data fields for {equipment_type} equipment"
    }


@app.get("/api/validation/requirements")
async def get_all_validation_requirements():
    """
    Get required fields for all equipment types

    Returns a dictionary of all equipment types and their required fields.
    """
    all_requirements = {}

    for equipment_type, fields in data_validator.REQUIRED_FIELDS_BY_TYPE.items():
        all_requirements[equipment_type] = {
            "required_fields": [field.value for field in fields],
            "field_count": len(fields)
        }

    return {
        "equipment_types": list(all_requirements.keys()),
        "requirements": all_requirements,
        "total_types": len(all_requirements)
    }


@app.get("/daily-brief")
async def get_daily_brief(
    latitude: Optional[float] = Query(None, description="User's current latitude"),
    longitude: Optional[float] = Query(None, description="User's current longitude"),
):
    """
    Get today's daily briefing with jobs, summary, and helpful tips

    Provides:
    - Greeting based on time of day
    - Summary statistics (total jobs, estimated hours, earliest/latest times)
    - Today's jobs with optional distance calculation
    - Helpful tips based on schedule
    - Historical alerts from previous inspections
    - Equipment needed across all jobs
    - Pre-job actions (notifications, coordination)
    - Travel plan with route summary (if location provided)
    - Time management suggestions
    """
    today = date.today()
    today_str = today.isoformat()

    # Get all jobs (already returns dictionaries with distance if lat/lon provided)
    all_jobs = job_service.get_all_jobs(latitude=latitude, longitude=longitude)

    # Filter jobs scheduled for today
    todays_jobs = []
    for job in all_jobs:
        try:
            # Parse scheduled_time (format: "2024-10-22 10:00 AM" or "2025-10-30 10:00 AM")
            scheduled_time = job.get('scheduled_time', '')
            if not scheduled_time:
                continue
            job_date_str = scheduled_time.split()[0]
            if job_date_str == today_str:
                todays_jobs.append(job)
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing job {job.get('id', 'unknown')} scheduled_time: {e}")

    # Jobs are already dictionaries from job_service
    jobs_with_distance = todays_jobs

    # Sort by scheduled time (parse AM/PM correctly)
    def parse_time(time_str: str) -> int:
        """Parse time string to minutes since midnight"""
        try:
            parts = time_str.split()
            time = parts[1]  # "08:00"
            ampm = parts[2]  # "AM" or "PM"
            hour_str, minute_str = time.split(':')
            hour = int(hour_str)
            minute = int(minute_str)

            # Convert to 24-hour format
            if ampm == 'PM' and hour != 12:
                hour += 12
            if ampm == 'AM' and hour == 12:
                hour = 0

            return hour * 60 + minute
        except:
            return 0

    jobs_with_distance.sort(key=lambda j: parse_time(j.get("scheduled_time", "")))

    # Calculate summary statistics
    total_jobs = len(jobs_with_distance)

    # Calculate total estimated hours
    total_minutes = 0
    for job in jobs_with_distance:
        duration_str = job.get("duration_estimate") or ""
        # Parse duration estimate (e.g., "3-4 hours" -> average 3.5 hours)
        import re
        if not duration_str:
            continue
        match = re.search(r'(\d+)-?(\d+)?\s*hours?', duration_str, re.IGNORECASE)
        if match:
            min_hours = int(match.group(1))
            max_hours = int(match.group(2)) if match.group(2) else min_hours
            total_minutes += ((min_hours + max_hours) / 2) * 60

    total_hours = int(total_minutes // 60)
    remaining_minutes = int(total_minutes % 60)
    total_estimated_time = f"{total_hours}h {remaining_minutes}m" if remaining_minutes > 0 else f"{total_hours}h"

    # Get earliest and latest job times
    earliest_job = (
        " ".join(jobs_with_distance[0]["scheduled_time"].split()[1:])
        if jobs_with_distance else "N/A"
    )
    latest_job = (
        " ".join(jobs_with_distance[-1]["scheduled_time"].split()[1:])
        if jobs_with_distance else "N/A"
    )

    # Generate greeting based on time of day
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Generate helpful tips
    tips = []
    if total_jobs == 0:
        tips.append("No jobs scheduled for today. Use this time to review NFPA standards or prepare equipment.")
    else:
        # High priority jobs
        high_priority_count = sum(1 for j in jobs_with_distance if j.get("priority") == "high")
        if high_priority_count > 0:
            tips.append(f"You have {high_priority_count} high-priority job{'s' if high_priority_count > 1 else ''} today.")

        # Long duration jobs
        if total_hours >= 6:
            tips.append(f"Long inspection day ahead ({total_estimated_time} total) - plan for breaks and hydration.")

        # Multiple locations
        if total_jobs > 1:
            tips.append("Multiple sites today - verify you have all necessary equipment and tools.")

    # Extract historical alerts
    historical_alerts = []
    for job in jobs_with_distance:
        history = job.get("history")
        if history and isinstance(history, list) and len(history) > 0:
            latest_history = history[0]
            # Check if latest_history is a dict and has issues
            if isinstance(latest_history, dict) and latest_history.get("issues"):
                for issue in latest_history["issues"][:2]:  # Top 2 issues
                    historical_alerts.append(
                        f"⚠ {job.get('location', {}).get('name', 'Unknown location')}: {issue} ({latest_history.get('date', 'Unknown date')})"
                    )

    # Aggregate equipment needed
    equipment_set = set()
    for job in jobs_with_distance:
        for item in job.get("equipment_to_inspect", []):
            # Handle both string and dict items
            item_name = item if isinstance(item, str) else (item.get("name", "") if isinstance(item, dict) else "")
            if not item_name:
                continue
            item_lower = item_name.lower()
            if "extinguisher" in item_lower:
                equipment_set.add("Fire extinguisher pressure gauge and inspection tags")
            if "sprinkler" in item_lower:
                equipment_set.add("Sprinkler system test equipment")
            if "pump" in item_lower:
                equipment_set.add("Fire pump flow test equipment")
            if "smoke detector" in item_lower:
                equipment_set.add("Canned smoke tester (for smoke detectors)")
            if "backflow" in item_lower:
                equipment_set.add("Backflow preventer test kit")

    equipment_needed = list(equipment_set) if equipment_set else None

    brief = {
        "date": today_str,
        "greeting": f"{greeting}! Here's your daily brief for {today.strftime('%A, %B %d')}.",
        "summary": {
            "total_jobs": total_jobs,
            "total_estimated_hours": total_estimated_time,
            "earliest_job": earliest_job,
            "latest_job": latest_job,
        },
        "jobs": jobs_with_distance,
        "tips": tips if tips else None,
        "historical_alerts": historical_alerts if historical_alerts else None,
        "equipment_needed": equipment_needed,
    }

    return brief


# ==================== LIVEKIT TOKEN ENDPOINTS ====================

@app.post("/token/job")
async def create_job_token(
    job_id: str = Body(...),
    participant_name: Optional[str] = Body(None),
    participant_identity: Optional[str] = Body(None),
    participant_attributes: Optional[Dict[str, str]] = Body(None),
):
    """
    Job-specific token endpoint - creates room with job context
    Room name = job ID (e.g., "JOB-2024-1022-001")
    """
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        # Create room with job ID as name
        room_name = job_id
        await livekit_service.create_room(
            name=room_name,
            empty_timeout=600,  # 10 minutes for job sessions
            max_participants=10,
            metadata=f'{{"job_id": "{job_id}"}}',
        )
    except Exception as e:
        # Room may already exist, that's okay
        print(f"Room {room_name} may already exist: {e}")

    # Generate token
    token = livekit_service.create_token(
        room_name=room_name,
        participant_name=participant_name or f"user-{uuid.uuid4()}",
        participant_identity=participant_identity,
        participant_attributes=participant_attributes,
    )

    return {
        "server_url": livekit_service.url,
        "token": token,
        "room": room_name,
        "job_id": job_id,
        "identity": participant_identity or participant_name or f"user-{uuid.uuid4()}",
    }


@app.post("/token")
async def create_token(
    room_name: Optional[str] = Body(None),
    participant_name: Optional[str] = Body(None),
    participant_identity: Optional[str] = Body(None),
    participant_metadata: Optional[str] = Body(None),
    participant_attributes: Optional[Dict[str, str]] = Body(None),
    permissions: Optional[Dict] = Body(None),
    ttl: Optional[str] = Body("10m"),
):
    """Generate access token with granular permissions"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    room = room_name or f"room-{uuid.uuid4()}"
    participant = participant_name or f"user-{uuid.uuid4()}"

    token = livekit_service.create_token(
        room_name=room,
        participant_name=participant,
        participant_identity=participant_identity,
        participant_metadata=participant_metadata,
        participant_attributes=participant_attributes,
        permissions=permissions,
        ttl=ttl,
    )

    return {
        "server_url": livekit_service.url,
        "token": token,
        "room": room,
        "identity": participant_identity or participant,
    }


@app.post("/createToken")
async def create_token_legacy(
    roomName: str = Body(...),
    participantName: Optional[str] = Body(None),
):
    """Legacy token endpoint for backwards compatibility"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    participant = participantName or f"user-{uuid.uuid4()}"

    token = livekit_service.create_token(
        room_name=roomName,
        participant_name=participant,
    )

    return {
        "server_url": livekit_service.url,
        "participant_token": token,
    }


# ==================== ROOM MANAGEMENT ENDPOINTS ====================

@app.post("/rooms")
async def create_room(
    name: Optional[str] = Body(None),
    emptyTimeout: Optional[int] = Body(300),
    maxParticipants: Optional[int] = Body(100),
    metadata: Optional[str] = Body(""),
):
    """Create a new room"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        room = await livekit_service.create_room(
            name=name,
            empty_timeout=emptyTimeout,
            max_participants=maxParticipants,
            metadata=metadata,
        )
        return {"room": room}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")


@app.get("/rooms")
async def list_rooms():
    """List all active rooms"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        rooms = await livekit_service.list_rooms()
        return {"rooms": rooms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list rooms: {str(e)}")


@app.get("/rooms/{room_name}")
async def get_room(room_name: str):
    """Get room details & participants"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        room = await livekit_service.get_room(room_name)
        return room
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Room not found: {str(e)}")


@app.delete("/rooms/{room_name}")
async def delete_room(room_name: str):
    """Delete a room"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        result = await livekit_service.delete_room(room_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")


@app.patch("/rooms/{room_name}")
async def update_room_metadata(
    room_name: str,
    metadata: str = Body(...),
):
    """Update room metadata"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        result = await livekit_service.update_room_metadata(room_name, metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update room: {str(e)}")


# ==================== PARTICIPANT MANAGEMENT ENDPOINTS ====================

@app.get("/rooms/{room_name}/participants/{identity}")
async def get_participant(room_name: str, identity: str):
    """Get participant info"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        participant = await livekit_service.get_participant(room_name, identity)
        return {"participant": participant}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Participant not found: {str(e)}")


@app.delete("/rooms/{room_name}/participants/{identity}")
async def remove_participant(room_name: str, identity: str):
    """Remove participant from room"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        result = await livekit_service.remove_participant(room_name, identity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove participant: {str(e)}")


@app.post("/rooms/{room_name}/participants/{identity}/mute")
async def mute_participant_track(
    room_name: str,
    identity: str,
    trackSid: str = Body(...),
    muted: bool = Body(True),
):
    """Mute/unmute participant track"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        result = await livekit_service.mute_published_track(room_name, identity, trackSid, muted)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mute track: {str(e)}")


@app.patch("/rooms/{room_name}/participants/{identity}")
async def update_participant(
    room_name: str,
    identity: str,
    metadata: Optional[str] = Body(None),
    name: Optional[str] = Body(None),
    attributes: Optional[Dict[str, str]] = Body(None),
):
    """Update participant metadata"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        result = await livekit_service.update_participant(room_name, identity, metadata, name, attributes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update participant: {str(e)}")


@app.post("/rooms/{room_name}/data")
async def send_room_data(
    room_name: str,
    data: str = Body(...),
    destinationIdentities: Optional[List[str]] = Body(None),
    topic: Optional[str] = Body(None),
):
    """Send data message to room or specific participants"""
    if not livekit_service:
        raise HTTPException(status_code=503, detail="LiveKit service not configured")

    try:
        data_bytes = data.encode('utf-8')
        result = await livekit_service.send_data(room_name, data_bytes, destinationIdentities, topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send data: {str(e)}")


# ==================== WEBHOOK ENDPOINT ====================

@app.post("/webhook")
async def webhook(event: Dict = Body(...)):
    """Webhook endpoint for LiveKit events"""
    try:
        event_type = event.get("event")
        room_name = event.get("room", {}).get("name")
        participant_identity = event.get("participant", {}).get("identity")

        print(f"Webhook received: {event_type}, room: {room_name}, participant: {participant_identity}")

        # Process different event types
        if event_type == "room_started":
            print(f"Room {room_name} started")
        elif event_type == "room_finished":
            print(f"Room {room_name} finished")
        elif event_type == "participant_joined":
            print(f"Participant {participant_identity} joined {room_name}")
        elif event_type == "participant_left":
            print(f"Participant {participant_identity} left {room_name}")
        elif event_type == "track_published":
            print(f"Track published in {room_name}")
        elif event_type == "track_unpublished":
            print(f"Track unpublished in {room_name}")
        else:
            print(f"Unknown event type: {event_type}")

        return {"message": "Webhook processed"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


# ============================================================================
# CRM Endpoints - Customer Relationship Management
# ============================================================================

@app.get("/api/crm/customers")
async def get_customers():
    """Get all customers with full profiles"""
    try:
        customers = crm_service.get_all_customers()
        return {
            "customers": [
                {
                    "customer_id": c.customer_id,
                    "name": c.name,
                    "company_type": c.company_type,
                    "location": c.location,
                    "primary_contact": c.primary_contact,
                    "phone": c.phone,
                    "email": c.email,
                    "industry": c.industry,
                    "building_type": c.building_type,
                    "square_footage": c.square_footage,
                    "customer_since": c.customer_since,
                    "lifetime_value": c.lifetime_value,
                    "annual_spend": c.annual_spend,
                    "total_equipment_count": c.total_equipment_count,
                    "equipment_types": c.equipment_types,
                    "total_service_calls": c.total_service_calls,
                    "last_service_date": c.last_service_date,
                    "satisfaction_score": c.satisfaction_score,
                    "special_requirements": c.special_requirements,
                    "preferred_service_times": c.preferred_service_times,
                    "notes": c.notes,
                }
                for c in customers
            ],
            "count": len(customers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customers: {str(e)}")


@app.get("/api/crm/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get specific customer by ID"""
    try:
        customer = crm_service.get_customer_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "company_type": customer.company_type,
            "location": customer.location,
            "primary_contact": customer.primary_contact,
            "phone": customer.phone,
            "email": customer.email,
            "industry": customer.industry,
            "building_type": customer.building_type,
            "square_footage": customer.square_footage,
            "customer_since": customer.customer_since,
            "lifetime_value": customer.lifetime_value,
            "annual_spend": customer.annual_spend,
            "total_equipment_count": customer.total_equipment_count,
            "equipment_types": customer.equipment_types,
            "total_service_calls": customer.total_service_calls,
            "last_service_date": customer.last_service_date,
            "satisfaction_score": customer.satisfaction_score,
            "special_requirements": customer.special_requirements,
            "preferred_service_times": customer.preferred_service_times,
            "notes": customer.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@app.get("/api/crm/customers/by-location/{location}")
async def get_customer_by_location(location: str):
    """Get customer by location name"""
    try:
        customer = crm_service.get_customer_by_location(location)
        if not customer:
            raise HTTPException(status_code=404, detail=f"No customer found at location: {location}")

        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "location": customer.location,
            "primary_contact": customer.primary_contact,
            "phone": customer.phone,
            "email": customer.email,
            "lifetime_value": customer.lifetime_value,
            "annual_spend": customer.annual_spend,
            "satisfaction_score": customer.satisfaction_score,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer by location: {str(e)}")


@app.get("/api/crm/contracts")
async def get_contracts():
    """Get all contracts"""
    try:
        contracts = crm_service.get_all_contracts()
        return {
            "contracts": [
                {
                    "contract_id": c.contract_id,
                    "customer_id": c.customer_id,
                    "customer_name": c.customer_name,
                    "contract_type": c.contract_type,
                    "status": c.status,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "annual_value": c.annual_value,
                    "covered_equipment": c.covered_equipment,
                    "service_frequency": c.service_frequency,
                    "response_time_sla": c.response_time_sla,
                    "renewal_date": c.renewal_date,
                    "auto_renewal": c.auto_renewal,
                    "contract_manager": c.contract_manager,
                }
                for c in contracts
            ],
            "count": len(contracts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contracts: {str(e)}")


@app.get("/api/crm/contracts/customer/{customer_id}")
async def get_customer_contracts(customer_id: str):
    """Get all contracts for a specific customer"""
    try:
        contracts = crm_service.get_customer_contracts(customer_id)
        return {
            "customer_id": customer_id,
            "contracts": [
                {
                    "contract_id": c.contract_id,
                    "contract_type": c.contract_type,
                    "status": c.status,
                    "start_date": c.start_date,
                    "end_date": c.end_date,
                    "annual_value": c.annual_value,
                    "service_frequency": c.service_frequency,
                }
                for c in contracts
            ],
            "count": len(contracts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer contracts: {str(e)}")


@app.get("/api/crm/opportunities")
async def get_opportunities():
    """Get all sales opportunities"""
    try:
        opportunities = crm_service.get_all_opportunities()
        return {
            "opportunities": [
                {
                    "opportunity_id": o.opportunity_id,
                    "customer_id": o.customer_id,
                    "customer_name": o.customer_name,
                    "opportunity_type": o.opportunity_type,
                    "title": o.title,
                    "description": o.description,
                    "estimated_value": o.estimated_value,
                    "probability": o.probability,
                    "stage": o.stage,
                    "created_date": o.created_date,
                    "expected_close_date": o.expected_close_date,
                    "decision_maker": o.decision_maker,
                    "next_action": o.next_action,
                    "next_action_date": o.next_action_date,
                    "competitor_info": o.competitor_info,
                }
                for o in opportunities
            ],
            "count": len(opportunities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get opportunities: {str(e)}")


@app.get("/api/crm/opportunities/customer/{customer_id}")
async def get_customer_opportunities(customer_id: str):
    """Get all sales opportunities for a specific customer"""
    try:
        opportunities = crm_service.get_customer_opportunities(customer_id)
        return {
            "customer_id": customer_id,
            "opportunities": [
                {
                    "opportunity_id": o.opportunity_id,
                    "opportunity_type": o.opportunity_type,
                    "title": o.title,
                    "estimated_value": o.estimated_value,
                    "probability": o.probability,
                    "stage": o.stage,
                    "expected_close_date": o.expected_close_date,
                }
                for o in opportunities
            ],
            "count": len(opportunities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer opportunities: {str(e)}")


@app.get("/api/crm/context/{customer_id}")
async def get_customer_context(customer_id: str):
    """Get complete customer context (profile + contracts + opportunities)"""
    try:
        context = crm_service.get_customer_context(customer_id)
        if not context:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

        return {
            "customer_id": customer_id,
            "profile": {
                "name": context["profile"]["name"],
                "location": context["profile"]["location"],
                "lifetime_value": context["profile"]["lifetime_value"],
                "annual_spend": context["profile"]["annual_spend"],
                "satisfaction_score": context["profile"]["satisfaction_score"],
            },
            "active_contracts": context["active_contracts"],
            "opportunities": context["opportunities"],
            "summary": context["summary"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer context: {str(e)}")


# ============================================================================
# Knowledge Base Endpoints - NFPA Standards & Manuals
# ============================================================================

@app.get("/api/knowledge/search")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(3, description="Number of results to return", ge=1, le=10)
):
    """Search NFPA standards and fire safety knowledge base"""
    try:
        results = knowledge_service.search_nfpa_standards(query, n_results=n_results)
        return {
            "query": query,
            "results": results,
            "count": n_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")


@app.get("/api/knowledge/hvac")
async def search_hvac_knowledge(
    query: str = Query(..., description="HVAC search query"),
    n_results: int = Query(3, description="Number of results", ge=1, le=10)
):
    """Search HVAC technical knowledge and troubleshooting"""
    try:
        results = knowledge_service.search_hvac_knowledge(query, n_results=n_results)
        return {
            "query": query,
            "results": results,
            "count": n_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HVAC knowledge search failed: {str(e)}")


@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        stats = knowledge_service.get_stats()
        return {
            "status": "ok",
            "collections": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge stats: {str(e)}")


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.post("/api/analytics/event")
async def track_event(event_data: Dict):
    """Track analytics event"""
    try:
        analytics_engine.track_event(
            event_type=event_data.get("event_type"),
            user_id=event_data.get("user_id"),
            metadata=event_data.get("metadata", {})
        )
        return {"status": "ok", "message": "Event tracked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track event: {str(e)}")


@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get analytics statistics"""
    try:
        stats = analytics_engine.get_stats()
        return {
            "status": "ok",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics stats: {str(e)}")


# ============================================================================
# User Preferences Endpoints
# ============================================================================

@app.get("/api/preferences/{user_id}")
async def get_user_prefs(user_id: str):
    """Get user preferences"""
    try:
        prefs = user_preferences.get_preferences(user_id)
        return {
            "user_id": user_id,
            "preferences": prefs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@app.post("/api/preferences/{user_id}")
async def update_user_prefs(user_id: str, preferences: Dict):
    """Update user preferences"""
    try:
        user_preferences.set_preferences(user_id, preferences)
        return {
            "status": "ok",
            "message": "Preferences updated",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


# ============================================================================
# Cache Management Endpoints
# ============================================================================

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = response_cache.stats()
        return {
            "status": "ok",
            "cache_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@app.delete("/api/cache/clear")
async def clear_cache():
    """Clear all caches"""
    try:
        response_cache.clear()
        return {
            "status": "ok",
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting Clara Backend API on http://localhost:3000")
    print("=" * 60)
    print("Services initialized:")
    print(f"  - Jobs Service: {len(job_service.get_all_jobs())} jobs")
    print(f"  - CRM Service: {len(crm_service.get_all_customers())} customers")
    print(f"  - Distance Service: {'Google Maps' if distance_service.is_google_maps_available() else 'Haversine'}")
    print(f"  - LiveKit Service: {'Enabled' if livekit_service else 'Disabled'}")
    print(f"  - Knowledge Base: {knowledge_service.get_stats()}")
    print(f"  - PostgreSQL: {'Connected' if db_helper.test_connection() else 'Not connected'}")
    print("=" * 60)
    print("API Documentation: http://localhost:3000/docs")
    uvicorn.run(app, host="0.0.0.0", port=3000)
