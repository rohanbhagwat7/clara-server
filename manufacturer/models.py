"""Data models for manufacturer equipment specifications."""

from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


class EquipmentCategory(str, Enum):
    """Equipment categories supported by Clara."""
    FIRE_EXTINGUISHER = "fire_extinguisher"
    FIRE_PUMP = "fire_pump"
    SPRINKLER_HEAD = "sprinkler_head"
    BACKFLOW_PREVENTER = "backflow_preventer"
    FIRE_ALARM_PANEL = "fire_alarm_panel"
    SMOKE_DETECTOR = "smoke_detector"
    STANDPIPE = "standpipe"
    HVAC = "hvac"
    OTHER = "other"


@dataclass
class ElectricalSpec:
    """Electrical specifications for equipment."""
    amp_draw_min: Optional[float] = None
    amp_draw_max: Optional[float] = None
    amp_draw_nominal: Optional[float] = None
    voltage: Optional[float] = None
    phase: Optional[int] = None  # 1 or 3 phase
    frequency: Optional[int] = None  # Hz
    capacitor_microfarads: Optional[float] = None
    power_watts: Optional[float] = None


@dataclass
class PressureSpec:
    """Pressure specifications for equipment."""
    operating_pressure_min: Optional[float] = None  # PSI
    operating_pressure_max: Optional[float] = None  # PSI
    operating_pressure_nominal: Optional[float] = None  # PSI
    test_pressure: Optional[float] = None  # PSI
    pressure_unit: str = "PSI"


@dataclass
class TemperatureSpec:
    """Temperature specifications for equipment."""
    operating_temp_min: Optional[float] = None  # Celsius or Fahrenheit
    operating_temp_max: Optional[float] = None
    temperature_delta_nominal: Optional[float] = None  # Expected temperature differential
    temperature_unit: str = "F"  # F or C


@dataclass
class FlowSpec:
    """Flow specifications for equipment."""
    flow_rate_min: Optional[float] = None  # GPM
    flow_rate_max: Optional[float] = None
    flow_rate_nominal: Optional[float] = None
    flow_unit: str = "GPM"


@dataclass
class PhysicalSpec:
    """Physical dimensions and component specifications."""
    filter_size: Optional[str] = None  # e.g., "16x25x4"
    belt_size: Optional[str] = None  # e.g., "4L340"
    weight: Optional[float] = None  # pounds or kg
    dimensions: Optional[str] = None  # e.g., "24x18x12"
    thread_size: Optional[str] = None  # e.g., "1/2 NPT"


