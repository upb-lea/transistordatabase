"""
FastAPI backend for Transistor Database Web Application.

This module provides REST API endpoints for transistor data management,
validation, export, and comparison operations.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import tempfile
import uvicorn
from transistordatabase.core.models import Transistor, TransistorMetadata, ElectricalRatings, ThermalProperties

app = FastAPI(
    title="Transistor Database API",
    description="REST API for managing transistor data",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],  # Vue dev server default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (replace with actual database in production)
transistors_db: Dict[str, Dict] = {}

# Placeholder services (replace with actual implementations)
class ValidationService:
    def validate_transistor(self, transistor):
        return {"valid": True, "errors": [], "warnings": []}

class ComparisonService:
    def compare_transistors(self, transistors):
        return {"comparison": "Feature not implemented yet"}

class ExportService:
    def export_to_json(self, transistor, path):
        with open(path, 'w') as f:
            json.dump(transistor_to_dict(transistor), f, indent=2)
    
    def export_to_csv(self, transistors, path):
        # Placeholder implementation
        with open(path, 'w') as f:
            f.write("CSV export not implemented yet\n")
    
    def export_to_spice(self, transistor, path):
        # Placeholder implementation
        with open(path, 'w') as f:
            f.write("SPICE export not implemented yet\n")

validation_service = ValidationService()
comparison_service = ComparisonService()
export_service = ExportService()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Transistor Database API", "version": "1.0.0"}

@app.get("/api/transistors")
async def get_transistors() -> List[Dict[str, Any]]:
    """Get all transistors."""
    return [transistor_to_dict(t) for t in transistors_db.values()]

@app.get("/api/transistors/{transistor_id}")
async def get_transistor(transistor_id: str) -> Dict[str, Any]:
    """Get a specific transistor by ID."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    return transistor_to_dict(transistors_db[transistor_id])

