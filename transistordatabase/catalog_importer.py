"""Import transistor data from manufacturer catalogs (CSV format).

Parses CSV catalog data (e.g., Digikey exports) and creates Transistor
objects with basic electrical ratings. Supports batch import and
Figure of Merit (FOM) calculations for device comparison.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from transistordatabase.core.models import (
    ElectricalRatings,
    ThermalProperties,
    Transistor,
    TransistorMetadata,
)


@dataclass
class CatalogEntry:
    """Parsed catalog entry with device parameters.

    :param part_number: Manufacturer part number.
    :param manufacturer: Device manufacturer.
    :param device_type: Device type (MOSFET, IGBT, etc.).
    :param v_ds_max: Maximum drain-source voltage in V.
    :param i_d_max: Maximum drain current in A.
    :param r_ds_on: On-state resistance in Ohm (MOSFET) or None.
    :param q_g: Total gate charge in C or None.
    :param v_ce_sat: Collector-emitter saturation voltage in V (IGBT) or None.
    :param package: Package type string.
    :param price: Unit price or None.
    """

    part_number: str
    manufacturer: str
    device_type: str = "MOSFET"
    v_ds_max: float = 0.0
    i_d_max: float = 0.0
    r_ds_on: Optional[float] = None
    q_g: Optional[float] = None
    v_ce_sat: Optional[float] = None
    package: str = ""
    price: Optional[float] = None

    def calc_fom_rds_qg(self) -> Optional[float]:
        """Calculate Rds(on) x Qg Figure of Merit.

        Lower is better. Returns None if data is missing.

        :return: FOM value in Ohm*C or None.
        """
        if self.r_ds_on is not None and self.q_g is not None:
            return self.r_ds_on * self.q_g
        return None

    def calc_fom_rds_area(self, die_area: float) -> Optional[float]:
        """Calculate specific on-resistance FOM (Rds*Area).

        :param die_area: Die area in mm^2.
        :return: Specific on-resistance in Ohm*mm^2 or None.
        """
        if self.r_ds_on is not None and die_area > 0:
            return self.r_ds_on * die_area
        return None


def parse_catalog_csv(
    file_path: str | Path,
    column_mapping: Optional[dict[str, str]] = None,
) -> list[CatalogEntry]:
    """Parse a CSV catalog file into CatalogEntry objects.

    :param file_path: Path to the CSV file.
    :param column_mapping: Optional mapping from CSV column names to CatalogEntry fields.
    :return: List of CatalogEntry objects.
    :raises FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Catalog CSV not found: {file_path}")

    default_mapping = {
        'part_number': ['Part Number', 'MPN', 'Manufacturer Part Number', 'PartNumber'],
        'manufacturer': ['Manufacturer', 'Mfr', 'Brand'],
        'device_type': ['Type', 'Device Type', 'Technology'],
        'v_ds_max': ['Voltage - Drain to Source', 'Vds', 'V_DS', 'Vdss', 'VDS_max'],
        'i_d_max': ['Current - Drain', 'Id', 'I_D', 'ID_max', 'Current - Continuous Drain'],
        'r_ds_on': ['Rds On', 'RDS(on)', 'Rds(on)', 'R_DS_on'],
        'q_g': ['Gate Charge', 'Qg', 'Q_g', 'Total Gate Charge'],
        'package': ['Package', 'Package / Case', 'Housing'],
        'price': ['Price', 'Unit Price'],
    }

    if column_mapping:
        for key, val in column_mapping.items():
            default_mapping[key] = [val] if isinstance(val, str) else val

    entries = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return entries

        # Build actual column name mapping
        field_map: dict[str, str] = {}
        for field, candidates in default_mapping.items():
            for candidate in candidates:
                if candidate in reader.fieldnames:
                    field_map[field] = candidate
                    break

        for row in reader:
            entry = _parse_row(row, field_map)
            if entry is not None:
                entries.append(entry)

    return entries


def catalog_to_transistors(entries: list[CatalogEntry]) -> list[Transistor]:
    """Convert catalog entries to Transistor domain objects.

    :param entries: List of CatalogEntry objects.
    :return: List of Transistor objects with basic ratings.
    """
    transistors = []
    for entry in entries:
        metadata = TransistorMetadata(
            name=entry.part_number,
            type=entry.device_type,
            author="Catalog Import",
            manufacturer=entry.manufacturer,
            housing_type=entry.package,
        )

        electrical = ElectricalRatings(
            v_abs_max=entry.v_ds_max,
            i_abs_max=entry.i_d_max,
            i_cont=entry.i_d_max * 0.7,  # Estimate continuous at 70% of max
            t_j_max=175.0,
        )

        thermal = ThermalProperties(
            housing_area=0.0,
            cooling_area=0.0,
        )

        transistor = Transistor(metadata, electrical, thermal)
        transistors.append(transistor)

    return transistors


