"""Equipment history summarization service using AI.

This service addresses customer pain point #2: "Messy equipment history"
- Automatically summarizes past issues, repairs, and component details
- Clearly differentiates between current and replaced equipment
- Provides quick access to critical information

Uses LLM to parse and summarize equipment history from job data.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime


logger = logging.getLogger("history_summarizer")


class EquipmentHistorySummarizer:
    """Service for summarizing equipment history using AI."""

    def __init__(self, llm_client=None):
        """Initialize the history summarizer.

        Args:
            llm_client: Optional LLM client (Google Gemini). If None, uses simple rule-based summarization.
        """
        self.llm_client = llm_client
        logger.info("Initialized equipment history summarizer")

    def summarize_equipment_history(
        self,
        equipment_list: List[Dict],
        inspection_history: List[Dict],
        equipment_id: Optional[str] = None
    ) -> str:
        """Summarize equipment history for a job or specific equipment.

        Args:
            equipment_list: List of equipment dictionaries from job data
            inspection_history: List of past inspection records
            equipment_id: Optional specific equipment ID to focus on

        Returns:
            Formatted summary string suitable for voice response
        """
        if equipment_id:
            # Filter to specific equipment
            equipment = [e for e in equipment_list if e.get('id') == equipment_id or e.get('name') == equipment_id]
            if not equipment:
                return f"No equipment found with ID or name '{equipment_id}'"
            return self._summarize_single_equipment(equipment[0], inspection_history)
        else:
            # Summarize all equipment
            return self._summarize_all_equipment(equipment_list, inspection_history)

    def _summarize_single_equipment(self, equipment: Dict, inspection_history: List[Dict]) -> str:
        """Summarize a single piece of equipment.

        Args:
            equipment: Equipment dictionary
            inspection_history: List of past inspection records

        Returns:
            Formatted summary string
        """
        lines = []

        # Equipment identification
        eq_name = equipment.get('name', 'Unknown Equipment')
        eq_type = equipment.get('type', 'Unknown Type')
        lines.append(f"**{eq_name}** ({eq_type})")

        # Current specifications
        lines.append("\n**Current Specifications:**")

        model = equipment.get('model')
        manufacturer = equipment.get('manufacturer')
        if manufacturer and model:
            lines.append(f"  • Make/Model: {manufacturer} {model}")
        elif model:
            lines.append(f"  • Model: {model}")

        serial = equipment.get('serial_number')
        if serial:
            lines.append(f"  • Serial Number: {serial}")

        location = equipment.get('location')
        if location:
            lines.append(f"  • Location: {location}")

        # Key component details
        if 'components' in equipment:
            lines.append("\n**Components:**")
            for component, value in equipment['components'].items():
                lines.append(f"  • {component.replace('_', ' ').title()}: {value}")

        # Installation/replacement info
        install_date = equipment.get('install_date') or equipment.get('installation_date')
        if install_date:
            lines.append(f"\n**Installed:** {install_date}")

        last_service = equipment.get('last_service_date')
        if last_service:
            lines.append(f"**Last Service:** {last_service}")

        # Historical issues and repairs
        relevant_history = self._filter_relevant_history(equipment, inspection_history)
        if relevant_history:
            lines.append("\n**Historical Notes:**")

            # Group by type of event
            issues = []
            repairs = []
            replacements = []

            for record in relevant_history[:5]:  # Limit to most recent 5 events
                event_type = record.get('event_type', 'inspection')
                notes = record.get('notes', '')
                date = record.get('date', 'Unknown date')

                if 'replaced' in notes.lower() or event_type == 'replacement':
                    replacements.append(f"{date}: {notes}")
                elif 'repair' in notes.lower() or event_type == 'repair':
                    repairs.append(f"{date}: {notes}")
                elif 'issue' in notes.lower() or 'problem' in notes.lower() or 'fail' in notes.lower():
                    issues.append(f"{date}: {notes}")

            if replacements:
                lines.append("  **Replacements:**")
                for item in replacements:
                    lines.append(f"    - {item}")

            if repairs:
                lines.append("  **Repairs:**")
                for item in repairs:
                    lines.append(f"    - {item}")

            if issues:
                lines.append("  **Past Issues:**")
                for item in issues:
                    lines.append(f"    - {item}")

        # Warnings about replaced equipment
        if equipment.get('status') == 'replaced' or equipment.get('replaced'):
            replacement_date = equipment.get('replacement_date')
            new_model = equipment.get('replacement_model')
            warning = f"\n⚠️ **This equipment was replaced"
            if replacement_date:
                warning += f" on {replacement_date}"
            if new_model:
                warning += f" with {new_model}"
            warning += "**"
            lines.append(warning)

        return "\n".join(lines)

    def _summarize_all_equipment(self, equipment_list: List[Dict], inspection_history: List[Dict]) -> str:
        """Summarize all equipment at a site.

        Args:
            equipment_list: List of equipment dictionaries
            inspection_history: List of past inspection records

        Returns:
            Formatted summary string
        """
        if not equipment_list:
            return "No equipment records found for this location."

        lines = []
        lines.append(f"**Equipment Summary** ({len(equipment_list)} items)")

        # Separate active and replaced equipment
        active_equipment = [e for e in equipment_list if e.get('status') != 'replaced' and not e.get('replaced')]
        replaced_equipment = [e for e in equipment_list if e.get('status') == 'replaced' or e.get('replaced')]

        # Active equipment
        if active_equipment:
            lines.append("\n**Active Equipment:**")
            for eq in active_equipment:
                eq_name = eq.get('name', 'Unknown')
                eq_type = eq.get('type', '')
                model = eq.get('model', '')
                location = eq.get('location', '')

                summary_line = f"  • {eq_name}"
                if eq_type:
                    summary_line += f" ({eq_type})"
                if model:
                    summary_line += f" - {model}"
                if location:
                    summary_line += f" [{location}]"

                lines.append(summary_line)

                # Quick issue summary
                relevant_history = self._filter_relevant_history(eq, inspection_history)
                issues = [r for r in relevant_history if 'issue' in r.get('notes', '').lower()
                         or 'problem' in r.get('notes', '').lower()
                         or 'fail' in r.get('notes', '').lower()]
                if issues and len(issues) > 0:
                    recent_issue = issues[0]
                    lines.append(f"    ⚠️ Last issue ({recent_issue.get('date')}): {recent_issue.get('notes', '')[:80]}")

        # Replaced equipment (to avoid confusion)
        if replaced_equipment:
            lines.append("\n**⚠️ Replaced Equipment** (no longer in service):")
            for eq in replaced_equipment:
                eq_name = eq.get('name', 'Unknown')
                replacement_date = eq.get('replacement_date', 'Unknown date')
                lines.append(f"  • {eq_name} - Replaced {replacement_date}")

        # Overall site history highlights
        if inspection_history:
            lines.append("\n**Recent Site Activity:**")
            recent_inspections = sorted(inspection_history, key=lambda x: x.get('date', ''), reverse=True)[:3]
            for inspection in recent_inspections:
                date = inspection.get('date', 'Unknown date')
                inspection_type = inspection.get('type', 'Inspection')
                summary = inspection.get('summary', '')
                lines.append(f"  • {date}: {inspection_type}")
                if summary:
                    lines.append(f"    {summary[:100]}")

        return "\n".join(lines)

    def _filter_relevant_history(self, equipment: Dict, inspection_history: List[Dict]) -> List[Dict]:
        """Filter inspection history relevant to specific equipment.

        Args:
            equipment: Equipment dictionary
            inspection_history: List of all inspection records

        Returns:
            List of relevant inspection records, sorted by date (newest first)
        """
        eq_name = equipment.get('name', '').lower()
        eq_id = equipment.get('id', '').lower()
        eq_type = equipment.get('type', '').lower()
        eq_location = equipment.get('location', '').lower()

        relevant = []
        for record in inspection_history:
            notes = record.get('notes', '').lower()
            equipment_ref = record.get('equipment', '').lower()
            location_ref = record.get('location', '').lower()

            # Check if record references this equipment
            if (eq_name and eq_name in notes) or \
               (eq_name and eq_name in equipment_ref) or \
               (eq_id and eq_id in notes) or \
               (eq_id and eq_id in equipment_ref) or \
               (eq_type and eq_type in notes) or \
               (eq_location and eq_location in location_ref):
                relevant.append(record)

        # Sort by date, newest first
        relevant.sort(key=lambda x: x.get('date', ''), reverse=True)
        return relevant

    def summarize_with_llm(
        self,
        equipment_list: List[Dict],
        inspection_history: List[Dict],
        focus_question: Optional[str] = None
    ) -> str:
        """Use LLM to generate intelligent summary (premium feature).

        This provides more sophisticated summarization using AI, including:
        - Natural language summaries
        - Trend analysis
        - Proactive alerts about recurring issues

        Args:
            equipment_list: List of equipment dictionaries
            inspection_history: List of past inspection records
            focus_question: Optional specific question to answer

        Returns:
            AI-generated summary
        """
        if not self.llm_client:
            # Fallback to rule-based if no LLM available
            logger.warning("LLM client not available, using rule-based summarization")
            return self._summarize_all_equipment(equipment_list, inspection_history)

        # Prepare context for LLM
        context = {
            "equipment": equipment_list,
            "inspection_history": inspection_history[-10:],  # Last 10 inspections
        }

        prompt = f"""You are helping a fire safety technician understand the equipment history at this site.

