"""Common problems database for equipment models.

This service addresses the need for aggregated industry knowledge about
typical equipment problems and failure modes.

In production, this would aggregate data from:
- Industry forums (HVAC-Talk, Contractor Talk, Reddit)
- Manufacturer service bulletins
- CPSC recall database
- Internal company historical data
- Warranty claim data

For now, provides curated common problems for major equipment models.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger("common_problems")


class ProblemSeverity(str, Enum):
    """Severity levels for common problems."""
    CRITICAL = "critical"  # Safety issue or complete failure
    HIGH = "high"  # Major functionality impaired
    MEDIUM = "medium"  # Reduced performance or reliability
    LOW = "low"  # Minor issue or maintenance item


class ProblemFrequency(str, Enum):
    """How frequently this problem occurs."""
    VERY_COMMON = "very_common"  # >20% of units
    COMMON = "common"  # 10-20% of units
    OCCASIONAL = "occasional"  # 5-10% of units
    RARE = "rare"  # <5% of units


@dataclass
class CommonProblem:
    """A common problem for a specific equipment model or type."""
    equipment_model: str
    equipment_manufacturer: str
    problem_description: str
    symptoms: List[str]
    root_cause: str
    solution: str
    severity: ProblemSeverity
    frequency: ProblemFrequency
    typical_age_range: Optional[str] = None  # e.g., "5-7 years"
    related_parts: Optional[List[str]] = None
    estimated_repair_cost: Optional[str] = None
    data_sources: Optional[List[str]] = None  # Where this knowledge came from


# Curated common problems database
COMMON_PROBLEMS_DATABASE = [
    # Carrier HVAC Common Problems
    CommonProblem(
        equipment_model="50A4-030",
        equipment_manufacturer="Carrier",
        problem_description="Capacitor failure causing compressor not starting",
        symptoms=[
            "Unit not cooling/heating",
            "Compressor humming but not starting",
            "Clicking sound from contactor",
            "High amp draw on common terminal",
        ],
        root_cause="Run capacitor degradation over time (typical 5-7 year lifespan)",
        solution="Replace run capacitor with OEM 75µF capacitor. Test compressor windings before replacement.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="5-7 years",
        related_parts=["Run capacitor 75µF", "Start capacitor (if applicable)"],
        estimated_repair_cost="$150-$300",
        data_sources=["HVAC-Talk forums", "Carrier service bulletins", "Field experience"],
    ),
    CommonProblem(
        equipment_model="50A4-030",
        equipment_manufacturer="Carrier",
        problem_description="Economizer damper stuck or not modulating properly",
        symptoms=[
            "Unit not bringing in outside air",
            "High cooling costs during mild weather",
            "Damper stuck open or closed",
        ],
        root_cause="Economizer actuator failure or damper linkage binding - common on rooftop units",
        solution="Check actuator operation and linkage. Lubricate damper pivots. Replace actuator if faulty.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="5-10 years",
        related_parts=["Economizer actuator", "Damper blades", "Linkage assembly"],
        estimated_repair_cost="$300-$800",
        data_sources=["Carrier tech support", "HVAC contractor forums"],
    ),

    # Daikin Ductless Common Problems
    CommonProblem(
        equipment_model="FTXS12WVJU9",
        equipment_manufacturer="Daikin",
        problem_description="Drain line clogging causing water leaks",
        symptoms=[
            "Water dripping from indoor unit",
            "Water pooling under unit",
            "Musty odor from unit",
            "E7 error code (some models)",
        ],
        root_cause="Algae and debris buildup in condensate drain line",
        solution="Clear drain line with shop vac or compressed air. Treat with algae tablets. Install P-trap if missing.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="1-3 years (then annually)",
        related_parts=["Drain pan tablets", "Condensate pump (if needed)"],
        estimated_repair_cost="$100-$250",
        data_sources=["Daikin service manual", "Mini-split forums", "Reddit r/HVAC"],
    ),

    # Peerless Fire Pump Common Problems
    CommonProblem(
        equipment_model="4AE12",
        equipment_manufacturer="Peerless Pump",
        problem_description="Mechanical seal leakage",
        symptoms=[
            "Water dripping from seal housing",
            "Visible water on pump volute",
            "Increased bearing temperature",
            "Whistling noise during operation",
        ],
        root_cause="Mechanical seal wear after 3-5 years of service or dry running damage",
        solution="Replace mechanical seal assembly. Check for shaft damage or corrosion. Verify water supply before restart.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="3-5 years",
        related_parts=["Mechanical seal kit", "O-rings", "Seal housing gasket"],
        estimated_repair_cost="$800-$1500",
        data_sources=["Peerless service manual", "NFPA 25 inspection reports", "Fire pump contractor forums"],
    ),
    CommonProblem(
        equipment_model="4AE12",
        equipment_manufacturer="Peerless Pump",
        problem_description="Bearing failure causing excessive vibration",
        symptoms=[
            "Unusual vibration during operation",
            "Grinding or rattling noise",
            "High bearing temperature (>180°F)",
            "Motor trips on overload",
        ],
        root_cause="Bearing wear due to age (5+ years) or inadequate lubrication",
        solution="Replace bearings. Check shaft alignment. Verify proper lubrication schedule.",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.OCCASIONAL,
        typical_age_range="5-8 years",
        related_parts=["Pump bearings", "Bearing grease", "Coupling (inspect)"],
        estimated_repair_cost="$1200-$2500",
        data_sources=["Peerless maintenance manual", "NFPA 25 requirements"],
    ),

    # Watts Backflow Preventer Common Problems
    CommonProblem(
        equipment_model="909-QT",
        equipment_manufacturer="Watts",
        problem_description="Relief valve continuous dripping",
        symptoms=[
            "Water continuously dripping from relief valve",
            "Differential pressure test failure",
            "First check valve not holding",
        ],
        root_cause="Debris on check valve seats or diaphragm wear",
        solution="Disassemble and clean check valve seats. Replace rubber parts kit if worn. Test per ASSE 5110.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="3-5 years",
        related_parts=["Rubber parts kit 909-K", "Check valve springs"],
        estimated_repair_cost="$200-$400",
        data_sources=["Watts service manual", "Backflow tester forums", "ASSE bulletins"],
    ),

    # Notifier Fire Alarm Panel Common Problems
    CommonProblem(
        equipment_model="NFS2-3030",
        equipment_manufacturer="Notifier",
        problem_description="Ground fault errors on NAC circuits",
        symptoms=[
            "Ground fault trouble on panel display",
            "NAC circuit supervision failure",
            "Intermittent alarm device activation",
        ],
        root_cause="Wiring insulation breakdown due to moisture or physical damage",
        solution="Isolate circuits systematically. Check for water intrusion at device boxes. Megger test wiring. Repair or replace damaged sections.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="Any age (environmental)",
        related_parts=["Wire (replacement sections)", "Device mounting boxes"],
        estimated_repair_cost="$500-$2000 (varies by extent)",
        data_sources=["Notifier technical support", "NFPA 72", "Fire alarm technician forums"],
    ),
    CommonProblem(
        equipment_model="NFS2-3030",
        equipment_manufacturer="Notifier",
        problem_description="Battery backup failure",
        symptoms=[
            "Low battery trouble",
            "Battery won't hold charge",
            "Reduced backup runtime",
            "Battery test failure",
        ],
        root_cause="Battery age (typical 4-5 year lifespan) or charger failure",
        solution="Load test batteries. Replace if >4 years old or failing load test. Check charging voltage (27.6V float, 28.4V equalize).",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="4-5 years",
        related_parts=["12V sealed lead-acid batteries (2x)", "Battery cables"],
        estimated_repair_cost="$200-$400",
        data_sources=["NFPA 72 battery requirements", "Notifier maintenance guide"],
    ),

    # Ansul Fire Extinguisher Common Problems
    CommonProblem(
        equipment_model="A410",
        equipment_manufacturer="Ansul",
        problem_description="Pressure loss requiring recharge",
        symptoms=[
            "Pressure gauge in red zone",
            "Gauge reads below 175 PSI",
            "Slow pressure drop over time",
        ],
        root_cause="Valve stem o-ring leakage or gauge connection leak",
        solution="Discharge unit, disassemble valve, replace o-rings. Recharge with ABC powder to 195 PSI.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="2-4 years",
        related_parts=["O-ring kit", "ABC dry chemical", "Pressure gauge (if damaged)"],
        estimated_repair_cost="$75-$150",
        data_sources=["Ansul service manual", "NFPA 10", "Extinguisher tech forums"],
    ),

    # Generic HVAC Problems (applicable to multiple models)
    CommonProblem(
        equipment_model="Generic Heat Pump",
        equipment_manufacturer="Multiple",
        problem_description="Defrost cycle too frequent in cold weather",
        symptoms=[
            "Outdoor unit covered in ice",
            "Defrost cycle every 15-20 minutes",
            "Reduced heating capacity",
            "High energy bills",
        ],
        root_cause="Low airflow over outdoor coil or refrigerant undercharge",
        solution="Clean outdoor coil. Check refrigerant charge. Verify outdoor fan operation. Check defrost board operation.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="Any age (seasonal)",
        related_parts=["Defrost board", "Defrost sensor", "Refrigerant (if low)"],
        estimated_repair_cost="$150-$500",
        data_sources=["Industry forums", "Manufacturer tech bulletins"],
    ),

    # Additional Trane HVAC Problems
    CommonProblem(
        equipment_model="XR16",
        equipment_manufacturer="Trane",
        problem_description="Compressor short cycling",
        symptoms=[
            "Unit turns on and off every 2-3 minutes",
            "No cooling or poor cooling",
            "Clicking sound from contactor",
            "High amp draw on compressor",
        ],
        root_cause="Failed run capacitor or contactor contacts pitting",
        solution="Check capacitor with multimeter (should be 60µF ±6%). Replace if out of spec. Inspect contactor contacts for pitting and replace if necessary.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="5-8 years",
        related_parts=["60µF run capacitor", "30A contactor"],
        estimated_repair_cost="$150-$300",
        data_sources=["Trane service bulletins", "HVAC tech forums"],
    ),

    # Lennox HVAC Problems
    CommonProblem(
        equipment_model="EL16XC1",
        equipment_manufacturer="Lennox",
        problem_description="Blower motor failure",
        symptoms=[
            "No air flow from vents",
            "Humming sound from air handler",
            "Burnt smell when unit runs",
            "Tripped breaker",
        ],
        root_cause="Blower motor bearings seized or capacitor failure",
        solution="Check blower motor capacitor (7.5µF). Test motor windings for shorts. Replace motor if bearings are seized or windings shorted.",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.OCCASIONAL,
        typical_age_range="10-15 years",
        related_parts=["Blower motor 1/2 HP", "7.5µF capacitor", "Motor mount"],
        estimated_repair_cost="$400-$800",
        data_sources=["Lennox technical manual", "Field experience"],
    ),

    # Goodman HVAC Problems
    CommonProblem(
        equipment_model="GSXC16",
        equipment_manufacturer="Goodman",
        problem_description="Refrigerant leak at service valve",
        symptoms=[
            "Unit not cooling",
            "Low pressure on gauges",
            "Hissing sound at outdoor unit",
            "Ice buildup on suction line",
        ],
        root_cause="Service valve core leak or Schrader valve deterioration",
        solution="Recover refrigerant, replace valve cores. Leak test with nitrogen and soap bubbles. Evacuate system and recharge to factory specs (R-410A).",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="3-7 years",
        related_parts=["Schrader valve cores", "R-410A refrigerant", "Valve caps"],
        estimated_repair_cost="$300-$600",
        data_sources=["Goodman warranty claims", "EPA refrigerant guidelines"],
    ),

    # Rheem Water Heater Problems (relevant for HVAC techs who service these)
    CommonProblem(
        equipment_model="RTGH-95DVLN",
        equipment_manufacturer="Rheem",
        problem_description="Ignition failure - no hot water",
        symptoms=[
            "Error code 11 (ignition failure)",
            "Clicking but no flame",
            "No hot water",
            "Gas valve clicking",
        ],
        root_cause="Flame rod fouling or igniter failure",
        solution="Clean flame rod with fine steel wool. Test igniter for spark. Check gas pressure (3.5-4.0\" WC natural gas). Replace igniter if cracked.",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="4-8 years",
        related_parts=["Flame rod sensor", "Igniter assembly", "Gas valve"],
        estimated_repair_cost="$200-$400",
        data_sources=["Rheem service manual", "Tankless water heater forums"],
    ),

    # Additional Fire Pump Problems
    CommonProblem(
        equipment_model="Generic Jockey Pump",
        equipment_manufacturer="Multiple",
        problem_description="Jockey pump cycling too frequently",
        symptoms=[
            "Pump runs every 5-10 minutes",
            "System pressure drops quickly",
            "Pump motor overheating",
            "High electric bills",
        ],
        root_cause="System leak or waterlogged pressure tank",
        solution="Check entire system for leaks (automatic drains, test connections, PRVs). Test pressure tank pre-charge (should be 2 PSI below cut-in). Look for weeping relief valves.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="Any age",
        related_parts=["Pressure tank", "Relief valve", "Leak repair parts"],
        estimated_repair_cost="$100-$500 depending on leak location",
        data_sources=["NFPA 25", "Fire pump maintenance guides"],
    ),

    CommonProblem(
        equipment_model="8196",
        equipment_manufacturer="Peerless",
        problem_description="Packing gland leaking excessively",
        symptoms=[
            "Heavy water drip from shaft seal",
            "Water pooling under pump",
            "Shaft visible through packing",
        ],
        root_cause="Packing worn out or shaft sleeve scored",
        solution="Tighten packing gland nuts evenly. If leak continues, repack with new packing rings. Inspect shaft sleeve for scoring - replace if grooved.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="5-10 years",
        related_parts=["Packing rings", "Shaft sleeve (if scored)", "Gland nuts"],
        estimated_repair_cost="$150-$400",
        data_sources=["Peerless service manual", "Pump maintenance guides"],
    ),

    # Additional Backflow Problems
    CommonProblem(
        equipment_model="909-QT",
        equipment_manufacturer="Watts",
        problem_description="Relief valve constantly dripping",
        symptoms=[
            "Water dripping from relief valve",
            "Valve won't fully close after test",
            "Debris visible in valve seat",
        ],
        root_cause="Debris on valve seat or worn valve diaphragm",
        solution="Isolate device, disassemble relief valve, clean seat thoroughly. Replace diaphragm if torn or brittle. Reassemble and test.",
        severity=ProblemSeverity.MEDIUM,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="3-6 years",
        related_parts=["Relief valve rebuild kit", "Diaphragm", "O-rings"],
        estimated_repair_cost="$100-$200",
        data_sources=["Watts technical bulletin", "Backflow tester experience"],
    ),

    CommonProblem(
        equipment_model="2000B",
        equipment_manufacturer="Ames",
        problem_description="Check valve #1 not holding",
        symptoms=[
            "Failed backflow test",
            "Check #1 pressure drop > 1 PSI",
            "Water flows backward through valve",
        ],
        root_cause="Check valve disc damaged or spring weakened",
        solution="Isolate and drain device. Disassemble check #1 assembly. Replace check disc and spring. Clean all seating surfaces. Reassemble with new o-rings.",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="5-10 years",
        related_parts=["Check valve kit", "Springs", "Rubber goods kit"],
        estimated_repair_cost="$150-$300",
        data_sources=["Ames service manual", "ASSE 5110 testing guidelines"],
    ),

    # Sprinkler System Problems
    CommonProblem(
        equipment_model="VK302",
        equipment_manufacturer="Viking",
        problem_description="Sprinkler head corrosion and sediment buildup",
        symptoms=[
            "Visible corrosion on head",
            "Sediment visible in water",
            "Head doesn't appear to be fully open",
            "Orange/brown water discharge",
        ],
        root_cause="Internal pipe corrosion in wet system",
        solution="Replace affected heads. Flush system piping. Consider nitrogen inerting for dry systems or corrosion inhibitor for wet systems. Conduct internal pipe inspection.",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.COMMON,
        typical_age_range="15-25 years for old steel pipe",
        related_parts=["Replacement sprinkler heads", "Pipe sections (if severe)", "Corrosion inhibitor"],
        estimated_repair_cost="$200-$1000+ depending on extent",
        data_sources=["NFPA 25 Chapter 5", "Viking technical bulletins"],
    ),

    # Fire Alarm Problems
    CommonProblem(
        equipment_model="i3",
        equipment_manufacturer="System Sensor",
        problem_description="False alarms from smoke detector",
        symptoms=[
            "Frequent unwanted alarms",
            "Alarms at similar time each day",
            "Alarms in specific locations only",
            "Detector sensitivity high",
        ],
        root_cause="Dust accumulation in detector chamber or detector aging",
        solution="Clean detector with vacuum and compressed air. Test with canned smoke. If >10 years old, replace detector. Check for environmental factors (steam, dust, etc).",
        severity=ProblemSeverity.HIGH,
        frequency=ProblemFrequency.VERY_COMMON,
        typical_age_range="8-15 years",
        related_parts=["Replacement smoke detector head", "Detector base (if damaged)"],
        estimated_repair_cost="$75-$200 per detector",
        data_sources=["NFPA 72", "System Sensor maintenance guide"],
    ),

    # Additional Fire Extinguisher Problems
    CommonProblem(
        equipment_model="B500",
        equipment_manufacturer="Amerex",
        problem_description="Discharge valve seized",
        symptoms=[
            "Handle won't move during test",
            "Pin removed but valve won't operate",
            "Corrosion visible on valve stem",
        ],
        root_cause="Corrosion from environmental exposure or lack of maintenance",
        solution="Do NOT force valve. Unit requires professional service. Discharge safely, disassemble valve, replace valve assembly. Hydrotest if >12 years old.",
        severity=ProblemSeverity.CRITICAL,
        frequency=ProblemFrequency.OCCASIONAL,
        typical_age_range="8-15 years in harsh environments",
        related_parts=["Valve assembly", "Discharge tube", "Safety pin"],
        estimated_repair_cost="$100-$250",
        data_sources=["NFPA 10", "Amerex service procedures"],
    ),
]


class CommonProblemsService:
    """Service for looking up common problems for equipment."""

    def __init__(self):
        """Initialize common problems service."""
        self.problems_database = COMMON_PROBLEMS_DATABASE
        logger.info(f"Initialized common problems service with {len(self.problems_database)} problems")

    def get_common_problems(
        self,
        model_number: str,
        manufacturer: Optional[str] = None,
        severity_filter: Optional[ProblemSeverity] = None
    ) -> List[CommonProblem]:
        """Get common problems for a specific equipment model.

        Args:
            model_number: Equipment model number
            manufacturer: Optional manufacturer name for disambiguation
            severity_filter: Optional filter by severity level

        Returns:
            List of common problems for the model
        """
        model_upper = model_number.upper().strip()
        problems = []

        for problem in self.problems_database:
            # Check model match
            model_match = problem.equipment_model.upper() == model_upper

            # Check manufacturer match if specified
            mfr_match = True
            if manufacturer:
                mfr_match = problem.equipment_manufacturer.upper() == manufacturer.upper().strip()

            # Check severity filter
            severity_match = True
            if severity_filter:
                severity_match = problem.severity == severity_filter

            if model_match and mfr_match and severity_match:
                problems.append(problem)

        # Sort by frequency (most common first), then severity
        frequency_order = {
            ProblemFrequency.VERY_COMMON: 0,
            ProblemFrequency.COMMON: 1,
            ProblemFrequency.OCCASIONAL: 2,
            ProblemFrequency.RARE: 3,
        }
        severity_order = {
            ProblemSeverity.CRITICAL: 0,
            ProblemSeverity.HIGH: 1,
            ProblemSeverity.MEDIUM: 2,
            ProblemSeverity.LOW: 3,
        }

        problems.sort(key=lambda p: (frequency_order[p.frequency], severity_order[p.severity]))

        return problems

    def search_problems_by_symptoms(self, symptoms: str) -> List[CommonProblem]:
        """Search for problems matching described symptoms.

        Args:
            symptoms: Description of symptoms (e.g., "water leaking, dripping")

        Returns:
            List of matching problems sorted by relevance
        """
        symptoms_lower = symptoms.lower()
        matches = []

        for problem in self.problems_database:
            relevance_score = 0

            # Check if any symptom keywords match
            for symptom in problem.symptoms:
                symptom_lower = symptom.lower()
                # Count matching words
                symptom_words = set(symptom_lower.split())
                query_words = set(symptoms_lower.split())
                matching_words = symptom_words.intersection(query_words)
                relevance_score += len(matching_words)

            # Check problem description
            if any(word in problem.problem_description.lower() for word in symptoms_lower.split()):
                relevance_score += 1

            if relevance_score > 0:
                matches.append((relevance_score, problem))

        # Sort by relevance score descending
        matches.sort(reverse=True, key=lambda x: x[0])

        return [problem for score, problem in matches[:5]]  # Top 5 matches

    def format_problem_for_technician(self, problem: CommonProblem) -> str:
        """Format a common problem for voice/text response.

        Args:
            problem: CommonProblem to format

        Returns:
            Formatted string suitable for technician
        """
        lines = []
        lines.append(f"**Common Problem: {problem.problem_description}**")
        lines.append(f"Equipment: {problem.equipment_manufacturer} {problem.equipment_model}")
        lines.append(f"Frequency: {problem.frequency.value.replace('_', ' ').title()}")
        lines.append(f"Severity: {problem.severity.value.title()}")

        if problem.typical_age_range:
            lines.append(f"Typical Age: {problem.typical_age_range}")

        lines.append("\n**Symptoms:**")
        for symptom in problem.symptoms:
            lines.append(f"  • {symptom}")

        lines.append(f"\n**Root Cause:** {problem.root_cause}")
        lines.append(f"\n**Solution:** {problem.solution}")

        if problem.related_parts:
            lines.append("\n**Parts Needed:**")
            for part in problem.related_parts:
                lines.append(f"  • {part}")

        if problem.estimated_repair_cost:
            lines.append(f"\n**Estimated Cost:** {problem.estimated_repair_cost}")

        if problem.data_sources:
            lines.append(f"\n**Source:** {', '.join(problem.data_sources)}")

        return "\n".join(lines)


# Singleton instance
_common_problems_service = None


def get_common_problems_service() -> CommonProblemsService:
    """Get singleton instance of common problems service."""
    global _common_problems_service
    if _common_problems_service is None:
        _common_problems_service = CommonProblemsService()
    return _common_problems_service