@app.post("/api/transistors")
async def create_transistor(transistor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new transistor."""
    try:
        transistor = dict_to_transistor(transistor_data)
        transistor_id = transistor.metadata.name.replace(" ", "_").replace("/", "_")
        transistors_db[transistor_id] = transistor
        return {"id": transistor_id, "message": "Transistor created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid transistor data: {str(e)}")

@app.put("/api/transistors/{transistor_id}")
async def update_transistor(transistor_id: str, transistor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing transistor."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    
    try:
        transistor = dict_to_transistor(transistor_data)
        transistors_db[transistor_id] = transistor
        return {"message": "Transistor updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid transistor data: {str(e)}")

@app.delete("/api/transistors/{transistor_id}")
async def delete_transistor(transistor_id: str) -> Dict[str, Any]:
    """Delete a transistor."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    
    del transistors_db[transistor_id]
    return {"message": "Transistor deleted successfully"}

@app.post("/api/transistors/{transistor_id}/validate")
async def validate_transistor(transistor_id: str) -> Dict[str, Any]:
    """Validate a transistor."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    
    transistor = transistors_db[transistor_id]
    result = validation_service.validate_transistor(transistor)
    return result

@app.post("/api/transistors/compare")
async def compare_transistors(transistor_ids: List[str]) -> Dict[str, Any]:
    """Compare multiple transistors."""
    transistors = []
    for tid in transistor_ids:
        if tid not in transistors_db:
            raise HTTPException(status_code=404, detail=f"Transistor {tid} not found")
        transistors.append(transistors_db[tid])
    
    if len(transistors) < 2:
        raise HTTPException(status_code=400, detail="At least 2 transistors required for comparison")
    
    result = comparison_service.compare_transistors(transistors)
    return result

@app.post("/api/transistors/{transistor_id}/export/{format}")
async def export_transistor(transistor_id: str, format: str) -> FileResponse:
    """Export a transistor in specified format."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    
    transistor = transistors_db[transistor_id]
    
    if format not in ["json", "csv", "spice"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    
    try:
        if format == "json":
            export_service.export_to_json(transistor, tmp_path)
            media_type = "application/json"
        elif format == "csv":
            export_service.export_to_csv([transistor], tmp_path)
            media_type = "text/csv"
        elif format == "spice":
            export_service.export_to_spice(transistor, tmp_path)
            media_type = "text/plain"
        
        filename = f"{transistor.metadata.name}.{format}"
        return FileResponse(
            path=tmp_path,
            media_type=media_type,
            filename=filename
        )
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/transistors/upload")
async def upload_transistor(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and import a transistor from JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")
    
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Log the received data structure for debugging
        print(f"Received data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        transistor = dict_to_transistor(data)
        transistor_id = transistor.metadata.name.replace(" ", "_").replace("/", "_")
        transistors_db[transistor_id] = transistor
        
        return {
            "id": transistor_id,
            "message": "Transistor uploaded successfully",
            "name": transistor.metadata.name,
            "manufacturer": transistor.metadata.manufacturer,
            "type": transistor.metadata.type
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data value: {str(e)}")
    except Exception as e:
        print(f"Upload error: {str(e)}")  # For debugging
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

def transistor_to_dict(transistor: Transistor) -> Dict[str, Any]:
    """Convert Transistor object to dictionary."""
    return {
        "metadata": {
            "name": transistor.metadata.name,
            "type": transistor.metadata.type,
            "manufacturer": transistor.metadata.manufacturer,
            "housing_type": transistor.metadata.housing_type,
            "author": transistor.metadata.author,
            "comment": transistor.metadata.comment
        },
        "electrical": {
            "v_abs_max": transistor.electrical_ratings.v_abs_max,
            "i_abs_max": transistor.electrical_ratings.i_abs_max,
            "i_cont": transistor.electrical_ratings.i_cont,
            "t_j_max": transistor.electrical_ratings.t_j_max
        },
        "thermal": {
            "r_th_cs": transistor.thermal_properties.r_th_cs,
            "housing_area": transistor.thermal_properties.housing_area,
            "cooling_area": transistor.thermal_properties.cooling_area
        }
    }

def dict_to_transistor(data: Dict[str, Any]) -> Transistor:
    """Convert dictionary to Transistor object."""
    # Handle both nested format (from web interface) and flat format (from TDB files)
    if "metadata" in data and "electrical" in data and "thermal" in data:
        # Nested format from web interface
        metadata = TransistorMetadata(
            name=data["metadata"]["name"],
            type=data["metadata"]["type"],
            manufacturer=data["metadata"]["manufacturer"],
            housing_type=data["metadata"]["housing_type"],
            author=data["metadata"].get("author", ""),
            comment=data["metadata"].get("comment", "")
        )
        
        electrical = ElectricalRatings(
            v_abs_max=data["electrical"]["v_abs_max"],
            i_abs_max=data["electrical"]["i_abs_max"],
            i_cont=data["electrical"]["i_cont"],
            t_j_max=data["electrical"]["t_j_max"]
        )
        
        thermal = ThermalProperties(
            r_th_cs=data["thermal"]["r_th_cs"],
            housing_area=data["thermal"]["housing_area"],
            cooling_area=data["thermal"]["cooling_area"]
        )
    else:
        # Flat format from TDB files
        metadata = TransistorMetadata(
            name=data.get("name", "Unknown"),
            type=data.get("type", "Unknown"),
            manufacturer=data.get("manufacturer", "Unknown"),
            housing_type=data.get("housing_type", "Unknown"),
            author=data.get("author", ""),
            comment=data.get("comment", "")
        )
        
        # Find maximum temperature from datasheet or use default
        t_j_max = data.get("t_j_max", data.get("t_c_max", 150))
        if t_j_max is None:
            t_j_max = 150  # Default value
        
        electrical = ElectricalRatings(
            v_abs_max=data.get("v_abs_max", 0),
            i_abs_max=data.get("i_abs_max", 0),
            i_cont=data.get("i_cont", 0),
            t_j_max=t_j_max
        )
        
        thermal = ThermalProperties(
            r_th_cs=data.get("r_th_cs", 0),
            housing_area=data.get("housing_area", 0),
            cooling_area=data.get("cooling_area", 0)
        )
    
    return Transistor(
        metadata=metadata,
        electrical=electrical,
        thermal=thermal
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
