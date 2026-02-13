"""Import transistor data from PLECS XML semiconductor library files.

Parses PLECS .xml semiconductor library files and maps them to core domain models.
Supports switch and diode packages with conduction loss, switching loss, and
Foster thermal model data.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import xmltodict

from transistordatabase.core.models import (
    ChannelCharacteristics,
    Diode,
    ElectricalRatings,
    FosterThermalModel,
    Switch,
    SwitchingLossData,
    ThermalProperties,
    Transistor,
    TransistorMetadata,
)


def import_plecs_xml(file_path: str | Path) -> list[Transistor]:
    """Import transistor(s) from a PLECS XML semiconductor library file.

    :param file_path: Path to the PLECS XML file.
    :return: List of Transistor objects parsed from the file.
    :raises FileNotFoundError: If the file does not exist.
    :raises ValueError: If the XML structure is invalid.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PLECS XML file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = xmltodict.parse(content)
    lib = parsed.get("SemiconductorLibrary")
    if lib is None:
        raise ValueError("Invalid PLECS XML: missing SemiconductorLibrary root")

    packages = lib.get("Package", [])
    if isinstance(packages, dict):
        packages = [packages]

    transistors = []
    for pkg in packages:
        transistor = _parse_package(pkg)
        transistors.append(transistor)

    return transistors


def _parse_package(pkg: dict[str, Any]) -> Transistor:
    """Parse a single PLECS Package element into a Transistor.

    :param pkg: Parsed XML dict for one Package element.
    :return: Transistor domain object.
    """
    device_class = pkg.get("@class", "MOSFET")
    vendor = pkg.get("@vendor", "Unknown")
    partnumber = pkg.get("@partnumber", "Unknown")

    metadata = TransistorMetadata(
        name=partnumber,
        type=_map_plecs_type(device_class),
        author="PLECS Import",
        manufacturer=vendor,
        housing_type="",
    )

    electrical = ElectricalRatings(
        v_abs_max=0.0,
        i_abs_max=0.0,
        i_cont=0.0,
        t_j_max=175.0,
    )

    thermal = ThermalProperties(
        housing_area=0.0,
        cooling_area=0.0,
    )

    transistor = Transistor(metadata, electrical, thermal)

    semi_data = pkg.get("SemiconductorData", {})
    semi_type = semi_data.get("@type", device_class)

    # Parse conduction loss -> channel characteristics
    cond_loss = semi_data.get("ConductionLoss")
    if cond_loss:
        channels = _parse_conduction_loss(cond_loss)
        if _is_diode_type(semi_type):
            transistor.diode.channel_data = channels
        else:
            transistor.switch.channel_data = channels

    # Parse turn-on loss
    turn_on = semi_data.get("TurnOnLoss")
    if turn_on:
        e_on_list = _parse_switching_loss(turn_on)
        transistor.switch.e_on_data = e_on_list

    # Parse turn-off loss
    turn_off = semi_data.get("TurnOffLoss")
    if turn_off:
        e_off_list = _parse_switching_loss(turn_off)
        if _is_diode_type(semi_type):
            transistor.diode.e_rr_data = e_off_list
        else:
            transistor.switch.e_off_data = e_off_list

    # Parse thermal model
    thermal_model = pkg.get("ThermalModel")
    if thermal_model:
        foster = _parse_thermal_model(thermal_model)
        if _is_diode_type(semi_type):
            transistor.diode.thermal_foster = foster
        else:
            transistor.switch.thermal_foster = foster

    # Extract max voltage from switching loss data for electrical ratings
    _infer_electrical_ratings(transistor)

    return transistor


def _parse_conduction_loss(
    cond_data: dict[str, Any],
) -> list[ChannelCharacteristics]:
    """Parse ConductionLoss XML element into ChannelCharacteristics list.

    :param cond_data: Parsed ConductionLoss dict.
    :return: List of ChannelCharacteristics at different temperatures.
    """
    current_axis = _parse_float_list(cond_data.get("CurrentAxis", ""))
    temp_axis = _parse_float_list(cond_data.get("TemperatureAxis", ""))

    voltage_drop = cond_data.get("VoltageDrop", {})
    scale = float(voltage_drop.get("@scale", "1"))

    temp_entries = voltage_drop.get("Temperature", [])
    if isinstance(temp_entries, str):
        temp_entries = [temp_entries]
    elif isinstance(temp_entries, dict):
        temp_entries = [temp_entries]

    channels = []
    for i, temp_entry in enumerate(temp_entries):
        if isinstance(temp_entry, dict):
            voltages_str = temp_entry.get("#text", "")
        else:
            voltages_str = str(temp_entry)

        voltages = np.array(_parse_float_list(voltages_str)) * scale
        currents = np.array(current_axis)

        if len(voltages) != len(currents):
            continue

        t_j = temp_axis[i] if i < len(temp_axis) else 25.0

        graph_v_i = np.array([voltages, currents])
        channels.append(ChannelCharacteristics(
            t_j=t_j,
            graph_v_i=graph_v_i,
        ))

    return channels


