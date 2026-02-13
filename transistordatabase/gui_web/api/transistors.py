"""Transistors API endpoints for Vercel serverless deployment."""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import json
import tempfile

# Sample transistor data for demo
SAMPLE_TRANSISTORS = {
    "CREE_C3M0016120K": {
        "metadata": {
            "name": "CREE_C3M0016120K",
            "manufacturer": "CREE",
            "type": "SiC MOSFET",
            "housing": "TO-247-3"
        },
        "electrical": {
            "v_abs_max": 1200,
            "i_abs_max": 90,
            "r_ds_on": 0.016,
            "q_g": 169,
            "v_gs": 20
        },
        "thermal": {
            "t_j_max": 175,
            "r_th_jc": 0.24,
            "r_th_ja": 25
        }
    },
    "Infineon_FF200R12KE3": {
        "metadata": {
            "name": "Infineon_FF200R12KE3",
            "manufacturer": "Infineon",
            "type": "IGBT",
            "housing": "62mm"
        },
        "electrical": {
            "v_abs_max": 1200,
            "i_abs_max": 200,
            "v_ce_sat": 1.7,
            "q_g": 280,
            "v_gs": 15
        },
        "thermal": {
            "t_j_max": 150,
            "r_th_jc": 0.19,
            "r_th_ja": 40
        }
    }
}

app = FastAPI()

@app.get("/")
async def get_transistors():
    """Get all transistors."""
    return {"transistors": list(SAMPLE_TRANSISTORS.values())}

@app.get("/{transistor_id}")
async def get_transistor(transistor_id: str):
    """Get a specific transistor by ID."""
    if transistor_id not in SAMPLE_TRANSISTORS:
        raise HTTPException(status_code=404, detail="Transistor not found")
    return SAMPLE_TRANSISTORS[transistor_id]

@app.post("/search")
async def search_transistors(search_params: Dict[str, Any]):
    """Search transistors based on criteria."""
    results = []
    
    for _transistor_id, transistor in SAMPLE_TRANSISTORS.items():
        match = True
        
        # Simple filtering logic
        if "manufacturer" in search_params:
            if transistor["metadata"]["manufacturer"].lower() != search_params["manufacturer"].lower():
                match = False
        
        if "min_voltage" in search_params:
            if transistor["electrical"]["v_abs_max"] < search_params["min_voltage"]:
                match = False
                
        if "max_current" in search_params:
            if transistor["electrical"]["i_abs_max"] > search_params["max_current"]:
                match = False
        
        if match:
            results.append(transistor)
    
    return {"results": results, "count": len(results)}

@app.post("/upload")
async def upload_transistor(file: UploadFile = File(...)):
    """Upload a new transistor file."""
    try:
        content = await file.read()
        data = json.loads(content)
        
        # Basic validation
        if "metadata" not in data or "name" not in data["metadata"]:
            raise HTTPException(status_code=400, detail="Invalid transistor data format")
        
        # In a real deployment, you'd save this to a database
        transistor_id = data["metadata"]["name"]
        SAMPLE_TRANSISTORS[transistor_id] = data
        
        return {"message": f"Transistor {transistor_id} uploaded successfully"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/export/{format}")
async def export_transistors(format: str, transistor_ids: Optional[str] = None):
    """Export transistors in specified format."""
    if format not in ["json", "matlab", "plecs", "spice"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Simple export logic
    transistors_to_export = SAMPLE_TRANSISTORS
    if transistor_ids:
        ids = transistor_ids.split(",")
        transistors_to_export = {k: v for k, v in SAMPLE_TRANSISTORS.items() if k in ids}
    
    if format == "json":
        return {"format": "json", "data": transistors_to_export}
    else:
        return {"format": format, "message": f"Export to {format} format", "data": transistors_to_export}
