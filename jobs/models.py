"""
Job data models for Clara demo
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Union
from enum import Enum


class JobStatus(str, Enum):
    """Job status states"""
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Types of fire safety jobs"""
    FIRE_EXTINGUISHER = "fire_extinguisher"
    SPRINKLER_INSPECTION = "sprinkler_inspection"
    FIRE_EXTINGUISHER_SPRINKLER = "fire_extinguisher_sprinkler_inspection"
    FIRE_EXTINGUISHER_ALARM = "fire_extinguisher_alarm_inspection"
    SPRINKLER_FIRE_PUMP = "sprinkler_fire_pump_inspection"
    BACKFLOW_VALVE = "backflow_valve"
    FIRE_PUMP = "fire_pump"
    ANNUAL_INSPECTION = "annual_inspection"


@dataclass
class Location:
    """Job site location"""
    name: str
    address: str
    latitude: float
    longitude: float
    access_notes: Optional[str] = None


@dataclass
class HistoricalInspection:
    """Past inspection record"""
    date: str
    technician: str
    findings: str
    issues: List[str] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)


@dataclass
class Customer:
    """Customer information"""
    name: str
    contact: str
    email: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ChecklistItem:
    """Individual checklist item"""
    id: str
    description: str
    category: str  # "general", "per_unit", "documentation", etc.
    completed: bool = False
    notes: Optional[str] = None
    photo_required: bool = False
    photo_url: Optional[str] = None


@dataclass
class Job:
    """Complete job data structure"""
    id: str
    title: str
    type: JobType
    status: JobStatus
    location: Location
    scheduled_time: str
    equipment_to_inspect: List[Union[str, Dict]]
    customer: Customer
    duration_estimate: Optional[str] = None
    history: List[HistoricalInspection] = field(default_factory=list)
    checklist: List[ChecklistItem] = field(default_factory=list)
    assigned_technician: str = "You"
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    notes: Optional[str] = None
    special_instructions: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
            "location": {
                "name": self.location.name,
                "address": self.location.address,
                "latitude": self.location.latitude,
                "longitude": self.location.longitude,
                "access_notes": self.location.access_notes,
            },
            "scheduled_time": self.scheduled_time,
            "duration_estimate": self.duration_estimate,
            "equipment_to_inspect": self.equipment_to_inspect,
            "customer": {
                "name": self.customer.name,
                "contact": self.customer.contact,
                "email": self.customer.email,
                "notes": self.customer.notes,
            },
            "history": [
                {
                    "date": h.date,
                    "technician": h.technician,
                    "findings": h.findings,
                    "issues": h.issues,
                    "photos": h.photos,
                }
                for h in self.history
            ],
            "checklist": [
                {
                    "id": item.id,
                    "description": item.description,
                    "category": item.category,
                    "completed": item.completed,
                    "notes": item.notes,
                    "photo_required": item.photo_required,
                    "photo_url": item.photo_url,
                }
                for item in self.checklist
            ],
            "assigned_technician": self.assigned_technician,
            "priority": self.priority,
            "notes": self.notes,
        }
