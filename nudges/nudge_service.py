"""
Nudge Service - Proactive Alert System

Monitors context and sends proactive nudges to frontend via LiveKit data channel.
"""

import asyncio
import logging
import json
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("nudge_service")


class NudgePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NudgeType(str, Enum):
    # Location-based
    PROXIMITY_TO_JOBSITE = "proximity_to_jobsite"
    ARRIVED_AT_JOBSITE = "arrived_at_jobsite"
    LEAVING_JOBSITE = "leaving_jobsite"

    # Time-based
    JOB_STARTING_SOON = "job_starting_soon"
    JOB_RUNNING_LATE = "job_running_late"
    END_OF_DAY_SUMMARY = "end_of_day_summary"

    # Progress-based
    CHECKLIST_INCOMPLETE = "checklist_incomplete"
    DATA_CAPTURE_MISSING = "data_capture_missing"
    EQUIPMENT_READING_DUE = "equipment_reading_due"

    # Safety & Compliance
    CERTIFICATION_EXPIRING = "certification_expiring"
    REQUIRED_PPE_REMINDER = "required_ppe_reminder"
    HAZARD_ALERT = "hazard_alert"

    # Equipment Intelligence
    COMMON_PROBLEM_DETECTED = "common_problem_detected"
    PART_AVAILABILITY = "part_availability"
    MAINTENANCE_OVERDUE = "maintenance_overdue"

    # Sales Opportunities
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    EQUIPMENT_AGING = "equipment_aging"
    SERVICE_CONTRACT_OPPORTUNITY = "service_contract_opportunity"
    ADDITIONAL_SERVICES_AVAILABLE = "additional_services"
    PREVENTIVE_MAINTENANCE_UPSELL = "preventive_maintenance_upsell"
    EQUIPMENT_UPGRADE_OPPORTUNITY = "equipment_upgrade_opportunity"


@dataclass
class NudgeAction:
    """Action button for a nudge"""
    label: str
    action: str  # Action identifier for frontend
    data: Optional[Dict] = None


@dataclass
class Nudge:
    """Proactive nudge/alert to send to frontend"""
    id: str
    type: NudgeType
    priority: NudgePriority
    message: str
    actions: List[NudgeAction]
    context: Dict  # Additional context data
    expires_at: Optional[int] = None  # Unix timestamp
    created_at: int = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(datetime.now().timestamp())


