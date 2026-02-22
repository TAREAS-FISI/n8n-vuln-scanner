"""
Router: Security checks — Endpoints para los 7 módulos de análisis.
"""
from fastapi import APIRouter

from app.models.schemas import CheckResult, UrlInput
from app.services.header_checker import check_headers
from app.services.ssl_checker import check_ssl
from app.services.port_scanner import check_ports
from app.services.cookie_checker import check_cookies
from app.services.cors_checker import check_cors
from app.services.info_disclosure import check_info_disclosure
from app.services.tech_detector import detect_technologies

router = APIRouter(prefix="/check", tags=["Security Checks"])


@router.post("/headers", response_model=CheckResult)
async def run_header_check(body: UrlInput):
    """Analiza 12 headers de seguridad HTTP."""
    return await check_headers(body.url)


@router.post("/ssl", response_model=CheckResult)
async def run_ssl_check(body: UrlInput):
    """Verifica certificado SSL/TLS, protocolo y cipher."""
    return await check_ssl(body.url)


@router.post("/ports", response_model=CheckResult)
async def run_port_check(body: UrlInput):
    """Escanea los top 20 puertos peligrosos."""
    return await check_ports(body.url)


@router.post("/cookies", response_model=CheckResult)
async def run_cookie_check(body: UrlInput):
    """Verifica flags de seguridad en cookies."""
    return await check_cookies(body.url)


@router.post("/cors", response_model=CheckResult)
async def run_cors_check(body: UrlInput):
    """Verifica configuración CORS."""
    return await check_cors(body.url)


@router.post("/disclosure", response_model=CheckResult)
async def run_disclosure_check(body: UrlInput):
    """Busca archivos y rutas sensibles expuestas."""
    return await check_info_disclosure(body.url)


@router.post("/tech", response_model=CheckResult)
async def run_tech_check(body: UrlInput):
    """Detecta tecnologías web del target."""
    return await detect_technologies(body.url)
