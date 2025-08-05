"""
Topology calculator API endpoints for Vercel serverless deployment.
"""

from fastapi import FastAPI
from typing import Dict, Any
import math

app = FastAPI()


@app.post("/calculate")
async def calculate_topology(params: Dict[str, Any]):
    """Calculate power converter topology parameters."""
    
    topology = params.get("topology", "buck")
    vin = params.get("vin", 12)
    vout = params.get("vout", 5)
    iout = params.get("iout", 10)
    fsw = params.get("fsw", 100000)  # 100kHz
    
    if topology == "buck":
        return calculate_buck_converter(vin, vout, iout, fsw)
    elif topology == "boost":
        return calculate_boost_converter(vin, vout, iout, fsw)
    elif topology == "buck-boost":
        return calculate_buck_boost_converter(vin, vout, iout, fsw)
    else:
        return {"error": "Unsupported topology"}


def calculate_buck_converter(vin: float, vout: float, iout: float, fsw: float) -> Dict[str, Any]:
    """Calculate Buck converter parameters."""
    
    # Duty cycle
    duty = vout / vin
    
    # Inductor calculation (assuming 20% ripple)
    ripple_factor = 0.2
    L = (vin - vout) * duty / (ripple_factor * iout * fsw)
    
    # Capacitor calculation (assuming 1% voltage ripple)
    voltage_ripple = 0.01 * vout
    C = ripple_factor * iout / (8 * fsw * voltage_ripple)
    
    # Power calculations
    pin = vout * iout / 0.95  # Assuming 95% efficiency
    
    return {
        "topology": "buck",
        "parameters": {
            "duty_cycle": round(duty, 3),
            "inductor_uH": round(L * 1e6, 2),
            "capacitor_uF": round(C * 1e6, 2),
            "input_power_W": round(pin, 2),
            "output_power_W": round(vout * iout, 2),
            "efficiency": 0.95
        },
        "operating_point": {
            "vin": vin,
            "vout": vout,
            "iout": iout,
            "fsw": fsw
        }
    }


def calculate_boost_converter(vin: float, vout: float, iout: float, fsw: float) -> Dict[str, Any]:
    """Calculate Boost converter parameters."""
    
    # Duty cycle
    duty = 1 - (vin / vout)
    
    # Input current
    iin = iout * vout / vin / 0.95  # Assuming 95% efficiency
    
    # Inductor calculation (assuming 20% ripple)
    ripple_factor = 0.2
    L = vin * duty / (ripple_factor * iin * fsw)
    
    # Capacitor calculation
    C = iout * duty / (0.01 * vout * fsw)  # 1% voltage ripple
    
    return {
        "topology": "boost",
        "parameters": {
            "duty_cycle": round(duty, 3),
            "inductor_uH": round(L * 1e6, 2),
            "capacitor_uF": round(C * 1e6, 2),
            "input_current_A": round(iin, 2),
            "efficiency": 0.95
        },
        "operating_point": {
            "vin": vin,
            "vout": vout,
            "iout": iout,
            "fsw": fsw
        }
    }


def calculate_buck_boost_converter(vin: float, vout: float, iout: float, fsw: float) -> Dict[str, Any]:
    """Calculate Buck-Boost converter parameters."""
    
    # Duty cycle
    duty = vout / (vin + vout)
    
    # Input current (discontinuous with buck-boost)
    iin = iout * vout / vin / 0.93  # Assuming 93% efficiency
    
    # Inductor calculation
    ripple_factor = 0.3
    L = vin * duty / (ripple_factor * iin * fsw)
    
    # Capacitor calculation
    C = iout * duty / (0.02 * abs(vout) * fsw)  # 2% voltage ripple
    
    return {
        "topology": "buck-boost",
        "parameters": {
            "duty_cycle": round(duty, 3),
            "inductor_uH": round(L * 1e6, 2),
            "capacitor_uF": round(C * 1e6, 2),
            "input_current_A": round(iin, 2),
            "efficiency": 0.93
        },
        "operating_point": {
            "vin": vin,
            "vout": abs(vout),  # Buck-boost inverts
            "iout": iout,
            "fsw": fsw
        }
    }
