"""
n8n Vulnerability Scanner — FastAPI Backend
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import checks, health, runners, scans

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="n8n Vulnerability Scanner API",
    description="API para escaneo de vulnerabilidades web",
    version="1.0.0",
)

# CORS para Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health.router)
app.include_router(checks.router)
app.include_router(runners.router)
app.include_router(scans.router)
