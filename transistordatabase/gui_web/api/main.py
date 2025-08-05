"""
Main API entry point for Vercel serverless deployment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Transistor Database API",
    description="REST API for managing transistor data",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Transistor Database API is running"}


@app.get("/api")
async def root():
    """API root endpoint."""
    return {
        "message": "Transistor Database API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
