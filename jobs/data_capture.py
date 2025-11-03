"""Systematic data capture prompting service.

This service addresses customer pain point #3: "Forgetting to capture equipment data"
- Proactively reminds technicians to capture critical equipment information
- Validates completeness of data before job closeout
- Ensures 100% capture rate for model numbers, serial numbers, filter/belt sizes

Management quote: "One of the things that is hardest to get and the hardest thing for the techs to remember"
"""

import logging
from typing import Dict, List, Optional, Set
from enum import Enum


logger = logging.getLogger("data_capture")


class DataCaptureField(str, Enum):
    """Required data capture fields for equipment."""
    MANUFACTURER = "manufacturer"
    MODEL_NUMBER = "model_number"
    SERIAL_NUMBER = "serial_number"
    FILTER_SIZE = "filter_size"
    BELT_SIZE = "belt_size"
    LOCATION = "location"
    INSTALLATION_DATE = "installation_date"
    PHOTO = "photo"


class DataCaptureValidator:
    """Service for validating and prompting equipment data capture."""

    # Required fields by equipment type
    REQUIRED_FIELDS_BY_TYPE = {
        "fire_pump": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
        "backflow_preventer": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.LOCATION,
            DataCaptureField.INSTALLATION_DATE,
            DataCaptureField.PHOTO,
        },
        "sprinkler_head": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
        "fire_extinguisher": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
        "hvac": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.FILTER_SIZE,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
        "hvac_with_belt": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.FILTER_SIZE,
            DataCaptureField.BELT_SIZE,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
        "default": {
            DataCaptureField.MANUFACTURER,
            DataCaptureField.MODEL_NUMBER,
            DataCaptureField.SERIAL_NUMBER,
            DataCaptureField.LOCATION,
            DataCaptureField.PHOTO,
        },
    }

    def __init__(self):
        """Initialize the data capture validator."""
        logger.info("Initialized data capture validator")

    def check_equipment_data_completeness(self, equipment: Dict) -> Dict:
        """Check if equipment data is complete and return missing fields.

        Args:
            equipment: Equipment dictionary with captured data

        Returns:
            Dictionary with:
            - is_complete: bool
            - missing_fields: List[str]
            - completion_percentage: float
            - prompt_message: str (for technician)
        """
        equipment_type = equipment.get('type', '').lower().replace(' ', '_')
        required_fields = self.REQUIRED_FIELDS_BY_TYPE.get(
            equipment_type,
            self.REQUIRED_FIELDS_BY_TYPE['default']
        )

        missing_fields = []
        captured_fields = []

        for field in required_fields:
            field_value = equipment.get(field.value)

            # Check if field exists and is not empty
            if not field_value or (isinstance(field_value, str) and field_value.strip() == ''):
                missing_fields.append(field.value)
            else:
                captured_fields.append(field.value)

        total_fields = len(required_fields)
        completion_percentage = (len(captured_fields) / total_fields * 100) if total_fields > 0 else 0

        is_complete = len(missing_fields) == 0

        # Generate prompt message
        prompt_message = self._generate_prompt_message(
            equipment.get('name', 'this equipment'),
            missing_fields,
            is_complete
        )

        return {
            'is_complete': is_complete,
            'missing_fields': missing_fields,
            'captured_fields': captured_fields,
            'completion_percentage': completion_percentage,
            'prompt_message': prompt_message,
        }

    def check_job_data_completeness(self, equipment_list: List[Dict]) -> Dict:
        """Check data completeness for all equipment in a job.

        Args:
            equipment_list: List of equipment dictionaries

        Returns:
            Dictionary with:
            - overall_complete: bool
            - total_equipment: int
            - complete_equipment: int
            - incomplete_equipment: List[Dict]
            - summary_message: str
        """
        if not equipment_list:
            return {
                'overall_complete': True,
                'total_equipment': 0,
                'complete_equipment': 0,
                'incomplete_equipment': [],
                'summary_message': 'No equipment to inspect at this job.',
            }

        incomplete_equipment = []
        complete_count = 0

        for equipment in equipment_list:
            completeness = self.check_equipment_data_completeness(equipment)
            if not completeness['is_complete']:
                incomplete_equipment.append({
                    'equipment': equipment,
                    'completeness': completeness,
                })
            else:
                complete_count += 1

        total_equipment = len(equipment_list)
        overall_complete = len(incomplete_equipment) == 0

        summary_message = self._generate_job_summary_message(
            total_equipment,
            complete_count,
            incomplete_equipment
        )

        return {
            'overall_complete': overall_complete,
            'total_equipment': total_equipment,
            'complete_equipment': complete_count,
            'incomplete_equipment': incomplete_equipment,
            'summary_message': summary_message,
        }

    def _generate_prompt_message(
        self,
        equipment_name: str,
        missing_fields: List[str],
        is_complete: bool
    ) -> str:
        """Generate friendly prompt message for technician.

        Args:
            equipment_name: Name of equipment
            missing_fields: List of missing field names
            is_complete: Whether data is complete

        Returns:
            Formatted prompt message
        """
        if is_complete:
            return f"✅ All required data captured for {equipment_name}!"

        # Format field names nicely
        formatted_fields = [field.replace('_', ' ').title() for field in missing_fields]

        if len(formatted_fields) == 1:
            fields_str = formatted_fields[0]
        elif len(formatted_fields) == 2:
            fields_str = f"{formatted_fields[0]} and {formatted_fields[1]}"
        else:
            fields_str = ", ".join(formatted_fields[:-1]) + f", and {formatted_fields[-1]}"

        return (f"⚠️ Missing data for {equipment_name}: {fields_str}. "
                f"Don't forget to capture this information before leaving the site!")

    def _generate_job_summary_message(
        self,
        total_equipment: int,
        complete_count: int,
        incomplete_equipment: List[Dict]
    ) -> str:
        """Generate summary message for entire job.

        Args:
            total_equipment: Total equipment count
            complete_count: Number of complete equipment records
            incomplete_equipment: List of incomplete equipment with details

        Returns:
            Formatted summary message
        """
        if complete_count == total_equipment:
            return f"✅ **Data Capture Complete!** All {total_equipment} equipment records have complete data."

        incomplete_count = len(incomplete_equipment)
        lines = []
        lines.append(f"**Data Capture Status:** {complete_count}/{total_equipment} equipment complete")
        lines.append(f"\n⚠️ **{incomplete_count} equipment still need data:**\n")

        for item in incomplete_equipment[:5]:  # Show up to 5
            eq = item['equipment']
            completeness = item['completeness']
            eq_name = eq.get('name', 'Unknown Equipment')
            completion_pct = int(completeness['completion_percentage'])
            missing = completeness['missing_fields']

            lines.append(f"  • {eq_name} ({completion_pct}% complete)")
            lines.append(f"    Missing: {', '.join([f.replace('_', ' ').title() for f in missing])}")

        if incomplete_count > 5:
            lines.append(f"\n  ...and {incomplete_count - 5} more")

        lines.append("\n**Don't forget to capture all required data before leaving the site!**")

        return "\n".join(lines)

    def get_field_capture_reminder(self, equipment_type: str) -> str:
        """Get a reminder message for what data to capture for equipment type.

        Args:
            equipment_type: Type of equipment

        Returns:
            Formatted reminder message
        """
        equipment_type_clean = equipment_type.lower().replace(' ', '_')
        required_fields = self.REQUIRED_FIELDS_BY_TYPE.get(
            equipment_type_clean,
            self.REQUIRED_FIELDS_BY_TYPE['default']
        )

        formatted_fields = [field.value.replace('_', ' ').title() for field in required_fields]

        lines = []
        lines.append(f"**Data Capture Checklist for {equipment_type}:**")
        for field in formatted_fields:
            lines.append(f"  ☐ {field}")

        lines.append("\nMake sure to capture all items before completing the inspection!")

        return "\n".join(lines)


# Singleton instance
_data_capture_validator = None


def get_data_capture_validator() -> DataCaptureValidator:
    """Get singleton instance of data capture validator."""
    global _data_capture_validator
    if _data_capture_validator is None:
        _data_capture_validator = DataCaptureValidator()
    return _data_capture_validator
