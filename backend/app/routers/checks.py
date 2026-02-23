"""
Router: Security checks — Endpoints para los 7 módulos de análisis.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import CheckResult, UrlInput
from app.services.header_checker import check_headers
from app.services.ssl_checker import check_ssl
from app.services.port_scanner import check_ports
from app.services.cookie_checker import check_cookies
from app.services.cors_checker import check_cors
from app.services.info_disclosure import check_info_disclosure
from app.services.tech_detector import detect_technologies

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/check", tags=["Security Checks"])


@router.post("/headers", response_model=CheckResult)
async def run_header_check(body: UrlInput):
    """Analiza 12 headers de seguridad HTTP."""
    try:
        return await check_headers(body.url)
    except Exception as e:
        logger.error("Router /check/headers — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en check de headers: {type(e).__name__}")


@router.post("/ssl", response_model=CheckResult)
async def run_ssl_check(body: UrlInput):
    """Verifica certificado SSL/TLS, protocolo y cipher."""
    try:
        return await check_ssl(body.url)
    except Exception as e:
        logger.error("Router /check/ssl — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en check SSL: {type(e).__name__}")


@router.post("/ports", response_model=CheckResult)
async def run_port_check(body: UrlInput):
    """Escanea los top 20 puertos peligrosos."""
    try:
        return await check_ports(body.url)
    except Exception as e:
        logger.error("Router /check/ports — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en port scan: {type(e).__name__}")


@router.post("/cookies", response_model=CheckResult)
async def run_cookie_check(body: UrlInput):
    """Verifica flags de seguridad en cookies."""
    try:
        return await check_cookies(body.url)
    except Exception as e:
        logger.error("Router /check/cookies — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en check de cookies: {type(e).__name__}")


@router.post("/cors", response_model=CheckResult)
async def run_cors_check(body: UrlInput):
    """Verifica configuración CORS."""
    try:
        return await check_cors(body.url)
    except Exception as e:
        logger.error("Router /check/cors — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en check CORS: {type(e).__name__}")


@router.post("/disclosure", response_model=CheckResult)
async def run_disclosure_check(body: UrlInput):
    """Busca archivos y rutas sensibles expuestas."""
    try:
        return await check_info_disclosure(body.url)
    except Exception as e:
        logger.error("Router /check/disclosure — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en check de disclosure: {type(e).__name__}")


@router.post("/tech", response_model=CheckResult)
async def run_tech_check(body: UrlInput):
    """Detecta tecnologías web del target."""
    try:
        return await detect_technologies(body.url)
    except Exception as e:
        logger.error("Router /check/tech — error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en tech detection: {type(e).__name__}")