class NudgeService:
    """Service for creating and sending proactive nudges"""

    def __init__(self, room=None):
        self._room = room
        self._sent_nudges = set()  # Track sent nudges to avoid duplicates
        self._monitoring_task = None
        logger.info("Nudge service initialized")

    def set_room(self, room):
        """Set the LiveKit room for sending nudges"""
        self._room = room

    async def send_nudge(self, nudge: Nudge) -> bool:
        """Send a nudge to the frontend via LiveKit data channel"""
        if not self._room:
            logger.warning("Cannot send nudge - room not available")
            return False

        # Avoid duplicate nudges
        if nudge.id in self._sent_nudges:
            logger.debug(f"Nudge {nudge.id} already sent, skipping")
            return False

        try:
            # Convert nudge to JSON
            nudge_data = {
                "type": "nudge",
                "nudge": {
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
                    "created_at": nudge.created_at,
                }
            }

            # Send via LiveKit data channel
            await self._room.local_participant.publish_data(
                json.dumps(nudge_data).encode('utf-8'),
                reliable=True,
                topic="nudges"  # Specific topic for nudges
            )

            self._sent_nudges.add(nudge.id)
            logger.info(f"Sent nudge: {nudge.type.value} - {nudge.message}")
            return True

        except Exception as e:
            logger.error(f"Error sending nudge: {e}")
            return False

    async def send_proximity_nudge(
        self,
        job_id: str,
        job_title: str,
        distance_meters: float,
        eta_minutes: int
    ):
        """Send nudge when approaching job site"""
        nudge = Nudge(
            id=f"proximity_{job_id}_{int(datetime.now().timestamp())}",
            type=NudgeType.PROXIMITY_TO_JOBSITE,
            priority=NudgePriority.HIGH,
            message=f"You're approaching {job_title}. Would you like a quick briefing?",
            actions=[
                NudgeAction(
                    label="Get Briefing",
                    action="get_job_briefing",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="View Checklist",
                    action="show_checklist",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "job_id": job_id,
                "job_title": job_title,
                "distance_meters": distance_meters,
                "eta_minutes": eta_minutes,
            },
            expires_at=int((datetime.now() + timedelta(minutes=30)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_arrived_nudge(
        self,
        job_id: str,
        job_title: str
    ):
        """Send nudge when arrived at job site"""
        nudge = Nudge(
            id=f"arrived_{job_id}_{int(datetime.now().timestamp())}",
            type=NudgeType.ARRIVED_AT_JOBSITE,
            priority=NudgePriority.CRITICAL,
            message=f"You've arrived at {job_title}. Ready to start the inspection?",
            actions=[
                NudgeAction(
                    label="Start Job",
                    action="start_job_timer",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="View Equipment",
                    action="show_equipment_list",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="Not Yet",
                    action="dismiss"
                )
            ],
            context={
                "job_id": job_id,
                "job_title": job_title,
            },
            expires_at=int((datetime.now() + timedelta(minutes=5)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_data_capture_missing_nudge(
        self,
        equipment_name: str,
        missing_fields: List[str],
        job_id: str = None
    ):
        """Send nudge when required data is missing"""
        fields_str = ", ".join(missing_fields)
        nudge = Nudge(
            id=f"data_missing_{equipment_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.DATA_CAPTURE_MISSING,
            priority=NudgePriority.HIGH,
            message=f"{equipment_name} readings are incomplete. Missing: {fields_str}",
            actions=[
                NudgeAction(
                    label="Capture Now",
                    action="open_voice_capture",
                    data={"equipment": equipment_name, "missing_fields": missing_fields}
                ),
                NudgeAction(
                    label="Remind Me Later",
                    action="snooze",
                    data={"duration_minutes": 30}
                ),
                NudgeAction(
                    label="Mark N/A",
                    action="mark_not_applicable",
                    data={"equipment": equipment_name, "fields": missing_fields}
                )
            ],
            context={
                "equipment_name": equipment_name,
                "missing_fields": missing_fields,
                "job_id": job_id,
            },
            expires_at=int((datetime.now() + timedelta(hours=2)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_checklist_incomplete_nudge(
        self,
        job_id: str,
        job_title: str,
        remaining_items: List[str],
        leaving_site: bool = False
    ):
        """Send nudge when checklist is incomplete"""
        items_str = ", ".join(remaining_items[:2])
        if len(remaining_items) > 2:
            items_str += f", and {len(remaining_items) - 2} more"

        message = f"{len(remaining_items)} checklist items remaining: {items_str}"
        if leaving_site:
            message = f"Wait! {message}. Complete before leaving?"

        nudge = Nudge(
            id=f"checklist_{job_id}_{int(datetime.now().timestamp())}",
            type=NudgeType.CHECKLIST_INCOMPLETE,
            priority=NudgePriority.HIGH if leaving_site else NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="View Checklist",
                    action="show_checklist",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="Continue Later" if not leaving_site else "I'll Come Back",
                    action="dismiss"
                )
            ],
            context={
                "job_id": job_id,
                "job_title": job_title,
                "remaining_items": remaining_items,
                "leaving_site": leaving_site,
            },
            expires_at=int((datetime.now() + timedelta(hours=1)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_common_problem_detected_nudge(
        self,
        equipment_model: str,
        manufacturer: str,
        problem_description: str,
        confidence: float,
        estimated_cost: str
    ):
        """Send nudge when agent detects a common problem"""
        nudge = Nudge(
            id=f"problem_detected_{equipment_model}_{int(datetime.now().timestamp())}",
            type=NudgeType.COMMON_PROBLEM_DETECTED,
            priority=NudgePriority.HIGH,
            message=f"Detected '{problem_description}' ({int(confidence * 100)}% confidence). Common issue with {manufacturer} {equipment_model}.",
            actions=[
                NudgeAction(
                    label="View Solution",
                    action="show_problem_solution",
                    data={"equipment": equipment_model, "manufacturer": manufacturer}
                ),
                NudgeAction(
                    label="Create Estimate",
                    action="start_estimate",
                    data={"equipment": equipment_model}
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "equipment_model": equipment_model,
                "manufacturer": manufacturer,
                "problem_description": problem_description,
                "confidence": confidence,
                "estimated_cost": estimated_cost,
            },
            expires_at=int((datetime.now() + timedelta(hours=4)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_part_availability_nudge(
        self,
        part_description: str,
        supplier_name: str,
        distance_miles: float,
        in_stock: bool = True
    ):
        """Send nudge when needed part is available nearby"""
        nudge = Nudge(
            id=f"part_avail_{part_description}_{int(datetime.now().timestamp())}",
            type=NudgeType.PART_AVAILABILITY,
            priority=NudgePriority.MEDIUM,
            message=f"{part_description} is in stock at {supplier_name} ({distance_miles:.1f} miles away).",
            actions=[
                NudgeAction(
                    label="Get Directions",
                    action="navigate_to_supplier",
                    data={"supplier": supplier_name}
                ),
                NudgeAction(
                    label="Call Store",
                    action="call_supplier",
                    data={"supplier": supplier_name}
                ),
                NudgeAction(
                    label="Not Now",
                    action="dismiss"
                )
            ],
            context={
                "part_description": part_description,
                "supplier_name": supplier_name,
                "distance_miles": distance_miles,
                "in_stock": in_stock,
            },
            expires_at=int((datetime.now() + timedelta(hours=2)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_job_starting_soon_nudge(
        self,
        job_id: str,
        job_title: str,
        minutes_until_start: int,
        current_eta_minutes: int
    ):
        """Send nudge when job is starting soon"""
        will_be_late = current_eta_minutes > minutes_until_start

        nudge = Nudge(
            id=f"job_starting_{job_id}_{int(datetime.now().timestamp())}",
            type=NudgeType.JOB_STARTING_SOON if not will_be_late else NudgeType.JOB_RUNNING_LATE,
            priority=NudgePriority.HIGH if will_be_late else NudgePriority.MEDIUM,
            message=f"{job_title} starts in {minutes_until_start} minutes. Current ETA: {current_eta_minutes} minutes.",
            actions=[
                NudgeAction(
                    label="Get Directions",
                    action="open_maps",
                    data={"job_id": job_id}
                ),
                NudgeAction(
                    label="Notify Customer" if will_be_late else "Update ETA",
                    action="send_eta_update",
                    data={"job_id": job_id, "eta_minutes": current_eta_minutes}
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "job_id": job_id,
                "job_title": job_title,
                "minutes_until_start": minutes_until_start,
                "current_eta_minutes": current_eta_minutes,
                "will_be_late": will_be_late,
            },
            expires_at=int((datetime.now() + timedelta(minutes=minutes_until_start)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_end_of_day_summary_nudge(
        self,
        completed_jobs: int,
        pending_jobs: List[Dict],
        incomplete_data_count: int
    ):
        """Send end of day summary nudge"""
        message = f"Great work today! You completed {completed_jobs} jobs."
        if incomplete_data_count > 0:
            message += f" {incomplete_data_count} jobs still have incomplete data."

        nudge = Nudge(
            id=f"end_of_day_{int(datetime.now().timestamp())}",
            type=NudgeType.END_OF_DAY_SUMMARY,
            priority=NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="Complete Data",
                    action="show_incomplete_jobs",
                    data={"jobs": pending_jobs}
                ) if incomplete_data_count > 0 else None,
                NudgeAction(
                    label="Tomorrow's Schedule",
                    action="show_tomorrows_jobs"
                ),
                NudgeAction(
                    label="Done for Day",
                    action="dismiss"
                )
            ],
            context={
                "completed_jobs": completed_jobs,
                "pending_jobs": pending_jobs,
                "incomplete_data_count": incomplete_data_count,
            },
            expires_at=int((datetime.now() + timedelta(hours=1)).timestamp())
        )

        # Filter out None actions
        nudge.actions = [a for a in nudge.actions if a is not None]

        await self.send_nudge(nudge)

    def clear_sent_nudges(self):
        """Clear the cache of sent nudges (for testing or new session)"""
        self._sent_nudges.clear()
        logger.info("Cleared sent nudges cache")

    # ===== SALES OPPORTUNITY NUDGES =====

    async def send_upsell_opportunity_nudge(
        self,
        opportunity_type: str,
        equipment_name: str,
        current_service: str,
        upsell_service: str,
        estimated_value: str,
        benefits: List[str]
    ):
        """Send upsell opportunity nudge when tech finds sales opportunity"""
        message = f"Sales Opportunity: While inspecting {equipment_name}, I noticed an opportunity to upsell {upsell_service}. Estimated value: {estimated_value}."

        nudge = Nudge(
            id=f"upsell_{equipment_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.UPSELL_OPPORTUNITY,
            priority=NudgePriority.HIGH,
            message=message,
            actions=[
                NudgeAction(
                    label="View Details",
                    action="show_upsell_details",
                    data={
                        "opportunity_type": opportunity_type,
                        "equipment_name": equipment_name,
                        "upsell_service": upsell_service,
                        "benefits": benefits
                    }
                ),
                NudgeAction(
                    label="Create Quote",
                    action="create_sales_quote",
                    data={
                        "service": upsell_service,
                        "equipment": equipment_name
                    }
                ),
                NudgeAction(
                    label="Notify Sales Team",
                    action="notify_sales_team",
                    data={
                        "opportunity_type": opportunity_type,
                        "estimated_value": estimated_value
                    }
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "opportunity_type": opportunity_type,
                "equipment_name": equipment_name,
                "current_service": current_service,
                "upsell_service": upsell_service,
                "estimated_value": estimated_value,
                "benefits": benefits,
            },
            expires_at=int((datetime.now() + timedelta(hours=24)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_equipment_aging_nudge(
        self,
        equipment_name: str,
        manufacturer: str,
        model: str,
        age_years: int,
        expected_lifespan_years: int,
        replacement_cost: str,
        efficiency_loss: str
    ):
        """Send nudge when equipment is nearing end of life"""
        # More natural, informative message focused on value, not sales
        message = f"FYI: This {equipment_name} is {age_years} years old. Typical lifespan is {expected_lifespan_years} years. If customer mentions reliability concerns or higher utility bills, newer models can reduce energy costs by {efficiency_loss}."

        # Parse replacement cost
        numeric_cost = int(replacement_cost.replace('$', '').replace(',', ''))

        # Create proposal for equipment replacement
        proposal = {
            "id": f"equipment_replacement_{int(datetime.now().timestamp())}",
            "type": "equipment_replacement",
            "title": f"Equipment Replacement - {equipment_name}",
            "subtitle": f"Replace aging {manufacturer} {model} ({age_years} years old)",
            "lineItems": [
                {
                    "description": f"New {manufacturer} {model} (or equivalent)",
                    "cost": numeric_cost,
                    "notes": "High-efficiency model with improved performance"
                }
            ],
            "totalCost": numeric_cost,
            "benefits": [
                {
                    "icon": "flash",
                    "title": "Energy Savings",
                    "description": f"Recover {efficiency_loss} efficiency loss",
                    "savings": f"{efficiency_loss} improvement"
                },
                {
                    "icon": "shield-checkmark",
                    "title": "Warranty Coverage",
                    "description": "Full manufacturer warranty on new equipment",
                    "savings": None
                },
                {
                    "icon": "trending-down",
                    "title": "Reduced Maintenance",
                    "description": "Lower maintenance costs with new equipment",
                    "savings": "Save 30-40% annually"
                }
            ],
            "roi": {
                "paybackMonths": 36,
                "annualSavings": int(numeric_cost * 0.15)
            },
            "createdAt": int(datetime.now().timestamp() * 1000)
        }

        nudge = Nudge(
            id=f"aging_{equipment_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.EQUIPMENT_AGING,
            priority=NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="View Replacement Options",
                    action="show_replacement_options",
                    data={
                        "equipment_name": equipment_name,
                        "manufacturer": manufacturer,
                        "model": model
                    }
                ),
                NudgeAction(
                    label="Create Quote",
                    action="create_replacement_quote",
                    data={
                        "equipment": equipment_name,
                        "estimated_cost": replacement_cost
                    }
                ),
                NudgeAction(
                    label="Schedule Assessment",
                    action="schedule_equipment_assessment"
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "equipment_name": equipment_name,
                "manufacturer": manufacturer,
                "model": model,
                "age_years": age_years,
                "expected_lifespan_years": expected_lifespan_years,
                "replacement_cost": replacement_cost,
                "efficiency_loss": efficiency_loss,
                "proposal": proposal,
            },
            expires_at=int((datetime.now() + timedelta(hours=48)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_service_contract_opportunity_nudge(
        self,
        customer_name: str,
        current_contract_type: str,
        recommended_contract_type: str,
        annual_value: str,
        benefits: List[str],
        equipment_count: int
    ):
        """Send nudge for service contract upsell opportunity"""
        message = f"Service Contract Opportunity: {customer_name} currently has {current_contract_type}. Based on {equipment_count} pieces of equipment, recommend upgrading to {recommended_contract_type}. Annual value: {annual_value}."

        nudge = Nudge(
            id=f"service_contract_{customer_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.SERVICE_CONTRACT_OPPORTUNITY,
            priority=NudgePriority.HIGH,
            message=message,
            actions=[
                NudgeAction(
                    label="View Contract Details",
                    action="show_contract_comparison",
                    data={
                        "current": current_contract_type,
                        "recommended": recommended_contract_type,
                        "benefits": benefits
                    }
                ),
                NudgeAction(
                    label="Create Proposal",
                    action="create_contract_proposal",
                    data={
                        "customer": customer_name,
                        "contract_type": recommended_contract_type,
                        "annual_value": annual_value
                    }
                ),
                NudgeAction(
                    label="Notify Sales Rep",
                    action="notify_sales_rep",
                    data={
                        "customer": customer_name,
                        "opportunity": "contract_upgrade"
                    }
                ),
                NudgeAction(
                    label="Later",
                    action="dismiss"
                )
            ],
            context={
                "customer_name": customer_name,
                "current_contract_type": current_contract_type,
                "recommended_contract_type": recommended_contract_type,
                "annual_value": annual_value,
                "benefits": benefits,
                "equipment_count": equipment_count,
            },
            expires_at=int((datetime.now() + timedelta(hours=72)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_additional_services_nudge(
        self,
        customer_name: str,
        current_services: List[str],
        recommended_services: List[str],
        total_value: str,
        reason: str
    ):
        """Send nudge for additional services opportunity"""
        services_list = ", ".join(recommended_services)
        # More natural, helpful message - positions as helping customer, not selling
        message = f"Note: Based on this equipment type, customers often ask about {services_list}. {reason}. Mentioning this can help them avoid issues."

        # Parse total_value to get numeric value (e.g., "$2,400" -> 2400)
        numeric_value = int(total_value.replace('$', '').replace(',', ''))

        # Create line items from recommended services
        line_items = []
        value_per_service = numeric_value // len(recommended_services) if recommended_services else 0
        for service in recommended_services:
            line_items.append({
                "description": service,
                "cost": value_per_service,
                "recurring": "annual",
                "notes": f"Professional {service.lower()} service"
            })

        # Create proposal object for frontend
        proposal = {
            "id": f"additional_services_{int(datetime.now().timestamp())}",
            "type": "additional_services",
            "title": f"Additional Services - {customer_name}",
            "subtitle": reason,
            "lineItems": line_items,
            "totalCost": numeric_value,
            "recurring": "annual",
            "benefits": [
                {
                    "icon": "shield-checkmark",
                    "title": "Full Compliance",
                    "description": "Ensure full compliance with regulations",
                    "savings": "Avoid costly violations"
                },
                {
                    "icon": "checkmark-done-circle",
                    "title": "Complete Coverage",
                    "description": "Comprehensive coverage of all equipment",
                    "savings": None
                },
                {
                    "icon": "calendar",
                    "title": "Priority Service",
                    "description": "Priority scheduling for all services",
                    "savings": None
                }
            ],
            "roi": {
                "paybackMonths": 12,
                "annualSavings": numeric_value
            },
            "createdAt": int(datetime.now().timestamp() * 1000)
        }

        nudge = Nudge(
            id=f"additional_services_{customer_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.ADDITIONAL_SERVICES_AVAILABLE,
            priority=NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="View Services",
                    action="view_services",
                    data={
                        "services": recommended_services,
                        "reason": reason
                    }
                ),
                NudgeAction(
                    label="Create Quote",
                    action="create_quote",
                    data={
                        "customer": customer_name,
                        "services": recommended_services,
                        "total_value": total_value
                    }
                ),
                NudgeAction(
                    label="Discuss with Customer",
                    action="discuss_with_customer",
                    data={
                        "talking_points": recommended_services
                    }
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "customer_name": customer_name,
                "current_services": current_services,
                "recommended_services": recommended_services,
                "total_value": total_value,
                "reason": reason,
                "proposal": proposal,  # Add proposal for frontend
                "customerName": customer_name,  # For extractCustomerInfo
                "customerEmail": None,  # Would need to be passed from job data
                "customerPhone": None,  # Would need to be passed from job data
            },
            expires_at=int((datetime.now() + timedelta(hours=24)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_preventive_maintenance_upsell_nudge(
        self,
        equipment_name: str,
        manufacturer: str,
        model: str,
        current_inspection_frequency: str,
        recommended_frequency: str,
        benefits: List[str],
        annual_value: str
    ):
        """Send nudge for preventive maintenance upsell"""
        message = f"Preventive Maintenance Opportunity: {equipment_name} ({manufacturer} {model}) is currently on {current_inspection_frequency} inspections. Recommend upgrading to {recommended_frequency} to prevent failures. Annual value: {annual_value}."

        nudge = Nudge(
            id=f"preventive_{equipment_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.PREVENTIVE_MAINTENANCE_UPSELL,
            priority=NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="View Benefits",
                    action="show_pm_benefits",
                    data={
                        "current": current_inspection_frequency,
                        "recommended": recommended_frequency,
                        "benefits": benefits
                    }
                ),
                NudgeAction(
                    label="Create PM Proposal",
                    action="create_pm_proposal",
                    data={
                        "equipment": equipment_name,
                        "frequency": recommended_frequency,
                        "annual_value": annual_value
                    }
                ),
                NudgeAction(
                    label="Schedule Discussion",
                    action="schedule_customer_meeting"
                ),
                NudgeAction(
                    label="Not Now",
                    action="dismiss"
                )
            ],
            context={
                "equipment_name": equipment_name,
                "manufacturer": manufacturer,
                "model": model,
                "current_inspection_frequency": current_inspection_frequency,
                "recommended_frequency": recommended_frequency,
                "benefits": benefits,
                "annual_value": annual_value,
            },
            expires_at=int((datetime.now() + timedelta(hours=48)).timestamp())
        )
        await self.send_nudge(nudge)

    async def send_equipment_upgrade_opportunity_nudge(
        self,
        equipment_name: str,
        current_model: str,
        upgraded_model: str,
        upgrade_benefits: List[str],
        roi_months: int,
        estimated_cost: str,
        energy_savings: str
    ):
        """Send nudge for equipment upgrade opportunity"""
        message = f"Upgrade Opportunity: {equipment_name} could be upgraded from {current_model} to {upgraded_model}. ROI in {roi_months} months with {energy_savings} energy savings. Cost: {estimated_cost}."

        nudge = Nudge(
            id=f"upgrade_{equipment_name}_{int(datetime.now().timestamp())}",
            type=NudgeType.EQUIPMENT_UPGRADE_OPPORTUNITY,
            priority=NudgePriority.MEDIUM,
            message=message,
            actions=[
                NudgeAction(
                    label="View Comparison",
                    action="show_upgrade_comparison",
                    data={
                        "current": current_model,
                        "upgrade": upgraded_model,
                        "benefits": upgrade_benefits
                    }
                ),
                NudgeAction(
                    label="Calculate ROI",
                    action="show_roi_calculator",
                    data={
                        "roi_months": roi_months,
                        "energy_savings": energy_savings,
                        "cost": estimated_cost
                    }
                ),
                NudgeAction(
                    label="Create Proposal",
                    action="create_upgrade_proposal",
                    data={
                        "equipment": equipment_name,
                        "upgrade_model": upgraded_model
                    }
                ),
                NudgeAction(
                    label="Dismiss",
                    action="dismiss"
                )
            ],
            context={
                "equipment_name": equipment_name,
                "current_model": current_model,
                "upgraded_model": upgraded_model,
                "upgrade_benefits": upgrade_benefits,
                "roi_months": roi_months,
                "estimated_cost": estimated_cost,
                "energy_savings": energy_savings,
            },
            expires_at=int((datetime.now() + timedelta(hours=72)).timestamp())
        )
        await self.send_nudge(nudge)


# Global service instance
_nudge_service = None


def get_nudge_service(room=None) -> NudgeService:
    """Get or create the global nudge service instance"""
    global _nudge_service
    if _nudge_service is None:
        _nudge_service = NudgeService(room=room)
    elif room is not None:
        _nudge_service.set_room(room)
    return _nudge_service
