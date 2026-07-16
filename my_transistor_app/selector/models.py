"""
Pydantic V2 models for the transistor selector.

All voltages in V, currents in A, frequencies in Hz, energies in J,
powers in W, temperatures in °C, resistances in Ω.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Topology(str, Enum):
    BUCK = "buck"
    BOOST = "boost"
    HALF_BRIDGE = "half_bridge"   # generic phase-leg / inverter


class TransistorType(str, Enum):
    MOSFET = "MOSFET"
    SIC_MOSFET = "SiC-MOSFET"
    IGBT = "IGBT"
    GAN = "GaN-Transistor"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CircuitRequirements(BaseModel):
    """User-supplied operating-point for transistor selection."""

    topology: Topology = Field(
        default=Topology.HALF_BRIDGE,
        description="Converter topology",
    )
    v_bus: float = Field(
        gt=0,
        description="DC-bus voltage [V]. "
                    "For boost: this is the output (high) side voltage.",
    )
    i_load: float = Field(
        gt=0,
        description="Load current [A]. "
                    "Buck/boost: DC average output current. "
                    "Half-bridge: peak sinusoidal current.",
    )
    f_sw: float = Field(
        gt=0,
        description="Switching frequency [Hz].",
    )
    v_out: Optional[float] = Field(
        default=None,
        gt=0,
        description="Second-port voltage [V]. "
                    "Buck: output voltage. "
                    "Boost: input (low) voltage. "
                    "Half-bridge: not used (D fixed at 0.5).",
    )
    t_j_op: float = Field(
        default=125.0,
        ge=-55.0,
        le=200.0,
        description="Target junction temperature for operating-point lookup [°C].",
    )
    v_g: float = Field(
        default=15.0,
        description="Gate-drive voltage for on-state [V].",
    )
    r_g_ext: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="External gate resistance [Ω]. "
                    "If None, transistor's r_g_int is used.",
    )
    v_margin: float = Field(
        default=1.5,
        ge=1.0,
        le=10.0,
        description="Minimum ratio V_abs_max / V_bus (voltage derating).",
    )
    i_margin: float = Field(
        default=1.5,
        ge=1.0,
        le=10.0,
        description="Minimum ratio I_abs_max / I_peak (current derating).",
    )
    allowed_types: Optional[list[TransistorType]] = Field(
        default=None,
        description="Restrict to specific transistor types. None = all types.",
    )
    max_results: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of ranked results to return.",
    )

    @model_validator(mode="after")
    def _validate_v_out(self) -> "CircuitRequirements":
        if self.topology in (Topology.BUCK, Topology.BOOST) and self.v_out is None:
            raise ValueError(
                f"v_out is required for the {self.topology} topology."
            )
        if self.topology == Topology.BUCK and self.v_out >= self.v_bus:
            raise ValueError(
                "Buck converter: v_out must be less than v_bus."
            )
        if self.topology == Topology.BOOST and self.v_out >= self.v_bus:
            raise ValueError(
                "Boost converter: v_out (input voltage) must be less than v_bus (output voltage)."
            )
        return self


# ---------------------------------------------------------------------------
# Intermediate computed waveforms  (not exposed to API consumers)
# ---------------------------------------------------------------------------

class CurrentWaveform(BaseModel):
    """Per-switch current waveform quantities derived from topology + specs."""

    duty_cycle: float = Field(description="Switch conduction duty cycle D.")
    i_sw_rms: float = Field(description="Switch RMS current [A].")
    i_sw_mean: float = Field(description="Switch average current [A].")
    i_diode_rms: float = Field(description="Anti-parallel diode RMS current [A].")
    i_diode_mean: float = Field(description="Anti-parallel diode average current [A].")
    i_peak: float = Field(description="Peak switching current [A] (used for E_on/E_off lookup).")


# ---------------------------------------------------------------------------
# Per-transistor loss breakdown
# ---------------------------------------------------------------------------

class LossBreakdown(BaseModel):
    """Estimated power losses for one transistor at the given operating point."""

    p_sw_cond_w: Optional[float] = Field(None, description="Switch conduction loss [W].")
    p_sw_on_w: Optional[float] = Field(None, description="Turn-on switching loss [W].")
    p_sw_off_w: Optional[float] = Field(None, description="Turn-off switching loss [W].")
    p_diode_cond_w: Optional[float] = Field(None, description="Diode/body-diode conduction loss [W].")
    p_diode_rr_w: Optional[float] = Field(None, description="Diode reverse-recovery loss [W].")
    p_total_w: float = Field(description="Total estimated loss [W] (sum of available components).")

    # Data provenance
    sw_channel_source: Optional[str] = Field(
        None,
        description="Operating point used for channel linearisation: 't_j=X, v_g=Y'.",
    )
    e_on_source: Optional[str] = Field(None, description="Dataset used for E_on interpolation.")
    e_off_source: Optional[str] = Field(None, description="Dataset used for E_off interpolation.")
    e_rr_source: Optional[str] = Field(None, description="Dataset used for E_rr interpolation.")
    e_on_v_scale: Optional[float] = Field(
        None,
        description="Voltage-scaling factor applied to E_on (V_bus / V_supply_meas).",
    )
    e_off_v_scale: Optional[float] = Field(None, description="Voltage-scaling factor for E_off.")


# ---------------------------------------------------------------------------
# Per-transistor result
# ---------------------------------------------------------------------------

class TransistorResult(BaseModel):
    """Single transistor in the ranked result list."""

    rank: int
    name: str
    transistor_type: str
    housing_type: str
    manufacturer: str
    v_abs_max: float = Field(description="Absolute max voltage [V].")
    i_abs_max: float = Field(description="Absolute max current [A].")
    i_cont: Optional[float] = Field(None, description="Continuous current rating [A].")
    t_j_max: float = Field(description="Maximum junction temperature [°C].")
    r_g_int: float = Field(description="Internal gate resistance [Ω].")
    r_th_cs: Optional[float] = Field(None, description="Case-to-sink thermal resistance [K/W].")

    # Derating
    v_derating: float = Field(description="V_abs_max / V_bus voltage margin.")
    i_derating: float = Field(description="I_abs_max / I_peak current margin.")

    # Loss estimate
    losses: LossBreakdown

    # Confidence
    data_confidence_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of loss components that could be estimated (0–100).",
    )

    # Flags
    missing_data_notes: list[str] = Field(
        default_factory=list,
        description="Notes on which data was missing or approximated.",
    )

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Selection response
# ---------------------------------------------------------------------------

class SelectionResponse(BaseModel):
    """Full response from the transistor selector."""

    requirements: CircuitRequirements
    waveform: CurrentWaveform
    results: list[TransistorResult]
    total_candidates: int = Field(description="Transistors that passed voltage/current filters.")
    total_in_db: int = Field(description="Total transistors in the loaded database.")
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    transistors_loaded: int
    db_path: str
