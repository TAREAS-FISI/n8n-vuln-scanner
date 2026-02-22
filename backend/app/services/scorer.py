"""
Scorer — Calcula el score global de seguridad (0-100) a partir de los findings.
"""
from __future__ import annotations

from app.models.schemas import FindingInput

# Factores de penalización por severidad
SEVERITY_FACTORS = {
    "Critical": 25,
    "High": 15,
    "Medium": 8,
    "Low": 3,
    "Info": 0,
}

# Pesos por fuente de detección
SOURCE_WEIGHTS = {
    "passive_headers": 0.15,
    "passive_ssl": 0.10,
    "passive_ports": 0.10,
    "passive_cookies": 0.05,
    "passive_cors": 0.05,
    "passive_disclosure": 0.05,
    "passive_tech": 0.00,  # Informativo, no penaliza
    "testssl": 0.15,
    "nuclei": 0.15,
    "zap": 0.20,
}

# Peso por defecto para fuentes desconocidas
DEFAULT_WEIGHT = 0.10


def calculate_score(findings: list[FindingInput]) -> dict:
    """
    Calcula el score global de seguridad.

    Fórmula: score = 100 - Σ(factor_severidad × peso_fuente)
    Score mínimo = 0, máximo = 100.

    Retorna dict con global_score y breakdown por fuente.
    """
    if not findings:
        return {
            "global_score": 100.0,
            "breakdown": {},
            "warning": "No se encontraron hallazgos. Score perfecto o análisis incompleto.",
        }

    breakdown: dict[str, dict] = {}
    total_penalty = 0.0

    for finding in findings:
        source = finding.source
        severity = finding.severity
        factor = SEVERITY_FACTORS.get(severity, 0)
        weight = SOURCE_WEIGHTS.get(source, DEFAULT_WEIGHT)

        penalty = factor * weight

        if source not in breakdown:
            breakdown[source] = {
                "findings_count": 0,
                "penalty": 0.0,
                "by_severity": {},
            }

        breakdown[source]["findings_count"] += 1
        breakdown[source]["penalty"] += penalty

        if severity not in breakdown[source]["by_severity"]:
            breakdown[source]["by_severity"][severity] = 0
        breakdown[source]["by_severity"][severity] += 1

        total_penalty += penalty

    global_score = max(0.0, min(100.0, 100.0 - total_penalty))
    global_score = round(global_score, 1)

    # Contar totales por severidad
    severity_totals = {}
    for finding in findings:
        sev = finding.severity
        severity_totals[sev] = severity_totals.get(sev, 0) + 1

    result = {
        "global_score": global_score,
        "total_findings": len(findings),
        "severity_totals": severity_totals,
        "total_penalty": round(total_penalty, 2),
        "breakdown": breakdown,
    }

    # Warning si score es 100 pero hay hallazgos informativos
    if global_score == 100.0 and len(findings) > 0:
        result["warning"] = (
            "Score perfecto pero se encontraron hallazgos informativos. "
            "Los findings con severidad Info no penalizan el score."
        )

    return result
