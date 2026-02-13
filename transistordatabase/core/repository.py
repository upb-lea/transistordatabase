"""Repository implementations and factory patterns for transistor data management."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    Transistor, TransistorMetadata, ElectricalRatings, ThermalProperties,
    Switch, Diode, ChannelCharacteristics, SwitchingLossData
)
from .services import TransistorRepository, ITransistorLoader


class JsonTransistorRepository(TransistorRepository):
    """File-based repository using JSON storage."""
    
    def __init__(self, data_directory: Path):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)
    
    def get_by_name(self, name: str) -> Optional[Transistor]:
        """Get transistor by name from JSON file."""
        file_path = self.data_directory / f"{name}.json"
        if not file_path.exists():
            return None
        
        loader = JsonTransistorLoader()
        return loader.load_from_json(file_path)
    
    def save(self, transistor: Transistor) -> None:
        """Save transistor to JSON file."""
        file_path = self.data_directory / f"{transistor.metadata.name}.json"
        loader = JsonTransistorLoader()
        loader.save_to_json(transistor, file_path)
    
    def list_all(self) -> List[str]:
        """List all available transistor names."""
        json_files = self.data_directory.glob("*.json")
        return [f.stem for f in json_files]
    
    def delete(self, name: str) -> bool:
        """Delete transistor from repository."""
        file_path = self.data_directory / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


class JsonTransistorLoader(ITransistorLoader):
    """JSON-based transistor loader."""
    
    def load_from_json(self, file_path: Path) -> Transistor:
        """Load transistor from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse metadata
        metadata = self._parse_metadata(data)
        
        # Parse electrical ratings
        electrical = self._parse_electrical_ratings(data)
        
        # Parse thermal properties
        thermal = self._parse_thermal_properties(data)
        
        # Create transistor
        transistor = Transistor(metadata, electrical, thermal)
        
        # Load switch data
        if 'switch' in data:
            transistor.switch = self._parse_switch_data(data['switch'])
        
        # Load diode data
        if 'diode' in data:
            transistor.diode = self._parse_diode_data(data['diode'])
        
        return transistor
    
    def save_to_json(self, transistor: Transistor, file_path: Path) -> None:
        """Save transistor to JSON file."""
        data = {
            'name': transistor.metadata.name,
            'type': transistor.metadata.type,
            'author': transistor.metadata.author,
            'manufacturer': transistor.metadata.manufacturer,
            'housing_type': transistor.metadata.housing_type,
            'v_abs_max': transistor.electrical_ratings.v_abs_max,
            'i_abs_max': transistor.electrical_ratings.i_abs_max,
            'i_cont': transistor.electrical_ratings.i_cont,
            't_j_max': transistor.electrical_ratings.t_j_max,
        }
        
        # Add optional metadata
        if transistor.metadata.comment:
            data['comment'] = transistor.metadata.comment
        if transistor.metadata.datasheet_hyperlink:
            data['datasheet_hyperlink'] = transistor.metadata.datasheet_hyperlink
        
        # Add thermal properties
        thermal_data = {
            'housing_area': transistor.thermal_properties.housing_area,
            'cooling_area': transistor.thermal_properties.cooling_area,
        }
        if transistor.thermal_properties.r_th_cs:
            thermal_data['r_th_cs'] = transistor.thermal_properties.r_th_cs
        data.update(thermal_data)
        
        # Add switch data
        if transistor.switch.channel_data:
            data['switch'] = self._serialize_switch_data(transistor.switch)
        
        # Add diode data
        if transistor.diode.channel_data:
            data['diode'] = self._serialize_diode_data(transistor.diode)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=self._json_serializer)
    
    def _parse_metadata(self, data: Dict[str, Any]) -> TransistorMetadata:
        """Parse metadata from JSON data."""
        return TransistorMetadata(
            name=data['name'],
            type=data['type'],
            author=data.get('author', ''),
            manufacturer=data.get('manufacturer', ''),
            housing_type=data.get('housing_type', ''),
            comment=data.get('comment'),
            datasheet_hyperlink=data.get('datasheet_hyperlink'),
            datasheet_date=self._parse_date(data.get('datasheet_date')),
            datasheet_version=data.get('datasheet_version')
        )
    
    def _parse_electrical_ratings(self, data: Dict[str, Any]) -> ElectricalRatings:
        """Parse electrical ratings from JSON data."""
        return ElectricalRatings(
            v_abs_max=data.get('v_abs_max', 0.0),
            i_abs_max=data.get('i_abs_max', 0.0),
            i_cont=data.get('i_cont', 0.0),
            t_j_max=data.get('t_j_max', 150.0)
        )
    
    def _parse_thermal_properties(self, data: Dict[str, Any]) -> ThermalProperties:
        """Parse thermal properties from JSON data."""
        return ThermalProperties(
            housing_area=data.get('housing_area', 0.0),
            cooling_area=data.get('cooling_area', 0.0),
            r_th_cs=data.get('r_th_cs'),
            r_th_switch_cs=data.get('r_th_switch_cs'),
            r_th_diode_cs=data.get('r_th_diode_cs'),
            t_c_max=data.get('t_c_max')
        )
    
    def _parse_switch_data(self, switch_data: Dict[str, Any]) -> Switch:
        """Parse switch data from JSON."""
        switch = Switch()
        
        # Parse channel data
        if 'channel' in switch_data:
            for channel_item in switch_data['channel']:
                channel = ChannelCharacteristics(
                    t_j=channel_item['t_j'],
                    graph_v_i=self._parse_array_data(channel_item['graph_v_i']),
                    v_g=channel_item.get('v_g')
                )
                switch.channel_data.append(channel)
        
        # Parse switching loss data
        if 'e_on' in switch_data:
            for loss_item in switch_data['e_on']:
                loss_data = self._parse_switching_loss_data(loss_item)
                switch.e_on_data.append(loss_data)
        
        if 'e_off' in switch_data:
            for loss_item in switch_data['e_off']:
                loss_data = self._parse_switching_loss_data(loss_item)
                switch.e_off_data.append(loss_data)
        
        return switch
    
    def _parse_diode_data(self, diode_data: Dict[str, Any]) -> Diode:
        """Parse diode data from JSON."""
        diode = Diode()
        
        # Parse channel data
        if 'channel' in diode_data:
            for channel_item in diode_data['channel']:
                channel = ChannelCharacteristics(
                    t_j=channel_item['t_j'],
                    graph_v_i=self._parse_array_data(channel_item['graph_v_i']),
                    v_g=channel_item.get('v_g')
                )
                diode.channel_data.append(channel)
        
        # Parse reverse recovery data
        if 'e_rr' in diode_data:
            for loss_item in diode_data['e_rr']:
                loss_data = self._parse_switching_loss_data(loss_item)
                diode.e_rr_data.append(loss_data)
        
        return diode
    
    def _parse_switching_loss_data(self, loss_data: Dict[str, Any]) -> SwitchingLossData:
        """Parse switching loss data from JSON."""
        return SwitchingLossData(
            dataset_type=loss_data['dataset_type'],
            t_j=loss_data['t_j'],
            v_supply=loss_data['v_supply'],
            v_g=loss_data.get('v_g', 0.0),
            e_x=loss_data.get('e_x'),
            r_g=loss_data.get('r_g'),
            i_x=loss_data.get('i_x'),
            graph_i_e=self._parse_array_data(loss_data.get('graph_i_e')),
            graph_r_e=self._parse_array_data(loss_data.get('graph_r_e'))
        )
    
    def _parse_array_data(self, data: Any) -> Optional[Any]:
        """Parse array data from JSON."""
        if data is None:
            return None
        return data  # Simplified - would need proper numpy array conversion
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None
    
    def _serialize_switch_data(self, switch: Switch) -> Dict[str, Any]:
        """Serialize switch data to JSON-compatible format."""
        data = {}
        
        if switch.channel_data:
            data['channel'] = [
                {
                    't_j': ch.t_j,
                    'v_g': ch.v_g,
                    'graph_v_i': ch.graph_v_i.tolist() if hasattr(ch.graph_v_i, 'tolist') else ch.graph_v_i
                }
                for ch in switch.channel_data
            ]
        
        return data
    
    def _serialize_diode_data(self, diode: Diode) -> Dict[str, Any]:
        """Serialize diode data to JSON-compatible format."""
        data = {}
        
        if diode.channel_data:
            data['channel'] = [
                {
                    't_j': ch.t_j,
                    'graph_v_i': ch.graph_v_i.tolist() if hasattr(ch.graph_v_i, 'tolist') else ch.graph_v_i
                }
                for ch in diode.channel_data
            ]
        
        return data
    
    def _json_serializer(self, obj: Any) -> Any:
        """Serialize special types to JSON-compatible format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class TransistorFactory:
    """Factory for creating transistor instances."""
    
    @staticmethod
    def create_empty_transistor(name: str, transistor_type: str = "IGBT") -> Transistor:
        """Create empty transistor with default values."""
        metadata = TransistorMetadata(
            name=name,
            type=transistor_type,
            author="",
            manufacturer="",
            housing_type=""
        )
        
        electrical = ElectricalRatings(
            v_abs_max=0.0,
            i_abs_max=0.0,
            i_cont=0.0,
            t_j_max=150.0
        )
        
        thermal = ThermalProperties(
            housing_area=0.0,
            cooling_area=0.0
        )
        
        return Transistor(metadata, electrical, thermal)
    
    @staticmethod
    def create_from_template(template_name: str, new_name: str) -> Transistor:
        """Create transistor from existing template."""
        # Implementation would load template and create new instance
        return TransistorFactory.create_empty_transistor(new_name)
