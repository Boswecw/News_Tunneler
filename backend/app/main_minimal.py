"""Minimal FastAPI application for testing Render deployment."""
from fastapi import FastAPI

app = FastAPI(title="News Tunneler - Minimal Test")

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal app is running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}
