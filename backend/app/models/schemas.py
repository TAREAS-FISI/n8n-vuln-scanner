"""
Pydantic schemas para request/response de la API.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


# ─── Requests ─────────────────────────────────────────────────
class ScanRequest(BaseModel):
    url: str = Field(..., description="URL del sitio web a escanear", examples=["http://dvwa:8081"])


class UrlInput(BaseModel):
    url: str = Field(..., description="URL del target")


class FindingInput(BaseModel):
    source: str
    category: str
    title: str
    severity: str = "Info"
    cvss_score: float = 0.0
    description: str | None = None
    remediation: str | None = None
    raw_data: dict[str, Any] | None = None


class FindingsBatch(BaseModel):
    findings: list[FindingInput]


class LLMAnalysisInput(BaseModel):
    raw_prompt: str | None = None
    raw_response: str | None = None
    recommendations_json: dict[str, Any] | list[Any] | None = None
    model_used: str | None = None
    duration_ms: int | None = None


class PhaseUpdate(BaseModel):
    phase: str
    status: str
    findings_count: int = 0
    error_message: str | None = None


class ScoreRequest(BaseModel):
    scan_id: str


# ─── Responses ────────────────────────────────────────────────
class ScanResponse(BaseModel):
    scan_id: str
    status: str


class FindingOut(BaseModel):
    id: str
    source: str
    category: str
    title: str
    severity: str
    cvss_score: float
    description: str | None = None
    remediation: str | None = None

    class Config:
        from_attributes = True


class PhaseOut(BaseModel):
    phase_name: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    findings_count: int = 0

    class Config:
        from_attributes = True


class LLMAnalysisOut(BaseModel):
    raw_response: str | None = None
    recommendations_json: Any | None = None
    model_used: str | None = None
    duration_ms: int | None = None

    class Config:
        from_attributes = True


class ScanReport(BaseModel):
    scan_id: str
    target_url: str
    status: str
    global_score: float | None = None
    total_findings: int = 0
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    findings: list[FindingOut] = []
    phases: list[PhaseOut] = []
    llm_analysis: LLMAnalysisOut | None = None

    class Config:
        from_attributes = True


class ScanSummary(BaseModel):
    scan_id: str
    target_url: str
    status: str
    global_score: float | None = None
    total_findings: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CheckResult(BaseModel):
    findings: list[FindingInput]
    duration_ms: int
    source: str


class ScoreResult(BaseModel):
    scan_id: str
    global_score: float
    breakdown: dict[str, Any] = {}
