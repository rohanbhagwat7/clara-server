"""Sample manufacturer specification data for common fire safety and HVAC equipment.

This file contains realistic manufacturer specifications based on common equipment
used in fire safety inspections. In production, this would be replaced with:
1. API integrations to manufacturer databases
2. Web scraping of manufacturer spec sheets
3. Integration with industry databases (e.g., FM Approvals, UL listings)
"""

from .models import (
    ManufacturerSpecification,
    ElectricalSpec,
    PressureSpec,
    TemperatureSpec,
    FlowSpec,
    PhysicalSpec,
    EquipmentCategory,
)


# Fire Pump Specifications
FIRE_PUMPS = [
    ManufacturerSpecification(
        manufacturer="Peerless Pump",
        model_number="4AE12",
        equipment_category=EquipmentCategory.FIRE_PUMP,
        product_name="Horizontal Split Case Fire Pump",
        electrical=ElectricalSpec(
            amp_draw_nominal=48.0,
            voltage=460.0,
            phase=3,
            frequency=60,
            power_watts=30000,
        ),
        pressure=PressureSpec(
            operating_pressure_nominal=100.0,
            operating_pressure_min=90.0,
            operating_pressure_max=110.0,
            test_pressure=150.0,
            pressure_unit="PSI",
        ),
        flow=FlowSpec(
            flow_rate_nominal=1500.0,
            flow_rate_min=1200.0,
            flow_rate_max=1800.0,
            flow_unit="GPM",
        ),
        common_issues=[
            "Bearing wear after 5+ years",
            "Seal leakage - check quarterly",
            "Impeller erosion in high-sediment water",
        ],
        maintenance_notes="Lubricate bearings every 6 months. Replace mechanical seal every 3-5 years. Check alignment annually.",
        data_source="Peerless Pump Installation & Operation Manual 4AE12",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Aurora Pump",
        model_number="Model 410",
        equipment_category=EquipmentCategory.FIRE_PUMP,
        product_name="Vertical Turbine Fire Pump",
        electrical=ElectricalSpec(
            amp_draw_nominal=52.0,
            voltage=480.0,
            phase=3,
            frequency=60,
        ),
        pressure=PressureSpec(
            operating_pressure_nominal=115.0,
            test_pressure=172.5,
            pressure_unit="PSI",
        ),
        flow=FlowSpec(
            flow_rate_nominal=2000.0,
            flow_unit="GPM",
        ),
        common_issues=[
            "Column pipe corrosion",
            "Bowl bearing failure",
            "Shaft misalignment",
        ],
        data_source="Aurora Pump Technical Manual 410 Series",
        last_updated="2024-10",
    ),
]


# Backflow Preventer Specifications
BACKFLOW_PREVENTERS = [
    ManufacturerSpecification(
        manufacturer="Watts",
        model_number="909-QT",
        equipment_category=EquipmentCategory.BACKFLOW_PREVENTER,
        product_name="Reduced Pressure Zone Backflow Preventer",
        pressure=PressureSpec(
            operating_pressure_max=175.0,
            test_pressure=200.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="2\" NPT",
            dimensions="20.5 x 8.5 x 13.5",
            weight=45.0,
        ),
        common_issues=[
            "Relief valve dripping - check diaphragm",
            "Check valve fouling - annual cleaning required",
            "Spring fatigue after 7-10 years",
        ],
        maintenance_notes="Annual test required per NFPA 25. Replace internal components every 5 years.",
        data_source="Watts 909 Series Installation Instructions",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Ames",
        model_number="C500",
        equipment_category=EquipmentCategory.BACKFLOW_PREVENTER,
        product_name="Colt Reduced Pressure Backflow Preventer",
        pressure=PressureSpec(
            operating_pressure_max=150.0,
            test_pressure=175.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="3\" Flanged",
            weight=78.0,
        ),
        common_issues=[
            "Pressure differential failure",
            "First check valve leakage",
        ],
        data_source="Ames C500 Technical Specifications",
        last_updated="2024-10",
    ),
]


