"""
Simplified FastAPI backend for Transistor Database Web Application.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import tempfile
import uvicorn

app = FastAPI(
    title="Transistor Database API",
    description="REST API for managing transistor data",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
transistors_db: Dict[str, Dict[str, Any]] = {}

# Load some example data
def load_example_data():
    """Load example transistor data from the database directory."""
    database_dir = Path(__file__).parent.parent.parent.parent / "database"
    if database_dir.exists():
        for json_file in database_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    transistor_id = json_file.stem
                    transistors_db[transistor_id] = normalize_transistor_data(data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

def normalize_transistor_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize transistor data to consistent format."""
    # Handle both nested and flat formats
    if "metadata" in data:
        return data
    
    # Convert flat format to nested format
    return {
        "metadata": {
            "name": data.get("name", "Unknown"),
            "type": data.get("type", "Unknown"),
            "manufacturer": data.get("manufacturer", "Unknown"),
            "housing_type": data.get("housing_type", "Unknown"),
            "author": data.get("author", ""),
            "comment": data.get("comment", "")
        },
        "electrical": {
            "v_abs_max": data.get("v_abs_max", 0),
            "i_abs_max": data.get("i_abs_max", 0),
            "i_cont": data.get("i_cont", 0),
            "t_j_max": data.get("t_j_max", data.get("t_c_max", 150))
        },
        "thermal": {
            "r_th_cs": data.get("r_th_cs", 0),
            "housing_area": data.get("housing_area", 0),
            "cooling_area": data.get("cooling_area", 0)
        },
        "curves": data.get("curves", {})
    }


@app.on_event("startup")
async def startup_event():
    """Load example data on startup."""
    load_example_data()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Transistor Database API", "version": "1.0.0"}


@app.get("/api/transistors")
async def get_transistors() -> List[Dict[str, Any]]:
    """Get all transistors."""
    return list(transistors_db.values())


@app.get("/api/transistors/{transistor_id}")
async def get_transistor(transistor_id: str) -> Dict[str, Any]:
    """Get a specific transistor."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    return transistors_db[transistor_id]


@app.post("/api/transistors")
async def create_transistor(transistor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new transistor."""
    try:
        transistor = normalize_transistor_data(transistor_data)
        transistor_id = transistor["metadata"]["name"].replace(" ", "_").replace("/", "_")
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
        transistor = normalize_transistor_data(transistor_data)
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


@app.post("/api/transistors/upload")
async def upload_transistor(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and import a transistor from JSON file."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")
    
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Normalize the data
        transistor = normalize_transistor_data(data)
        transistor_id = transistor["metadata"]["name"].replace(" ", "_").replace("/", "_")
        transistors_db[transistor_id] = transistor
        
        return {
            "id": transistor_id,
            "message": "Transistor uploaded successfully",
            "name": transistor["metadata"]["name"],
            "manufacturer": transistor["metadata"]["manufacturer"],
            "type": transistor["metadata"]["type"]
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


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
    
    # Simple comparison result
    comparison = {
        "transistors": transistors,
        "comparison_matrix": {},
        "similarities": [],
        "recommendations": []
    }
    
    return comparison


@app.post("/api/transistors/{transistor_id}/export/{format}")
async def export_transistor(transistor_id: str, format: str) -> FileResponse:
    """Export a transistor in specified format."""
    if transistor_id not in transistors_db:
        raise HTTPException(status_code=404, detail="Transistor not found")
    
    transistor = transistors_db[transistor_id]
    
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as tmp_file:
        if format == "json":
            json.dump(transistor, tmp_file, indent=2)
            media_type = "application/json"
        elif format == "csv":
            # Simple CSV export
            tmp_file.write("Property,Value\n")
            tmp_file.write(f"Name,{transistor['metadata']['name']}\n")
            tmp_file.write(f"Type,{transistor['metadata']['type']}\n")
            tmp_file.write(f"Manufacturer,{transistor['metadata']['manufacturer']}\n")
            tmp_file.write(f"V_max,{transistor['electrical']['v_abs_max']}\n")
            tmp_file.write(f"I_max,{transistor['electrical']['i_abs_max']}\n")
            media_type = "text/csv"
        
        tmp_path = Path(tmp_file.name)
    
    filename = f"{transistor['metadata']['name']}.{format}"
    return FileResponse(
        path=tmp_path,
        media_type=media_type,
        filename=filename
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
