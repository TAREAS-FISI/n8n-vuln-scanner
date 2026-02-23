"""
Router: Health check — verifica API y conectividad con PostgreSQL.
"""
import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.models.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    """Devuelve estado del servicio y conectividad con la base de datos."""
    db_ok = False
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Health check — DB unreachable: %s", e)

    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "service": "vuln-scanner-api",
        "database": "connected" if db_ok else "unreachable",
    }
