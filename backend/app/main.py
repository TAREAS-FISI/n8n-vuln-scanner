"""
n8n Vulnerability Scanner — FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "vuln-scanner-api"}
