"""Gate resistance dependent switching energy interpolation.

Interpolates switching loss energy as a function of gate resistance (Rg),
current, and temperature. Supports both direct Rg-Energy curves and
formula-based scaling from reference data.
"""
from __future__ import annotations

import math

import numpy as np

from transistordatabase.core.models import SwitchingLossData


def interpolate_energy_at_rg(
    loss_data: list[SwitchingLossData],
    r_g: float,
    i_channel: float,
    t_j: float,
) -> float:
    """Find switching energy for a given gate resistance.

    If ``graph_r_e`` data is available on any dataset matching the temperature,
    interpolate directly on the resistance-energy curve.  Otherwise, find the
    dataset whose ``r_g`` value is closest to the requested value among those
    that carry ``graph_i_e`` data at the matching temperature, and interpolate
    the current on that curve.

    :param loss_data: List of SwitchingLossData objects to search.
    :param r_g: Target gate resistance in Ohm.
    :param i_channel: Channel current in A.
    :param t_j: Junction temperature in deg C.
    :return: Interpolated switching energy in J, or 0.0 when no data matches.
    """
    if not loss_data:
        return 0.0

    # Strategy 1: direct Rg-Energy curve at matching temperature
    for entry in loss_data:
        if entry.t_j == t_j and entry.graph_r_e is not None:
            resistances = entry.graph_r_e[0]
            energies = entry.graph_r_e[1]
            return float(np.interp(r_g, resistances, energies))

    # Strategy 2: closest r_g among graph_i_e datasets at matching temperature
    candidates = [
        entry
        for entry in loss_data
        if entry.t_j == t_j
        and entry.graph_i_e is not None
        and entry.r_g is not None
    ]

    if not candidates:
        return 0.0

    best = min(candidates, key=lambda e: abs(e.r_g - r_g))  # type: ignore[arg-type]
    currents = best.graph_i_e[0]  # type: ignore[index]
    energies = best.graph_i_e[1]  # type: ignore[index]
    return float(np.interp(i_channel, currents, energies))


def scale_energy_by_rg(
    e_ref: float,
    r_g_ref: float,
    r_g_target: float,
    scaling: str = "linear",
) -> float:
    """Scale a reference switching energy to a different gate resistance.

    :param e_ref: Reference switching energy in J.
    :param r_g_ref: Reference gate resistance in Ohm.
    :param r_g_target: Target gate resistance in Ohm.
    :param scaling: Scaling law to apply. ``"linear"`` uses
        ``E_target = E_ref * r_g_target / r_g_ref``.  ``"sqrt"`` uses
        ``E_target = E_ref * sqrt(r_g_target / r_g_ref)``.
    :return: Scaled switching energy in J.
    :raises ValueError: If *scaling* is not ``"linear"`` or ``"sqrt"``.
    :raises ZeroDivisionError: If *r_g_ref* is zero.
    """
    if r_g_ref == 0.0:
        raise ZeroDivisionError(
            "Reference gate resistance r_g_ref must not be zero"
        )

    if scaling == "linear":
        return e_ref * r_g_target / r_g_ref
    if scaling == "sqrt":
        return e_ref * math.sqrt(r_g_target / r_g_ref)

    raise ValueError(
        f"Unknown scaling method '{scaling}'. Use 'linear' or 'sqrt'."
    )


def find_rg_for_target_energy(
    loss_data: list[SwitchingLossData],
    e_target: float,
    i_channel: float,
    t_j: float,
) -> float | None:
    """Find the gate resistance that produces a target switching energy.

    Searches datasets that carry ``graph_r_e`` curves at the given temperature.
    If multiple ``graph_r_e`` datasets exist the first match is used.  Falls
    back to building an (r_g, energy) mapping from ``graph_i_e`` datasets when
    no ``graph_r_e`` data is available.

    :param loss_data: List of SwitchingLossData objects to search.
    :param e_target: Target switching energy in J.
    :param i_channel: Channel current in A.
    :param t_j: Junction temperature in deg C.
    :return: Gate resistance in Ohm, or ``None`` if no solution is found.
    """
    if not loss_data:
        return None

    # Strategy 1: use graph_r_e directly
    for entry in loss_data:
        if entry.t_j == t_j and entry.graph_r_e is not None:
            resistances = entry.graph_r_e[0]
            energies = entry.graph_r_e[1]

            e_min = float(np.min(energies))
            e_max = float(np.max(energies))
            if e_target < e_min or e_target > e_max:
                return None

            return float(np.interp(e_target, energies, resistances))

    # Strategy 2: build r_g vs energy from graph_i_e datasets
    candidates = [
        entry
        for entry in loss_data
        if entry.t_j == t_j
        and entry.graph_i_e is not None
        and entry.r_g is not None
    ]

    if len(candidates) < 2:
        return None

    # Sort by r_g and interpolate energy at the requested current for each
    candidates.sort(key=lambda e: e.r_g)  # type: ignore[arg-type]
    rg_values = np.array([c.r_g for c in candidates])
    energy_values = np.array([
        float(np.interp(i_channel, c.graph_i_e[0], c.graph_i_e[1]))  # type: ignore[index]
        for c in candidates
    ])

    e_min = float(np.min(energy_values))
    e_max = float(np.max(energy_values))
    if e_target < e_min or e_target > e_max:
        return None

    return float(np.interp(e_target, energy_values, rg_values))


def get_available_rg_values(
    loss_data: list[SwitchingLossData],
) -> list[float]:
    """Extract all unique gate resistance values from switching loss datasets.

    Collects ``r_g`` values that are explicitly set on the provided
    :class:`SwitchingLossData` objects.

    :param loss_data: List of SwitchingLossData objects.
    :return: Sorted list of unique Rg values.
    """
    rg_set: set[float] = set()
    for entry in loss_data:
        if entry.r_g is not None:
            rg_set.add(entry.r_g)
    return sorted(rg_set)
