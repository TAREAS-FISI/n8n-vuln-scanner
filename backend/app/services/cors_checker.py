"""
CORS Checker — Verifica configuración de CORS (wildcard, reflected origin, credentials).
"""
import time
from urllib.parse import urlparse

import httpx

from app.models.schemas import CheckResult, FindingInput

EVIL_ORIGINS = [
    "https://evil.com",
    "https://attacker.example.com",
    "null",
]


async def check_cors(url: str) -> CheckResult:
    """
    Verifica la configuración CORS del target enviando requests con origins maliciosos.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    try:
        parsed = urlparse(url)
        target_origin = f"{parsed.scheme}://{parsed.netloc}"

        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:

            # 1. Request sin Origin — verificar si ACAO está presente
            response_base = await client.get(url)
            acao = response_base.headers.get("access-control-allow-origin", "")

            if acao == "*":
                # Wildcard CORS
                acac = response_base.headers.get("access-control-allow-credentials", "").lower()
                if acac == "true":
                    # Wildcard + Credentials = CRITICAL
                    findings.append(
                        FindingInput(
                            source="passive_cors",
                            category="CORS Misconfiguration",
                            title="CORS wildcard (*) con Allow-Credentials",
                            severity="Critical",
                            cvss_score=9.1,
                            description=(
                                "El servidor expone Access-Control-Allow-Origin: * junto con "
                                "Access-Control-Allow-Credentials: true. Esto permite que CUALQUIER "
                                "sitio web acceda a la API autenticada del usuario."
                            ),
                            remediation=(
                                "NUNCA combinar ACAO: * con ACAC: true. "
                                "Usar una lista blanca de origins permitidos y validarlos en el backend."
                            ),
                        )
                    )
                else:
                    findings.append(
                        FindingInput(
                            source="passive_cors",
                            category="CORS Misconfiguration",
                            title="CORS permite cualquier origin (*)",
                            severity="Medium",
                            cvss_score=5.4,
                            description=(
                                "El servidor expone Access-Control-Allow-Origin: *. "
                                "Cualquier sitio web puede leer las respuestas de la API."
                            ),
                            remediation=(
                                "Restringir ACAO a los dominios de confianza específicos en lugar de wildcard.\n"
                                "Ejemplo: Access-Control-Allow-Origin: https://tu-dominio.com"
                            ),
                        )
                    )

            # 2. Probar reflected origins maliciosos
            for evil_origin in EVIL_ORIGINS:
                try:
                    response = await client.get(
                        url, headers={"Origin": evil_origin}
                    )
                    acao_reflected = response.headers.get("access-control-allow-origin", "")
                    acac_reflected = response.headers.get(
                        "access-control-allow-credentials", ""
                    ).lower()

                    if acao_reflected == evil_origin:
                        severity = "Critical" if acac_reflected == "true" else "High"
                        cvss = 9.1 if acac_reflected == "true" else 7.5

                        findings.append(
                            FindingInput(
                                source="passive_cors",
                                category="CORS Origin Reflection",
                                title=f"CORS refleja origin malicioso: {evil_origin}",
                                severity=severity,
                                cvss_score=cvss,
                                description=(
                                    f"El servidor refleja el Origin '{evil_origin}' en ACAO. "
                                    "Un atacante puede enviar requests desde cualquier dominio "
                                    "y leer las respuestas."
                                    + (" Con credentials habilitadas, puede robar sesiones."
                                       if acac_reflected == "true" else "")
                                ),
                                remediation=(
                                    "No reflejar el header Origin directamente. "
                                    "Validar contra una lista blanca de origins permitidos."
                                ),
                            )
                        )
                        break  # Un origin reflejado es suficiente
                except Exception:
                    continue

    except httpx.ConnectError:
        findings.append(
            FindingInput(
                source="passive_cors",
                category="Connection Error",
                title="No se pudo conectar al target",
                severity="Info",
                cvss_score=0.0,
                description=f"No se pudo establecer conexión con {url}",
            )
        )
    except Exception as e:
        findings.append(
            FindingInput(
                source="passive_cors",
                category="Scan Error",
                title=f"Error al verificar CORS: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_cors")