def _parse_switching_loss(
    loss_data: dict[str, Any],
) -> list[SwitchingLossData]:
    """Parse TurnOnLoss or TurnOffLoss XML element.

    If the switching loss element or its ``Energy`` sub-element carries an
    ``@Rg`` attribute, the parsed gate resistance value is stored in the
    ``r_g`` field of every resulting :class:`SwitchingLossData` object.

    :param loss_data: Parsed switching loss dict.
    :return: List of SwitchingLossData at different conditions.
    """
    current_axis = _parse_float_list(loss_data.get("CurrentAxis", ""))
    voltage_axis = _parse_float_list(loss_data.get("VoltageAxis", ""))
    temp_axis = _parse_float_list(loss_data.get("TemperatureAxis", ""))

    # Extract gate resistance from attributes on the loss element itself
    # or from the Energy sub-element.  PLECS may store it as @Rg on either.
    r_g = _extract_rg(loss_data)

    energy_data = loss_data.get("Energy", {})
    scale = float(energy_data.get("@scale", "1"))

    if r_g is None:
        r_g = _extract_rg(energy_data)

    temp_entries = energy_data.get("Temperature", [])
    if isinstance(temp_entries, dict):
        temp_entries = [temp_entries]

    results = []
    for temp_idx, temp_entry in enumerate(temp_entries):
        t_j = temp_axis[temp_idx] if temp_idx < len(temp_axis) else 25.0

        voltage_entries = temp_entry.get("Voltage", [])
        if isinstance(voltage_entries, str):
            voltage_entries = [voltage_entries]

        for v_idx, v_entry in enumerate(voltage_entries):
            if isinstance(v_entry, dict):
                energy_str = v_entry.get("#text", "")
            else:
                energy_str = str(v_entry)

            energies = np.array(_parse_float_list(energy_str)) * scale
            currents = np.array(current_axis)

            if len(energies) != len(currents):
                continue

            v_supply = voltage_axis[v_idx] if v_idx < len(voltage_axis) else 0.0

            graph_i_e = np.array([currents, energies])
            results.append(SwitchingLossData(
                dataset_type="graph_i_e",
                t_j=t_j,
                v_supply=v_supply,
                v_g=0.0,
                r_g=r_g,
                graph_i_e=graph_i_e,
            ))

    return results


def _extract_rg(element: dict[str, Any]) -> float | None:
    """Extract gate resistance from an XML element's attributes.

    Looks for ``@Rg``, ``@rg``, or ``@GateResistance`` attributes.

    :param element: Parsed XML dict for an element.
    :return: Gate resistance in Ohm, or ``None`` if not present.
    """
    for key in ("@Rg", "@rg", "@GateResistance"):
        raw = element.get(key)
        if raw is not None:
            try:
                return float(raw)
            except (ValueError, TypeError):
                continue
    return None


def _parse_thermal_model(thermal_data: dict[str, Any]) -> FosterThermalModel:
    """Parse ThermalModel XML element into FosterThermalModel.

    :param thermal_data: Parsed ThermalModel dict.
    :return: FosterThermalModel with R and tau vectors.
    """
    branch = thermal_data.get("Branch", {})
    branch_type = branch.get("@type", "Foster")

    if branch_type != "Foster":
        return FosterThermalModel()

    elements = branch.get("RTauElement", [])
    if isinstance(elements, dict):
        elements = [elements]

    r_th_vector = []
    tau_vector = []

    for elem in elements:
        r_val = float(elem.get("@R", 0))
        tau_val = float(elem.get("@Tau", 0))
        r_th_vector.append(r_val)
        tau_vector.append(tau_val)

    r_th_total = sum(r_th_vector) if r_th_vector else None

    return FosterThermalModel(
        r_th_vector=r_th_vector if r_th_vector else None,
        tau_vector=tau_vector if tau_vector else None,
        r_th_total=r_th_total,
    )


def _parse_float_list(text: str) -> list[float]:
    """Parse a whitespace-separated string of numbers.

    :param text: Space-separated number string.
    :return: List of float values.
    """
    if not text or not text.strip():
        return []
    return [float(x) for x in text.split() if x.strip()]


def _map_plecs_type(plecs_class: str) -> str:
    """Map PLECS device class to core transistor type.

    :param plecs_class: PLECS class string (e.g. 'MOSFET', 'IGBT').
    :return: Core type string.
    """
    mapping = {
        "MOSFET": "MOSFET",
        "SiC MOSFET": "SiC-MOSFET",
        "IGBT": "IGBT",
        "Diode": "Diode",
        "GaN Transistor": "GaN-Transistor",
    }
    return mapping.get(plecs_class, plecs_class)


def _is_diode_type(semi_type: str) -> bool:
    """Check if the semiconductor type is a diode.

    :param semi_type: Semiconductor type string.
    :return: True if diode type.
    """
    return semi_type.lower() in ("diode", "bodydiode")


def _infer_electrical_ratings(transistor: Transistor) -> None:
    """Infer electrical ratings from available data.

    :param transistor: Transistor to update.
    """
    max_voltage = 0.0
    max_current = 0.0

    for data in transistor.switch.e_on_data + transistor.switch.e_off_data:
        max_voltage = max(max_voltage, data.v_supply)
        if data.graph_i_e is not None:
            max_current = max(max_current, float(np.max(data.graph_i_e[0])))

    for ch in transistor.switch.channel_data + transistor.diode.channel_data:
        max_current = max(max_current, float(np.max(ch.graph_v_i[1])))

    if max_voltage > 0:
        transistor.electrical_ratings.v_abs_max = max_voltage
    if max_current > 0:
        transistor.electrical_ratings.i_abs_max = max_current
        transistor.electrical_ratings.i_cont = max_current * 0.5
