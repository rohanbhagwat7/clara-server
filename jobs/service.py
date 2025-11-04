"""
Real Job Service - Connects to PostgreSQL
Replaces mock data with actual database queries
"""
import psycopg
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def format_historical_inspections(inspections: List[Dict[str, Any]]) -> str:
    """
    Format historical inspections array into a readable string

    Args:
        inspections: List of inspection dictionaries with date, technician, findings, issues

    Returns:
        Formatted string for display in frontend
    """
    if not inspections:
        return ""

    lines = []
    lines.append(f"Historical Inspections ({len(inspections)} records):\n")

    for inspection in inspections:
        date = inspection.get('date', 'Unknown date')
        technician = inspection.get('technician', 'Unknown technician')
        findings = inspection.get('findings', 'No findings recorded')
        issues = inspection.get('issues', [])

        lines.append(f"• {date} (by {technician})")
        lines.append(f"  Findings: {findings}")

        if issues:
            lines.append(f"  Issues found:")
            for issue in issues:
                lines.append(f"    - {issue}")

        lines.append("")  # Blank line between inspections

    return "\n".join(lines)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://clara:clara_dev_password@localhost:5432/clara")


class JobService:
    """Service for managing jobs with PostgreSQL backend"""

    def __init__(self):
        self.db_url = DATABASE_URL
        logger.info(f"JobService initialized with database")

    def _get_connection(self):
        """Get database connection"""
        return psycopg.connect(self.db_url)

    def get_all_jobs(self, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from database

        Args:
            latitude: User's latitude for distance calculation
            longitude: User's longitude for distance calculation

        Returns:
            List of job dictionaries with all details
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Fetch jobs with equipment and checklist items
                    query = """
                        SELECT
                            j.job_id,
                            j.title,
                            j.job_type,
                            j.status,
                            j.scheduled_time,
                            j.location_name,
                            j.location_address,
                            j.location_latitude,
                            j.location_longitude,
                            j.access_notes,
                            j.customer_name,
                            j.customer_contact,
                            j.customer_email,
                            j.customer_notes,
                            j.historical_inspections,
                            COALESCE(
                                json_agg(
                                    DISTINCT jsonb_build_object(
                                        'equipment_id', e.equipment_id,
                                        'name', e.name,
                                        'manufacturer', e.manufacturer,
                                        'model', e.model,
                                        'serial_number', e.serial_number
                                    )
                                ) FILTER (WHERE e.equipment_id IS NOT NULL),
                                '[]'::json
                            ) as equipment,
                            COALESCE(
                                (
                                    SELECT json_agg(
                                        json_build_object(
                                            'id', ci.checklist_id,
                                            'description', ci.description,
                                            'category', ci.category,
                                            'photo_required', ci.photo_required,
                                            'completed', ci.completed,
                                            'notes', ci.notes,
                                            'photo_url', ci.photo_url,
                                            'completed_at', ci.completed_at
                                        )
                                        ORDER BY ci.item_id
                                    )
                                    FROM checklist_items ci
                                    WHERE ci.job_id = j.job_id
                                ),
                                '[]'::json
                            ) as checklist
                        FROM jobs j
                        LEFT JOIN job_equipment je ON j.job_id = je.job_id
                        LEFT JOIN equipment e ON je.equipment_id = e.equipment_id
                        GROUP BY j.job_id
                        ORDER BY j.scheduled_time ASC
                    """

                    cur.execute(query)
                    rows = cur.fetchall()

                    jobs = []
                    for row in rows:
                        # Parse equipment list
                        equipment_list = row[15] if row[15] else []
                        equipment_to_inspect = [
                            f"{eq.get('manufacturer', '')} {eq.get('model', '')} {eq.get('name', '')}".strip()
                            for eq in equipment_list
                        ] if equipment_list else []

                        # Parse historical inspections and format as string
                        historical_inspections = row[14] if row[14] else []
                        history = format_historical_inspections(historical_inspections)

                        # Parse checklist items
                        checklist = row[16] if row[16] else []

                        # Check if job is past due
                        is_past_due = False
                        if row[4] and row[3] in ['scheduled', 'pending']:  # Only scheduled/pending jobs can be past due
                            is_past_due = row[4] < datetime.now()

                        job = {
                            "id": row[0],
                            "title": row[1],
                            "type": row[2],
                            "status": row[3],
                            "scheduled_time": row[4].strftime("%Y-%m-%d %I:%M %p") if row[4] else "",
                            "location": {
                                "name": row[5] or "",
                                "address": row[6] or "",
                                "latitude": float(row[7]) if row[7] else 0.0,
                                "longitude": float(row[8]) if row[8] else 0.0,
                                "access_notes": row[9]
                            },
                            "customer": {
                                "name": row[10] or "",
                                "contact": row[11] or "",
                                "email": row[12] or "",
                                "notes": row[13] or ""
                            },
                            "equipment_to_inspect": equipment_to_inspect,
                            "equipment_list": equipment_to_inspect,  # Frontend expects this field
                            "history": history,
                            "checklist": checklist,  # Checklist items from database
                            "assigned_technician": "You",
                            "priority": "normal",
                            "past_due": is_past_due
                        }

                        # Add distance if location provided
                        if latitude is not None and longitude is not None and row[7] and row[8]:
                            # Calculate Haversine distance
                            from math import radians, sin, cos, sqrt, atan2

                            lat1, lon1 = radians(latitude), radians(longitude)
                            lat2, lon2 = radians(float(row[7])), radians(float(row[8]))

                            dlat = lat2 - lat1
                            dlon = lon2 - lon1

                            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                            c = 2 * atan2(sqrt(a), sqrt(1-a))
                            distance_km = 6371 * c

                            job["distance_km"] = round(distance_km, 2)
                            job["distance_text"] = f"{distance_km:.1f} km"
                            job["distance_method"] = "haversine"
                            job["duration_minutes"] = int(distance_km * 2)  # Rough estimate
                            job["duration_text"] = f"{int(distance_km * 2)} mins"

                        jobs.append(job)

                    logger.info(f"✓ Fetched {len(jobs)} jobs from PostgreSQL")
                    return jobs

        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return []

    def get_job_by_id(self, job_id: str, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single job by ID

        Args:
            job_id: Job ID to fetch
            latitude: User's latitude for distance calculation
            longitude: User's longitude for distance calculation

        Returns:
            Job dictionary or None if not found
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT
                            j.job_id,
                            j.title,
                            j.job_type,
                            j.status,
                            j.scheduled_time,
                            j.location_name,
                            j.location_address,
                            j.location_latitude,
                            j.location_longitude,
                            j.access_notes,
                            j.customer_name,
                            j.customer_contact,
                            j.customer_email,
                            j.customer_notes,
                            j.historical_inspections,
                            COALESCE(
                                json_agg(
                                    DISTINCT jsonb_build_object(
                                        'equipment_id', e.equipment_id,
                                        'name', e.name,
                                        'manufacturer', e.manufacturer,
                                        'model', e.model,
                                        'serial_number', e.serial_number
                                    )
                                ) FILTER (WHERE e.equipment_id IS NOT NULL),
                                '[]'::json
                            ) as equipment,
                            COALESCE(
                                (
                                    SELECT json_agg(
                                        json_build_object(
                                            'id', ci.checklist_id,
                                            'description', ci.description,
                                            'category', ci.category,
                                            'photo_required', ci.photo_required,
                                            'completed', ci.completed,
                                            'notes', ci.notes,
                                            'photo_url', ci.photo_url,
                                            'completed_at', ci.completed_at
                                        )
                                        ORDER BY ci.item_id
                                    )
                                    FROM checklist_items ci
                                    WHERE ci.job_id = j.job_id
                                ),
                                '[]'::json
                            ) as checklist
                        FROM jobs j
                        LEFT JOIN job_equipment je ON j.job_id = je.job_id
                        LEFT JOIN equipment e ON je.equipment_id = e.equipment_id
                        WHERE j.job_id = %s
                        GROUP BY j.job_id
                    """

                    cur.execute(query, (job_id,))
                    row = cur.fetchone()

                    if not row:
                        logger.warning(f"Job {job_id} not found")
                        return None

                    # Parse equipment list
                    equipment_list = row[15] if row[15] else []
                    equipment_to_inspect = [
                        f"{eq.get('manufacturer', '')} {eq.get('model', '')} {eq.get('name', '')}".strip()
                        for eq in equipment_list
                    ] if equipment_list else []

                    # Parse historical inspections and format as string
                    historical_inspections = row[14] if row[14] else []
                    history = format_historical_inspections(historical_inspections)

                    # Parse checklist items
                    checklist = row[16] if row[16] else []

                    # Check if job is past due
                    is_past_due = False
                    if row[4] and row[3] in ['scheduled', 'pending']:  # Only scheduled/pending jobs can be past due
                        is_past_due = row[4] < datetime.now()

                    job = {
                        "id": row[0],
                        "title": row[1],
                        "type": row[2],
                        "status": row[3],
                        "scheduled_time": row[4].strftime("%Y-%m-%d %I:%M %p") if row[4] else "",
                        "location": {
                            "name": row[5] or "",
                            "address": row[6] or "",
                            "latitude": float(row[7]) if row[7] else 0.0,
                            "longitude": float(row[8]) if row[8] else 0.0,
                            "access_notes": row[9]
                        },
                        "customer": {
                            "name": row[10] or "",
                            "contact": row[11] or "",
                            "email": row[12] or "",
                            "notes": row[13] or ""
                        },
                        "equipment_to_inspect": equipment_to_inspect,
                        "equipment_list": equipment_to_inspect,  # Frontend expects this field
                        "history": history,
                        "checklist": checklist,  # Checklist items from database
                        "assigned_technician": "You",
                        "priority": "normal",
                        "past_due": is_past_due
                    }

                    # Add distance if location provided
                    if latitude is not None and longitude is not None and row[7] and row[8]:
                        from math import radians, sin, cos, sqrt, atan2

                        lat1, lon1 = radians(latitude), radians(longitude)
                        lat2, lon2 = radians(float(row[7])), radians(float(row[8]))

                        dlat = lat2 - lat1
                        dlon = lon2 - lon1

                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance_km = 6371 * c

                        job["distance_km"] = round(distance_km, 2)
                        job["distance_text"] = f"{distance_km:.1f} km"
                        job["distance_method"] = "haversine"
                        job["duration_minutes"] = int(distance_km * 2)
                        job["duration_text"] = f"{int(distance_km * 2)} mins"

                    logger.info(f"✓ Fetched job {job_id} from PostgreSQL")
                    return job

        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return None

    def get_past_due_jobs(self, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get only past due jobs (scheduled jobs with scheduled_time in the past)

        Args:
            latitude: User's latitude for distance calculation
            longitude: User's longitude for distance calculation

        Returns:
            List of past due job dictionaries
        """
        all_jobs = self.get_all_jobs(latitude, longitude)
        past_due_jobs = [job for job in all_jobs if job.get('past_due', False)]
        logger.info(f"✓ Found {len(past_due_jobs)} past due jobs")
        return past_due_jobs

    def get_completed_jobs(self, limit: int = 50, latitude: Optional[float] = None, longitude: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get completed jobs (job history)

        Args:
            limit: Maximum number of jobs to return
            latitude: User's latitude for distance calculation
            longitude: User's longitude for distance calculation

        Returns:
            List of completed job dictionaries, sorted by completion time (most recent first)
        """
        all_jobs = self.get_all_jobs(latitude, longitude)
        completed_jobs = [job for job in all_jobs if job['status'] == 'completed']
        # Sort by scheduled time descending (most recent first)
        completed_jobs.sort(key=lambda j: j.get('scheduled_time', ''), reverse=True)
        # Limit results
        completed_jobs = completed_jobs[:limit]
        logger.info(f"✓ Found {len(completed_jobs)} completed jobs")
        return completed_jobs


# Singleton instance
_job_service_instance = None

def get_job_service() -> JobService:
    """Get singleton JobService instance"""
    global _job_service_instance
    if _job_service_instance is None:
        _job_service_instance = JobService()
    return _job_service_instance
