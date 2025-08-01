"""
Core domain models for the transistor database.
These models represent the core business entities.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any
import numpy as np
import numpy.typing as npt
from datetime import datetime
from abc import ABC, abstractmethod


@dataclass
class TransistorMetadata:
    """Core metadata for a transistor."""
    name: str
    type: str  # IGBT, MOSFET, SiC-MOSFET, etc.
    author: str
    manufacturer: str
    housing_type: str
    comment: Optional[str] = None
    datasheet_hyperlink: Optional[str] = None
    datasheet_date: Optional[datetime] = None
    datasheet_version: Optional[str] = None


@dataclass
class ElectricalRatings:
    """Electrical ratings and limits."""
    v_abs_max: float  # V
    i_abs_max: float  # A
    i_cont: float     # A
    t_j_max: float    # °C


@dataclass
class ThermalProperties:
    """Thermal properties of the transistor."""
    housing_area: float    # m²
    cooling_area: float    # m²
    r_th_cs: Optional[float] = None      # K/W
    r_th_switch_cs: Optional[float] = None  # K/W
    r_th_diode_cs: Optional[float] = None   # K/W
    t_c_max: Optional[float] = None      # °C


@dataclass
class ChannelCharacteristics:
    """V-I characteristics for a channel at specific conditions."""
    t_j: float  # Junction temperature in °C
    graph_v_i: npt.NDArray[np.float64]  # 2D array: [voltage, current]
    v_g: Optional[float] = None  # Gate voltage (mandatory for switch, optional for diode)
    
    def get_resistance_at_current(self, current: float) -> float:
        """Calculate channel resistance at specific current."""
        # Implementation here
        pass


@dataclass 
class SwitchingLossData:
    """Switching loss characteristics."""
    dataset_type: str  # 'single', 'graph_i_e', 'graph_r_e'
    t_j: float        # °C
    v_supply: float   # V
    v_g: float        # V
    
    # One of these will be None based on dataset_type
    e_x: Optional[float] = None  # Single point energy
    r_g: Optional[float] = None  # Gate resistance
    i_x: Optional[float] = None  # Current point
    graph_i_e: Optional[npt.NDArray[np.float64]] = None  # Energy vs Current
    graph_r_e: Optional[npt.NDArray[np.float64]] = None  # Energy vs Resistance


class ITransistorComponent(ABC):
    """Interface for transistor components (Switch/Diode)."""
    
    @abstractmethod
    def get_channel_data(self, t_j: float, v_g: Optional[float] = None) -> List[ChannelCharacteristics]:
        """Get channel characteristics for given conditions."""
        pass
    
    @abstractmethod
    def linearize_at_operating_point(self, t_j: float, v_g: float, i_channel: float) -> Dict[str, float]:
        """Linearize component at specific operating point."""
        pass


class Switch(ITransistorComponent):
    """Switch component with all switching characteristics."""
    
    def __init__(self):
        self.channel_data: List[ChannelCharacteristics] = []
        self.e_on_data: List[SwitchingLossData] = []
        self.e_off_data: List[SwitchingLossData] = []
        self.metadata: Dict[str, Any] = {}
    
    def get_channel_data(self, t_j: float, v_g: Optional[float] = None) -> List[ChannelCharacteristics]:
        """Get channel data for specific temperature and gate voltage."""
        return [ch for ch in self.channel_data 
                if ch.t_j == t_j and (v_g is None or ch.v_g == v_g)]
    
    def linearize_at_operating_point(self, t_j: float, v_g: float, i_channel: float) -> Dict[str, float]:
        """Linearize switch at operating point."""
        channel_data = self.get_channel_data(t_j, v_g)
        if not channel_data:
            raise ValueError(f"No channel data found for t_j={t_j}, v_g={v_g}")
        
        # Implementation for linearization
        ch = channel_data[0]
        # Calculate v_channel and r_channel from graph_v_i and i_channel
        return {"v_channel": 0.0, "r_channel": 0.0}  # Placeholder


class Diode(ITransistorComponent):
    """Diode component with reverse characteristics."""
    
    def __init__(self):
        self.channel_data: List[ChannelCharacteristics] = []
        self.e_rr_data: List[SwitchingLossData] = []
        self.metadata: Dict[str, Any] = {}
    
    def get_channel_data(self, t_j: float, v_g: Optional[float] = None) -> List[ChannelCharacteristics]:
        """Get channel data for specific temperature."""
        return [ch for ch in self.channel_data if ch.t_j == t_j]
    
    def linearize_at_operating_point(self, t_j: float, v_g: float, i_channel: float) -> Dict[str, float]:
        """Linearize diode at operating point."""
        channel_data = self.get_channel_data(t_j)
        if not channel_data:
            raise ValueError(f"No channel data found for t_j={t_j}")
        
        # Implementation for linearization
        return {"v_channel": 0.0, "r_channel": 0.0}  # Placeholder


class Transistor:
    """Main transistor aggregate containing all components and metadata."""
    
    def __init__(self, metadata: TransistorMetadata, electrical: ElectricalRatings, 
                 thermal: ThermalProperties):
        self.metadata = metadata
        self.electrical_ratings = electrical
        self.thermal_properties = thermal
        self.switch = Switch()
        self.diode = Diode()
        self._working_point: Optional[Dict[str, Any]] = None
    
    @property
    def working_point(self) -> Optional[Dict[str, Any]]:
        """Current working point data."""
        return self._working_point
    
    def update_working_point(self, t_j: float, v_g: float, i_channel: float, 
                           component: str = "both") -> None:
        """Update working point for calculations."""
        wp_data = {}
        
        if component in ["switch", "both"]:
            switch_wp = self.switch.linearize_at_operating_point(t_j, v_g, i_channel)
            wp_data["switch"] = switch_wp
        
        if component in ["diode", "both"]:
            diode_wp = self.diode.linearize_at_operating_point(t_j, v_g, i_channel)
            wp_data["diode"] = diode_wp
        
        self._working_point = wp_data
    
    def get_component(self, component_type: str) -> ITransistorComponent:
        """Get specific component."""
        if component_type.lower() == "switch":
            return self.switch
        elif component_type.lower() == "diode":
            return self.diode
        else:
            raise ValueError(f"Unknown component type: {component_type}")
