"""
SQLAlchemy async engine, session y modelos ORM.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_size=5)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


# ─── Tabla: scans ────────────────────────────────────────────
class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    target_url = Column(String(2048), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    global_score = Column(Numeric(5, 1), nullable=True)
    total_findings = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    phases = relationship("ScanPhase", back_populates="scan", cascade="all, delete-orphan")
    llm_analyses = relationship("LLMAnalysis", back_populates="scan", cascade="all, delete-orphan")


# ─── Tabla: scan_phases ──────────────────────────────────────
class ScanPhase(Base):
    __tablename__ = "scan_phases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    phase_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    findings_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    scan = relationship("Scan", back_populates="phases")


# ─── Tabla: findings ─────────────────────────────────────────
class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False, default="Info")
    cvss_score = Column(Numeric(3, 1), default=0.0)
    description = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    raw_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    scan = relationship("Scan", back_populates="findings")


# ─── Tabla: llm_analyses ─────────────────────────────────────
class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("uuid_generate_v4()"))
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    raw_prompt = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    recommendations_json = Column(JSONB, nullable=True)
    model_used = Column(String(100), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    scan = relationship("Scan", back_populates="llm_analyses")


# ─── Dependency para routers ─────────────────────────────────
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