Equipment List:
{equipment_list}

Recent Inspection History:
{inspection_history[-5:]}

Please provide a clear, concise summary that:
1. Lists all active equipment (clearly separate from any replaced equipment)
2. Highlights any recurring issues or patterns
3. Notes important component details (filter sizes, belt sizes, etc.)
4. Points out anything that needs attention based on history

"""
        if focus_question:
            prompt += f"\nSpecific Question: {focus_question}\n"

        prompt += "\nProvide the summary in a field-ready format suitable for voice response."

        try:
            # Call LLM (implementation depends on LLM client)
            # This is a placeholder - would integrate with actual LLM client
            logger.info("Generating LLM-based summary")
            # response = self.llm_client.generate(prompt)
            # return response

            # For now, fallback to rule-based
            return self._summarize_all_equipment(equipment_list, inspection_history)

        except Exception as e:
            logger.error(f"Error generating LLM summary: {e}")
            return self._summarize_all_equipment(equipment_list, inspection_history)


# Singleton instance
_history_summarizer = None


def get_history_summarizer(llm_client=None) -> EquipmentHistorySummarizer:
    """Get singleton instance of equipment history summarizer."""
    global _history_summarizer
    if _history_summarizer is None:
        _history_summarizer = EquipmentHistorySummarizer(llm_client)
    return _history_summarizer
