#!/usr/bin/env python3
"""Simple test to verify TestClient works."""

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"Hello": "World"}
    
    client = TestClient(app)
    response = client.get("/")
    
    print("TestClient works!")
    print(f"Response: {response.status_code}")
    print(f"Data: {response.json()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