# Sprinkler Head Specifications
SPRINKLER_HEADS = [
    ManufacturerSpecification(
        manufacturer="Viking",
        model_number="VK302",
        equipment_category=EquipmentCategory.SPRINKLER_HEAD,
        product_name="Standard Response Upright Sprinkler",
        temperature=TemperatureSpec(
            operating_temp_max=155.0,
            temperature_unit="F",
        ),
        pressure=PressureSpec(
            operating_pressure_min=7.0,
            operating_pressure_nominal=15.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="1/2\" NPT",
        ),
        common_issues=[
            "Corrosion in humid environments",
            "Paint buildup affecting thermal element",
        ],
        maintenance_notes="Replace every 50 years per NFPA 25. Inspect annually for corrosion.",
        data_source="Viking Model VK302 Technical Data Sheet",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Tyco",
        model_number="TY3251",
        equipment_category=EquipmentCategory.SPRINKLER_HEAD,
        product_name="Quick Response Pendent Sprinkler",
        temperature=TemperatureSpec(
            operating_temp_max=165.0,
            temperature_unit="F",
        ),
        pressure=PressureSpec(
            operating_pressure_min=7.0,
            operating_pressure_nominal=20.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="1/2\" NPT",
        ),
        maintenance_notes="Quick response element - replace every 50 years. Check for damage during annual inspection.",
        data_source="Tyco TY3251 Product Datasheet",
        last_updated="2024-10",
    ),
]


# Fire Extinguisher Specifications
FIRE_EXTINGUISHERS = [
    ManufacturerSpecification(
        manufacturer="Ansul",
        model_number="A410",
        equipment_category=EquipmentCategory.FIRE_EXTINGUISHER,
        product_name="Dry Chemical Fire Extinguisher - 10 lb ABC",
        pressure=PressureSpec(
            operating_pressure_nominal=195.0,
            operating_pressure_min=175.0,
            operating_pressure_max=215.0,
            test_pressure=480.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            weight=15.5,
            dimensions="20\" H x 5.5\" Dia",
        ),
        common_issues=[
            "Pressure loss - recharge required",
            "Hose cracking after 5-7 years",
            "Valve stem corrosion",
        ],
        maintenance_notes="Monthly pressure check. Annual maintenance. 6-year teardown. 12-year hydrostatic test.",
        data_source="Ansul A-Line Service Manual",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Amerex",
        model_number="B500",
        equipment_category=EquipmentCategory.FIRE_EXTINGUISHER,
        product_name="ABC Dry Chemical Extinguisher - 5 lb",
        pressure=PressureSpec(
            operating_pressure_nominal=195.0,
            operating_pressure_min=175.0,
            operating_pressure_max=215.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            weight=8.5,
            dimensions="15.5\" H x 4.5\" Dia",
        ),
        maintenance_notes="Monthly visual inspection. Annual professional service. 6-year internal exam.",
        data_source="Amerex B500 Owner's Manual",
        last_updated="2024-10",
    ),
]


# HVAC Equipment Specifications (for mixed fire safety/HVAC companies)
HVAC_EQUIPMENT = [
    ManufacturerSpecification(
        manufacturer="Carrier",
        model_number="50A4-030",
        product_name="Carrier 50A4 30-Ton Horizontal Packaged Rooftop Unit",
        equipment_category=EquipmentCategory.HVAC,
        electrical=ElectricalSpec(
            amp_draw_nominal=115.0,
            amp_draw_min=100.0,
            amp_draw_max=128.0,
            voltage=460.0,
            phase=3,
            frequency=60,
            capacitor_microfarads=75.0,
        ),
        temperature=TemperatureSpec(
            temperature_delta_nominal=20.0,
            operating_temp_min=-20.0,
            operating_temp_max=125.0,
            temperature_unit="F",
        ),
        physical=PhysicalSpec(
            filter_size="24x24x4",
            dimensions="180 x 80 x 72",
            weight=3400.0,
        ),
        common_issues=[
            "Capacitor failure - typical 5-7 year lifespan",
            "Economizer damper stuck - common on rooftop units",
            "Low refrigerant charge - check for leaks",
            "Compressor short cycling",
        ],
        maintenance_notes="Change filters quarterly. Check refrigerant charge annually. Clean coils semi-annually. Inspect economizer operation.",
        data_source="Carrier 50A Series Service Manual",
        last_updated="2025-01",
    ),
    ManufacturerSpecification(
        manufacturer="Daikin",
        model_number="FTXS12WVJU9",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Daikin Wall-Mounted Ductless Heat Pump - 12K BTU",
        electrical=ElectricalSpec(
            amp_draw_nominal=0.6,
            amp_draw_max=1.2,
            voltage=230.0,
            phase=1,
            frequency=60,
        ),
        temperature=TemperatureSpec(
            operating_temp_min=-13.0,
            operating_temp_max=115.0,
            temperature_unit="F",
        ),
        common_issues=[
            "Drain line clogging - clean annually",
            "Remote control battery failure",
            "Filter clogging - clean monthly",
        ],
        maintenance_notes="Clean filters monthly. Professional service annually. Check drain line quarterly.",
        data_source="Daikin FTXS Installation Manual",
        last_updated="2024-10",
    ),
]