@dataclass
class ManufacturerSpecification:
    """Complete manufacturer specification for a specific equipment model.

    This represents the "factory specifications" that technicians need to
    validate equipment is operating correctly.
    """
    # Identification
    manufacturer: str
    model_number: str
    equipment_category: EquipmentCategory
    product_name: Optional[str] = None

    # Specifications by type
    electrical: Optional[ElectricalSpec] = None
    pressure: Optional[PressureSpec] = None
    temperature: Optional[TemperatureSpec] = None
    flow: Optional[FlowSpec] = None
    physical: Optional[PhysicalSpec] = None

    # Additional information
    year_introduced: Optional[int] = None
    year_discontinued: Optional[int] = None
    replacement_model: Optional[str] = None
    common_issues: Optional[List[str]] = None
    maintenance_notes: Optional[str] = None
    data_source: Optional[str] = None  # URL or source of specification
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "equipment_category": self.equipment_category.value,
            "product_name": self.product_name,
        }

        if self.electrical:
            result["electrical"] = {
                k: v for k, v in self.electrical.__dict__.items() if v is not None
            }

        if self.pressure:
            result["pressure"] = {
                k: v for k, v in self.pressure.__dict__.items() if v is not None
            }

        if self.temperature:
            result["temperature"] = {
                k: v for k, v in self.temperature.__dict__.items() if v is not None
            }

        if self.flow:
            result["flow"] = {
                k: v for k, v in self.flow.__dict__.items() if v is not None
            }

        if self.physical:
            result["physical"] = {
                k: v for k, v in self.physical.__dict__.items() if v is not None
            }

        if self.common_issues:
            result["common_issues"] = self.common_issues

        if self.maintenance_notes:
            result["maintenance_notes"] = self.maintenance_notes

        if self.data_source:
            result["data_source"] = self.data_source

        if self.year_introduced:
            result["year_introduced"] = self.year_introduced

        if self.year_discontinued:
            result["year_discontinued"] = self.year_discontinued

        if self.replacement_model:
            result["replacement_model"] = self.replacement_model

        if self.last_updated:
            result["last_updated"] = self.last_updated

        return result

    def format_for_technician(self) -> str:
        """Format specifications in a clear, field-ready format for technicians."""
        lines = [
            f"**{self.manufacturer} {self.model_number}**",
            f"Category: {self.equipment_category.value.replace('_', ' ').title()}"
        ]

        if self.product_name:
            lines.append(f"Product: {self.product_name}")

        if self.electrical:
            lines.append("\n**Electrical Specifications:**")
            if self.electrical.amp_draw_nominal:
                lines.append(f"  • Amp Draw: {self.electrical.amp_draw_nominal} A")
            elif self.electrical.amp_draw_min and self.electrical.amp_draw_max:
                lines.append(f"  • Amp Draw: {self.electrical.amp_draw_min}-{self.electrical.amp_draw_max} A")

            if self.electrical.voltage:
                phase_str = f" ({self.electrical.phase}-phase)" if self.electrical.phase else ""
                lines.append(f"  • Voltage: {self.electrical.voltage}V{phase_str}")

            if self.electrical.capacitor_microfarads:
                lines.append(f"  • Capacitor: {self.electrical.capacitor_microfarads} µF")

        if self.pressure:
            lines.append("\n**Pressure Specifications:**")
            if self.pressure.operating_pressure_nominal:
                lines.append(f"  • Operating Pressure: {self.pressure.operating_pressure_nominal} {self.pressure.pressure_unit}")
            elif self.pressure.operating_pressure_min and self.pressure.operating_pressure_max:
                lines.append(f"  • Operating Pressure: {self.pressure.operating_pressure_min}-{self.pressure.operating_pressure_max} {self.pressure.pressure_unit}")

            if self.pressure.test_pressure:
                lines.append(f"  • Test Pressure: {self.pressure.test_pressure} {self.pressure.pressure_unit}")

        if self.temperature:
            lines.append("\n**Temperature Specifications:**")
            if self.temperature.operating_temp_min and self.temperature.operating_temp_max:
                lines.append(f"  • Operating Range: {self.temperature.operating_temp_min}-{self.temperature.operating_temp_max}°{self.temperature.temperature_unit}")

            if self.temperature.temperature_delta_nominal:
                lines.append(f"  • Expected Delta: {self.temperature.temperature_delta_nominal}°{self.temperature.temperature_unit}")

        if self.flow:
            lines.append("\n**Flow Specifications:**")
            if self.flow.flow_rate_nominal:
                lines.append(f"  • Flow Rate: {self.flow.flow_rate_nominal} {self.flow.flow_unit}")
            elif self.flow.flow_rate_min and self.flow.flow_rate_max:
                lines.append(f"  • Flow Range: {self.flow.flow_rate_min}-{self.flow.flow_rate_max} {self.flow.flow_unit}")

        if self.physical:
            lines.append("\n**Physical Specifications:**")
            if self.physical.filter_size:
                lines.append(f"  • Filter Size: {self.physical.filter_size}")
            if self.physical.belt_size:
                lines.append(f"  • Belt Size: {self.physical.belt_size}")
            if self.physical.dimensions:
                lines.append(f"  • Dimensions: {self.physical.dimensions}")
            if self.physical.thread_size:
                lines.append(f"  • Thread Size: {self.physical.thread_size}")

        if self.common_issues:
            lines.append("\n**Common Issues:**")
            for issue in self.common_issues:
                lines.append(f"  • {issue}")

        if self.maintenance_notes:
            lines.append(f"\n**Maintenance Notes:** {self.maintenance_notes}")

        if self.year_discontinued and self.replacement_model:
            lines.append(f"\n⚠️ This model was discontinued in {self.year_discontinued}. Replacement: {self.replacement_model}")

        return "\n".join(lines)
