"""Manufacturer specification lookup service.

This service provides instant access to factory specifications for equipment.
Addresses customer pain point #1: "30-60 minute wait times for manufacturer support"

In production, this would integrate with:
1. Manufacturer APIs (e.g., Daikin, Carrier, Notifier)
2. Industry databases (FM Approvals, UL listings)
3. Web scraping of manufacturer spec sheets
4. Internal company spec database
"""

import logging
from typing import Optional, List, Dict
from difflib import SequenceMatcher

from .models import ManufacturerSpecification
from .sample_data import ALL_SPECIFICATIONS, SPECS_BY_MODEL, SPECS_BY_MANUFACTURER


logger = logging.getLogger("manufacturer_service")


class ManufacturerSpecificationService:
    """Service for looking up manufacturer equipment specifications."""

    def __init__(self):
        """Initialize the manufacturer specification service."""
        self.all_specs = ALL_SPECIFICATIONS
        self.specs_by_model = SPECS_BY_MODEL
        self.specs_by_manufacturer = SPECS_BY_MANUFACTURER
        logger.info(f"Initialized manufacturer service with {len(self.all_specs)} specifications")

    def get_specification(self, model_number: str, manufacturer: Optional[str] = None) -> Optional[ManufacturerSpecification]:
        """Get exact specification for a model number.

        Args:
            model_number: Equipment model number
            manufacturer: Optional manufacturer name for disambiguation

        Returns:
            ManufacturerSpecification if found, None otherwise
        """
        # Try exact match first
        model_upper = model_number.upper().strip()

        for spec in self.all_specs:
            if spec.model_number.upper() == model_upper:
                # If manufacturer specified, verify it matches
                if manufacturer:
                    if spec.manufacturer.upper() == manufacturer.upper().strip():
                        return spec
                else:
                    return spec

        return None

    def search_specifications(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        limit: int = 5
    ) -> List[ManufacturerSpecification]:
        """Search for specifications using fuzzy matching.

        Args:
            query: Search query (model number or description)
            manufacturer: Optional manufacturer filter
            limit: Maximum results to return

        Returns:
            List of matching specifications, sorted by relevance
        """
        query_upper = query.upper().strip()
        results = []

        for spec in self.all_specs:
            # Skip if manufacturer filter doesn't match
            if manufacturer and spec.manufacturer.upper() != manufacturer.upper().strip():
                continue

            # Calculate relevance score
            score = 0.0

            # Model number match (highest weight)
            model_similarity = SequenceMatcher(None, query_upper, spec.model_number.upper()).ratio()
            score += model_similarity * 3.0

            # Product name match
            if spec.product_name:
                name_similarity = SequenceMatcher(None, query_upper, spec.product_name.upper()).ratio()
                score += name_similarity * 1.5

            # Manufacturer match
            mfr_similarity = SequenceMatcher(None, query_upper, spec.manufacturer.upper()).ratio()
            score += mfr_similarity * 1.0

            # Category match
            if query_upper in spec.equipment_category.value.upper().replace('_', ' '):
                score += 0.5

            if score > 0.3:  # Minimum relevance threshold
                results.append((score, spec))

        # Sort by score descending
        results.sort(reverse=True, key=lambda x: x[0])

        return [spec for score, spec in results[:limit]]

    def get_specs_by_manufacturer(self, manufacturer: str) -> List[ManufacturerSpecification]:
        """Get all specifications for a manufacturer.

        Args:
            manufacturer: Manufacturer name

        Returns:
            List of specifications for that manufacturer
        """
        manufacturer_upper = manufacturer.upper().strip()

        # Try exact match
        for mfr_name, specs in self.specs_by_manufacturer.items():
            if mfr_name.upper() == manufacturer_upper:
                return specs

        # Try fuzzy match
        for mfr_name, specs in self.specs_by_manufacturer.items():
            if manufacturer_upper in mfr_name.upper() or mfr_name.upper() in manufacturer_upper:
                return specs

        return []

    def get_common_issues(self, model_number: str, manufacturer: Optional[str] = None) -> Optional[List[str]]:
        """Get common issues for a specific model.

        Args:
            model_number: Equipment model number
            manufacturer: Optional manufacturer name

        Returns:
            List of common issues if found, None otherwise
        """
        spec = self.get_specification(model_number, manufacturer)
        if spec and spec.common_issues:
            return spec.common_issues
        return None

    def format_specification_for_technician(
        self,
        model_number: str,
        manufacturer: Optional[str] = None
    ) -> str:
        """Get formatted specification suitable for voice response.

        Args:
            model_number: Equipment model number
            manufacturer: Optional manufacturer name

        Returns:
            Formatted string ready for technician
        """
        spec = self.get_specification(model_number, manufacturer)

        if not spec:
            # Try fuzzy search
            results = self.search_specifications(model_number, manufacturer, limit=3)
            if results:
                # Return top match with confidence note
                spec = results[0]
                confidence_note = "\n\n⚠️ Note: I found a similar model. Please verify this is correct.\n"
                return confidence_note + spec.format_for_technician()
            else:
                return f"I don't have factory specifications for {manufacturer + ' ' if manufacturer else ''}{model_number} in my database. This might require contacting the manufacturer directly or checking their website."

        return spec.format_for_technician()

    def quick_spec_lookup(
        self,
        model_number: str,
        manufacturer: Optional[str] = None,
        spec_type: Optional[str] = None
    ) -> str:
        """Quick lookup for specific specification types.

        Args:
            model_number: Equipment model number
            manufacturer: Optional manufacturer name
            spec_type: Type of spec (e.g., "amp_draw", "pressure", "filter_size")

        Returns:
            Quick answer string
        """
        spec = self.get_specification(model_number, manufacturer)

        if not spec:
            return f"Specification not found for {model_number}"

        spec_type_lower = spec_type.lower() if spec_type else None

        # Handle specific requests
        if spec_type_lower in ["amp", "amp_draw", "amps", "amperage"]:
            if spec.electrical and spec.electrical.amp_draw_nominal:
                return f"The {spec.manufacturer} {spec.model_number} has a nominal amp draw of {spec.electrical.amp_draw_nominal} amps."
            elif spec.electrical and spec.electrical.amp_draw_min and spec.electrical.amp_draw_max:
                return f"The {spec.manufacturer} {spec.model_number} amp draw range is {spec.electrical.amp_draw_min}-{spec.electrical.amp_draw_max} amps."
            else:
                return f"I don't have amp draw specifications for {spec.manufacturer} {spec.model_number}."

        if spec_type_lower in ["pressure", "operating_pressure"]:
            if spec.pressure and spec.pressure.operating_pressure_nominal:
                return f"The {spec.manufacturer} {spec.model_number} operates at {spec.pressure.operating_pressure_nominal} {spec.pressure.pressure_unit}."
            elif spec.pressure and spec.pressure.operating_pressure_min and spec.pressure.operating_pressure_max:
                return f"The {spec.manufacturer} {spec.model_number} operates between {spec.pressure.operating_pressure_min}-{spec.pressure.operating_pressure_max} {spec.pressure.pressure_unit}."
            else:
                return f"I don't have pressure specifications for {spec.manufacturer} {spec.model_number}."

        if spec_type_lower in ["filter", "filter_size"]:
            if spec.physical and spec.physical.filter_size:
                return f"The {spec.manufacturer} {spec.model_number} uses a {spec.physical.filter_size} filter."
            else:
                return f"I don't have filter size information for {spec.manufacturer} {spec.model_number}."

        if spec_type_lower in ["belt", "belt_size"]:
            if spec.physical and spec.physical.belt_size:
                return f"The {spec.manufacturer} {spec.model_number} uses a {spec.physical.belt_size} belt."
            else:
                return f"I don't have belt size information for {spec.manufacturer} {spec.model_number}."

        if spec_type_lower in ["capacitor", "microfarads", "uf"]:
            if spec.electrical and spec.electrical.capacitor_microfarads:
                return f"The {spec.manufacturer} {spec.model_number} uses a {spec.electrical.capacitor_microfarads} microfarad capacitor."
            else:
                return f"I don't have capacitor specifications for {spec.manufacturer} {spec.model_number}."

        if spec_type_lower in ["temperature", "temp", "delta"]:
            if spec.temperature and spec.temperature.temperature_delta_nominal:
                return f"The {spec.manufacturer} {spec.model_number} has an expected temperature delta of {spec.temperature.temperature_delta_nominal}°{spec.temperature.temperature_unit}."
            elif spec.temperature and spec.temperature.operating_temp_min and spec.temperature.operating_temp_max:
                return f"The {spec.manufacturer} {spec.model_number} operates between {spec.temperature.operating_temp_min}-{spec.temperature.operating_temp_max}°{spec.temperature.temperature_unit}."
            else:
                return f"I don't have temperature specifications for {spec.manufacturer} {spec.model_number}."

        # If no specific type requested, return full formatted spec
        return spec.format_for_technician()


# Singleton instance
_manufacturer_service = None


def get_manufacturer_service() -> ManufacturerSpecificationService:
    """Get singleton instance of manufacturer specification service."""
    global _manufacturer_service
    if _manufacturer_service is None:
        _manufacturer_service = ManufacturerSpecificationService()
    return _manufacturer_service
