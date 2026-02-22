"""
Router: Scans — CRUD de escaneos + endpoints para n8n.
"""
import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.database import Finding, LLMAnalysis, Scan, ScanPhase, get_db
from app.models.schemas import (
    FindingInput,
    FindingsBatch,
    LLMAnalysisInput,
    PhaseUpdate,
    ScanReport,
    ScanRequest,
    ScanResponse,
    ScanSummary,
    ScoreRequest,
    ScoreResult,
    FindingOut,
    PhaseOut,
    LLMAnalysisOut,
)
from app.services.scorer import calculate_score

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Scans"])

# Fases del pipeline
PIPELINE_PHASES = [
    "passive_checks",
    "testssl",
    "nuclei",
    "zap",
    "scoring_llm",
]


# ─── POST /scan ──────────────────────────────────────────────
@router.post("/scan", response_model=ScanResponse)
async def create_scan(body: ScanRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo escaneo, registra las fases en BD y dispara webhook a n8n.
    """
    scan = Scan(
        id=uuid.uuid4(),
        target_url=body.url,
        status="pending",
    )
    db.add(scan)

    # Crear las fases del pipeline
    for phase_name in PIPELINE_PHASES:
        phase = ScanPhase(
            scan_id=scan.id,
            phase_name=phase_name,
            status="pending",
        )
        db.add(phase)

    await db.commit()
    await db.refresh(scan)

    # Disparar webhook a n8n (async, no bloquea)
    scan_id_str = str(scan.id)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                settings.n8n_webhook_url,
                json={"url": body.url, "scan_id": scan_id_str},
            )
        logger.info(f"Webhook disparado para scan {scan_id_str}")
    except Exception as e:
        logger.warning(f"No se pudo disparar webhook n8n: {e}. El scan queda pendiente.")
        # No falla el request — n8n puede estar caído durante desarrollo

    return ScanResponse(scan_id=scan_id_str, status=scan.status)


# ─── GET /scan/{id} ──────────────────────────────────────────
@router.get("/scan/{scan_id}", response_model=ScanReport)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retorna estado actual del escaneo + fases + findings + análisis LLM.
    """
    try:
        uid = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de scan inválido")

    result = await db.execute(
        select(Scan)
        .options(
            selectinload(Scan.findings),
            selectinload(Scan.phases),
            selectinload(Scan.llm_analyses),
        )
        .where(Scan.id == uid)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan no encontrado")

    # Construir respuesta
    llm = None
    if scan.llm_analyses:
        la = scan.llm_analyses[0]
        llm = LLMAnalysisOut(
            raw_response=la.raw_response,
            recommendations_json=la.recommendations_json,
            model_used=la.model_used,
            duration_ms=la.duration_ms,
        )

    return ScanReport(
        scan_id=str(scan.id),
        target_url=scan.target_url,
        status=scan.status,
        global_score=float(scan.global_score) if scan.global_score is not None else None,
        total_findings=scan.total_findings or 0,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        findings=[
            FindingOut(
                id=str(f.id),
                source=f.source,
                category=f.category,
                title=f.title,
                severity=f.severity,
                cvss_score=float(f.cvss_score) if f.cvss_score else 0.0,
                description=f.description,
                remediation=f.remediation,
            )
            for f in sorted(scan.findings, key=lambda x: (
                {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}.get(x.severity, 5)
            ))
        ],
        phases=[
            PhaseOut(
                phase_name=p.phase_name,
                status=p.status,
                started_at=p.started_at,
                completed_at=p.completed_at,
                findings_count=p.findings_count or 0,
            )
            for p in scan.phases
        ],
        llm_analysis=llm,
    )


# ─── GET /scans ──────────────────────────────────────────────
@router.get("/scans", response_model=list[ScanSummary])
async def list_scans(db: AsyncSession = Depends(get_db)):
    """
    Lista los últimos 20 escaneos.
    """
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(20)
    )
    scans = result.scalars().all()

    return [
        ScanSummary(
            scan_id=str(s.id),
            target_url=s.target_url,
            status=s.status,
            global_score=float(s.global_score) if s.global_score is not None else None,
            total_findings=s.total_findings or 0,
            created_at=s.created_at,
        )
        for s in scans
    ]


# ─── PUT /scan/{id}/phase ────────────────────────────────────
@router.put("/scan/{scan_id}/phase")
async def update_phase(scan_id: str, body: PhaseUpdate, db: AsyncSession = Depends(get_db)):
    """
    n8n actualiza el estado de una fase del pipeline.
    """
    uid = uuid.UUID(scan_id)

    result = await db.execute(
        select(ScanPhase).where(
            ScanPhase.scan_id == uid,
            ScanPhase.phase_name == body.phase,
        )
    )
    phase = result.scalar_one_or_none()

    if not phase:
        raise HTTPException(status_code=404, detail=f"Fase '{body.phase}' no encontrada")

    now = datetime.now(timezone.utc)

    if body.status == "running":
        phase.status = "running"
        phase.started_at = now
        # Marcar el scan como running si está pending
        await db.execute(
            update(Scan).where(Scan.id == uid, Scan.status == "pending").values(status="running")
        )
    elif body.status in ("completed", "failed", "skipped"):
        phase.status = body.status
        phase.completed_at = now
        phase.findings_count = body.findings_count
        if body.error_message:
            phase.error_message = body.error_message

    await db.commit()
    return {"ok": True}


# ─── PUT /scan/{id}/findings ─────────────────────────────────
@router.put("/scan/{scan_id}/findings")
async def add_findings(scan_id: str, body: FindingsBatch, db: AsyncSession = Depends(get_db)):
    """
    n8n envía findings de una fase. Se agregan a la BD.
    """
    uid = uuid.UUID(scan_id)

    # Verificar que el scan existe
    result = await db.execute(select(Scan).where(Scan.id == uid))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan no encontrado")

    count = 0
    for f in body.findings:
        finding = Finding(
            scan_id=uid,
            source=f.source,
            category=f.category,
            title=f.title,
            severity=f.severity,
            cvss_score=f.cvss_score,
            description=f.description,
            remediation=f.remediation,
            raw_data=f.raw_data,
        )
        db.add(finding)
        count += 1

    # Actualizar total_findings
    scan.total_findings = (scan.total_findings or 0) + count
    await db.commit()

    logger.info(f"Scan {scan_id}: +{count} findings agregados (total: {scan.total_findings})")
    return {"ok": True, "added": count, "total": scan.total_findings}


# ─── POST /score ──────────────────────────────────────────────
@router.post("/score", response_model=ScoreResult)
async def compute_score(body: ScoreRequest, db: AsyncSession = Depends(get_db)):
    """
    Calcula el score global del scan leyendo todos los findings de la BD.
    """
    uid = uuid.UUID(body.scan_id)

    result = await db.execute(select(Finding).where(Finding.scan_id == uid))
    findings_db = result.scalars().all()

    # Convertir a FindingInput para el scorer
    findings_input = [
        FindingInput(
            source=f.source,
            category=f.category,
            title=f.title,
            severity=f.severity,
            cvss_score=float(f.cvss_score) if f.cvss_score else 0.0,
            description=f.description,
            remediation=f.remediation,
        )
        for f in findings_db
    ]

    score_data = calculate_score(findings_input)

    # Guardar en BD
    await db.execute(
        update(Scan).where(Scan.id == uid).values(global_score=score_data["global_score"])
    )
    await db.commit()

    return ScoreResult(
        scan_id=body.scan_id,
        global_score=score_data["global_score"],
        breakdown=score_data,
    )


# ─── PUT /scan/{id}/llm-analysis ─────────────────────────────
@router.put("/scan/{scan_id}/llm-analysis")
async def save_llm_analysis(
    scan_id: str, body: LLMAnalysisInput, db: AsyncSession = Depends(get_db)
):
    """
    n8n envía el análisis generado por Ollama.
    """
    uid = uuid.UUID(scan_id)

    analysis = LLMAnalysis(
        scan_id=uid,
        raw_prompt=body.raw_prompt,
        raw_response=body.raw_response,
        recommendations_json=body.recommendations_json,
        model_used=body.model_used,
        duration_ms=body.duration_ms,
    )
    db.add(analysis)
    await db.commit()

    return {"ok": True}


# ─── PUT /scan/{id}/complete ─────────────────────────────────
@router.put("/scan/{scan_id}/complete")
async def complete_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    """
    n8n marca el scan como completado.
    """
    uid = uuid.UUID(scan_id)
    now = datetime.now(timezone.utc)

    await db.execute(
        update(Scan)
        .where(Scan.id == uid)
        .values(status="completed", completed_at=now)
    )
    await db.commit()

    logger.info(f"Scan {scan_id} completado")
    return {"ok": True}