# Fire Alarm Panel Specifications
FIRE_ALARM_PANELS = [
    ManufacturerSpecification(
        manufacturer="Notifier",
        model_number="NFS2-3030",
        equipment_category=EquipmentCategory.FIRE_ALARM_PANEL,
        product_name="Intelligent Fire Alarm Control Panel",
        electrical=ElectricalSpec(
            voltage=120.0,
            amp_draw_nominal=3.5,
            phase=1,
            frequency=60,
        ),
        common_issues=[
            "Battery backup failure after 4-5 years",
            "Ground fault errors - check wiring",
            "NAC circuit supervision issues",
        ],
        maintenance_notes="Quarterly inspection. Annual load test on batteries. Replace batteries every 5 years.",
        data_source="Notifier NFS2-3030 Installation Manual",
        last_updated="2024-10",
    ),
]


# Additional HVAC Equipment - Major Manufacturers
ADDITIONAL_HVAC = [
    # Trane Heat Pumps
    ManufacturerSpecification(
        manufacturer="Trane",
        model_number="XR16",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Trane XR16 Heat Pump 4 Ton",
        electrical=ElectricalSpec(
            amp_draw_nominal=20.5,
            voltage=208.0,
            phase=1,
            frequency=60,
            capacitor_microfarads=60.0,
        ),
        temperature=TemperatureSpec(
            temperature_delta_nominal=20.0,
            operating_temp_min=-10.0,
            operating_temp_max=120.0,
            temperature_unit="F",
        ),
        physical=PhysicalSpec(
            filter_size="20x25x5",
        ),
        common_issues=[
            "Compressor contactor failure - 5-7 years",
            "Defrost control board issues in cold climates",
            "TXV valve sticking",
        ],
        data_source="Trane XR16 Installation Manual",
        last_updated="2024-10",
    ),
    # Lennox AC Units
    ManufacturerSpecification(
        manufacturer="Lennox",
        model_number="EL16XC1",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Lennox Elite Series 16 SEER AC - 3 Ton",
        electrical=ElectricalSpec(
            amp_draw_nominal=18.2,
            voltage=230.0,
            phase=1,
            frequency=60,
            capacitor_microfarads=55.0,
        ),
        physical=PhysicalSpec(
            filter_size="16x25x4",
        ),
        common_issues=[
            "Capacitor failure typical at 5-6 years",
            "Condenser fan motor bearing wear",
            "Refrigerant leaks at service ports",
        ],
        data_source="Lennox EL16XC1 Service Manual",
        last_updated="2024-10",
    ),
    # Goodman AC Units
    ManufacturerSpecification(
        manufacturer="Goodman",
        model_number="GSX140361",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Goodman 14 SEER AC - 3 Ton",
        electrical=ElectricalSpec(
            amp_draw_nominal=17.5,
            voltage=208.0,
            phase=1,
            frequency=60,
            capacitor_microfarads=50.0,
        ),
        physical=PhysicalSpec(
            filter_size="16x20x1",
        ),
        common_issues=[
            "Run capacitor failure - very common at 4-6 years",
            "Contactor welding/pitting",
            "Low refrigerant charge from factory",
        ],
        data_source="Goodman GSX Series Documentation",
        last_updated="2024-10",
    ),
    # Rheem Heat Pumps
    ManufacturerSpecification(
        manufacturer="Rheem",
        model_number="RP1636AJ1NA",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Rheem Classic Plus 16 SEER Heat Pump - 3 Ton",
        electrical=ElectricalSpec(
            amp_draw_nominal=19.0,
            voltage=208.0,
            phase=1,
            frequency=60,
        ),
        physical=PhysicalSpec(
            filter_size="16x25x1",
        ),
        common_issues=[
            "Reversing valve solenoid failure",
            "Defrost sensor failure in heating mode",
            "Outdoor fan motor capacitor failure",
        ],
        data_source="Rheem Classic Plus Service Guide",
        last_updated="2024-10",
    ),
    # York AC Units
    ManufacturerSpecification(
        manufacturer="York",
        model_number="YHJD36S41S",
        equipment_category=EquipmentCategory.HVAC,
        product_name="York Affinity Series 16 SEER AC - 3 Ton",
        electrical=ElectricalSpec(
            amp_draw_nominal=16.8,
            voltage=230.0,
            phase=1,
            frequency=60,
            capacitor_microfarads=55.0,
        ),
        common_issues=[
            "Compressor hard start kit needed after 7+ years",
            "Control board moisture damage",
        ],
        data_source="York Affinity Installation Manual",
        last_updated="2024-10",
    ),
    # Mitsubishi Ductless
    ManufacturerSpecification(
        manufacturer="Mitsubishi",
        model_number="MSZ-FH12NA",
        equipment_category=EquipmentCategory.HVAC,
        product_name="Mitsubishi Hyper-Heat 12K BTU Ductless",
        electrical=ElectricalSpec(
            amp_draw_nominal=0.7,
            voltage=230.0,
            phase=1,
            frequency=60,
        ),
        temperature=TemperatureSpec(
            operating_temp_min=-13.0,
            operating_temp_max=115.0,
            temperature_unit="F",
        ),
        common_issues=[
            "Drain pump failure in condensate line",
            "Indoor fan motor bearing noise",
            "Remote control signal issues",
        ],
        data_source="Mitsubishi MSZ-FH Service Manual",
        last_updated="2024-10",
    ),
]