def rank_by_fom(
    entries: list[CatalogEntry],
    fom_type: str = "rds_qg",
) -> list[tuple[CatalogEntry, float]]:
    """Rank catalog entries by Figure of Merit.

    :param entries: List of CatalogEntry objects.
    :param fom_type: FOM type ('rds_qg' for Rds*Qg).
    :return: Sorted list of (entry, fom_value) tuples. Lower FOM is better.
    """
    ranked = []
    for entry in entries:
        if fom_type == "rds_qg":
            fom = entry.calc_fom_rds_qg()
        else:
            fom = None

        if fom is not None:
            ranked.append((entry, fom))

    ranked.sort(key=lambda x: x[1])
    return ranked


def _parse_row(
    row: dict[str, str], field_map: dict[str, str]
) -> Optional[CatalogEntry]:
    """Parse a single CSV row into a CatalogEntry.

    :param row: CSV row dict.
    :param field_map: Mapping from CatalogEntry fields to CSV column names.
    :return: CatalogEntry or None if required fields are missing.
    """
    part_number = _get_str(row, field_map.get('part_number', ''))
    if not part_number:
        return None

    return CatalogEntry(
        part_number=part_number,
        manufacturer=_get_str(row, field_map.get('manufacturer', ''), 'Unknown'),
        device_type=_get_str(row, field_map.get('device_type', ''), 'MOSFET'),
        v_ds_max=_parse_voltage(row.get(field_map.get('v_ds_max', ''), '')),
        i_d_max=_parse_current(row.get(field_map.get('i_d_max', ''), '')),
        r_ds_on=_parse_resistance(row.get(field_map.get('r_ds_on', ''), '')),
        q_g=_parse_charge(row.get(field_map.get('q_g', ''), '')),
        package=_get_str(row, field_map.get('package', ''), ''),
        price=_parse_float_safe(row.get(field_map.get('price', ''), '')),
    )


def _get_str(row: dict[str, str], column: str, default: str = '') -> str:
    """Get string value from CSV row.

    :param row: CSV row dict.
    :param column: Column name.
    :param default: Default value.
    :return: String value.
    """
    if not column:
        return default
    return row.get(column, default).strip()


def _parse_float_safe(value: str) -> Optional[float]:
    """Safely parse a float from string, handling units and special chars.

    :param value: String value.
    :return: Float value or None.
    """
    if not value or not value.strip():
        return None
    # Remove common unit suffixes and special characters
    cleaned = value.strip().replace(',', '').replace('$', '')
    for suffix in ['V', 'A', 'W', 'F', 'C', 'Hz', 'Ohm']:
        cleaned = cleaned.replace(suffix, '')
    cleaned = cleaned.strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_voltage(value: str) -> float:
    """Parse voltage value with unit handling.

    :param value: String like '650V' or '650'.
    :return: Voltage in V.
    """
    result = _parse_float_safe(value)
    return result if result is not None else 0.0


def _parse_current(value: str) -> float:
    """Parse current value with unit handling.

    :param value: String like '30A' or '30'.
    :return: Current in A.
    """
    result = _parse_float_safe(value)
    return result if result is not None else 0.0


def _parse_resistance(value: str) -> Optional[float]:
    """Parse resistance value with unit handling.

    Handles mOhm notation.

    :param value: String like '60mOhm' or '0.06'.
    :return: Resistance in Ohm or None.
    """
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    multiplier = 1.0
    if 'mOhm' in cleaned or 'mohm' in cleaned.lower():
        multiplier = 1e-3
        cleaned = cleaned.lower().replace('mohm', '').strip()
    elif 'uOhm' in cleaned or 'uohm' in cleaned.lower():
        multiplier = 1e-6
        cleaned = cleaned.lower().replace('uohm', '').strip()
    result = _parse_float_safe(cleaned)
    return result * multiplier if result is not None else None


def _parse_charge(value: str) -> Optional[float]:
    """Parse gate charge value with unit handling.

    Handles nC notation.

    :param value: String like '50nC' or '50e-9'.
    :return: Charge in C or None.
    """
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    multiplier = 1.0
    if 'nC' in cleaned or 'nc' in cleaned.lower():
        multiplier = 1e-9
        cleaned = cleaned.lower().replace('nc', '').strip()
    elif 'uC' in cleaned or 'uc' in cleaned.lower():
        multiplier = 1e-6
        cleaned = cleaned.lower().replace('uc', '').strip()
    result = _parse_float_safe(cleaned)
    return result * multiplier if result is not None else None