# Additional Fire Safety Equipment
ADDITIONAL_FIRE_SAFETY = [
    # More Fire Extinguishers
    ManufacturerSpecification(
        manufacturer="Badger",
        model_number="B-20-PK",
        equipment_category=EquipmentCategory.FIRE_EXTINGUISHER,
        product_name="Badger 20lb ABC Fire Extinguisher",
        pressure=PressureSpec(
            operating_pressure_nominal=195.0,
            operating_pressure_min=175.0,
            operating_pressure_max=215.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            weight=27.0,
            dimensions="25\" H x 7\" Dia",
        ),
        common_issues=[
            "Pressure gauge failure",
            "Hose degradation from UV exposure",
        ],
        data_source="Badger Fire Extinguisher Manual",
        last_updated="2024-10",
    ),
    # Fire Alarm Devices
    ManufacturerSpecification(
        manufacturer="System Sensor",
        model_number="2WTA-B",
        equipment_category=EquipmentCategory.SMOKE_DETECTOR,
        product_name="System Sensor 2-Wire Photoelectric Smoke Detector",
        electrical=ElectricalSpec(
            voltage=24.0,
            amp_draw_nominal=0.04,
        ),
        common_issues=[
            "Dust accumulation causing false alarms",
            "Chamber degradation after 10 years",
        ],
        maintenance_notes="Replace every 10 years per NFPA 72. Clean annually.",
        data_source="System Sensor Installation Guide",
        last_updated="2024-10",
    ),
    # More Backflow Preventers
    ManufacturerSpecification(
        manufacturer="Wilkins",
        model_number="975XL",
        equipment_category=EquipmentCategory.BACKFLOW_PREVENTER,
        product_name="Wilkins 975XL Reduced Pressure Backflow Preventer",
        pressure=PressureSpec(
            operating_pressure_max=175.0,
            test_pressure=200.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="2\" Flanged",
            weight=55.0,
        ),
        common_issues=[
            "Relief valve dripping - diaphragm wear",
            "Check valve fouling from debris",
        ],
        data_source="Wilkins 975XL Service Manual",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Febco",
        model_number="860",
        equipment_category=EquipmentCategory.BACKFLOW_PREVENTER,
        product_name="Febco 860 Reduced Pressure Backflow Preventer",
        pressure=PressureSpec(
            operating_pressure_max=150.0,
            test_pressure=175.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="3\" NPT",
        ),
        common_issues=[
            "Air inlet valve weeping",
            "Spring fatigue in check valves",
        ],
        data_source="Febco 860 Technical Manual",
        last_updated="2024-10",
    ),
    # Additional Sprinkler Heads
    ManufacturerSpecification(
        manufacturer="Reliable",
        model_number="F1FR56",
        equipment_category=EquipmentCategory.SPRINKLER_HEAD,
        product_name="Reliable Quick Response Pendent Sprinkler",
        temperature=TemperatureSpec(
            operating_temp_max=155.0,
            temperature_unit="F",
        ),
        pressure=PressureSpec(
            operating_pressure_min=7.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="1/2\" NPT",
        ),
        maintenance_notes="Replace every 50 years per NFPA 25.",
        data_source="Reliable Sprinkler Catalog",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Victaulic",
        model_number="V2705",
        equipment_category=EquipmentCategory.SPRINKLER_HEAD,
        product_name="Victaulic FireLock Quick Response Sprinkler",
        temperature=TemperatureSpec(
            operating_temp_max=165.0,
            temperature_unit="F",
        ),
        pressure=PressureSpec(
            operating_pressure_min=7.0,
            pressure_unit="PSI",
        ),
        physical=PhysicalSpec(
            thread_size="1/2\" NPT",
        ),
        data_source="Victaulic FireLock Documentation",
        last_updated="2024-10",
    ),
    # Fire Pumps
    ManufacturerSpecification(
        manufacturer="Grundfos",
        model_number="CR64-2-2",
        equipment_category=EquipmentCategory.FIRE_PUMP,
        product_name="Grundfos Vertical Multistage Fire Pump",
        electrical=ElectricalSpec(
            amp_draw_nominal=45.0,
            voltage=460.0,
            phase=3,
            frequency=60,
        ),
        pressure=PressureSpec(
            operating_pressure_nominal=105.0,
            test_pressure=157.5,
            pressure_unit="PSI",
        ),
        flow=FlowSpec(
            flow_rate_nominal=1750.0,
            flow_unit="GPM",
        ),
        common_issues=[
            "Shaft seal leakage",
            "Bearing wear",
            "Impeller cavitation damage",
        ],
        data_source="Grundfos Fire Pump Manual",
        last_updated="2024-10",
    ),
    ManufacturerSpecification(
        manufacturer="Xylem",
        model_number="e-1510",
        equipment_category=EquipmentCategory.FIRE_PUMP,
        product_name="Xylem/Bell & Gossett Horizontal Split Case Fire Pump",
        electrical=ElectricalSpec(
            amp_draw_nominal=50.0,
            voltage=480.0,
            phase=3,
            frequency=60,
        ),
        pressure=PressureSpec(
            operating_pressure_nominal=110.0,
            pressure_unit="PSI",
        ),
        flow=FlowSpec(
            flow_rate_nominal=1500.0,
            flow_unit="GPM",
        ),
        common_issues=[
            "Mechanical seal failure",
            "Coupling misalignment",
            "Bearing overheating",
        ],
        data_source="Xylem e-1510 Documentation",
        last_updated="2024-10",
    ),
]

# Compile all specifications into searchable database
ALL_SPECIFICATIONS = (
    FIRE_PUMPS +
    BACKFLOW_PREVENTERS +
    SPRINKLER_HEADS +
    FIRE_EXTINGUISHERS +
    HVAC_EQUIPMENT +
    FIRE_ALARM_PANELS +
    ADDITIONAL_HVAC +
    ADDITIONAL_FIRE_SAFETY
)


# Create lookup dictionaries for fast access
SPECS_BY_MODEL = {
    spec.model_number: spec for spec in ALL_SPECIFICATIONS
}

SPECS_BY_MANUFACTURER = {}
for spec in ALL_SPECIFICATIONS:
    if spec.manufacturer not in SPECS_BY_MANUFACTURER:
        SPECS_BY_MANUFACTURER[spec.manufacturer] = []
    SPECS_BY_MANUFACTURER[spec.manufacturer].append(spec)
