"""
Header Checker — Analiza 12 headers de seguridad HTTP.
"""
import time
from urllib.parse import urlparse

import httpx

from app.models.schemas import CheckResult, FindingInput

# Definición de headers esperados con severidad y CVSS
SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "severity": "High",
        "cvss": 7.4,
        "category": "Missing Security Header",
        "description": (
            "El header HSTS (Strict-Transport-Security) no está presente. "
            "Esto permite ataques de downgrade de HTTPS a HTTP y man-in-the-middle."
        ),
        "remediation": (
            "Agregar el header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload\n"
            "En Nginx: add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains; preload\" always;\n"
            "En Apache: Header always set Strict-Transport-Security \"max-age=31536000; includeSubDomains; preload\""
        ),
    },
    "Content-Security-Policy": {
        "severity": "Medium",
        "cvss": 5.3,
        "category": "Missing Security Header",
        "description": (
            "El header CSP (Content-Security-Policy) no está presente. "
            "Sin CSP, el sitio es más vulnerable a ataques XSS y de inyección de contenido."
        ),
        "remediation": (
            "Agregar un CSP restrictivo. Ejemplo mínimo:\n"
            "Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        ),
    },
    "X-Frame-Options": {
        "severity": "Medium",
        "cvss": 4.3,
        "category": "Missing Security Header",
        "description": (
            "El header X-Frame-Options no está presente. "
            "El sitio puede ser embebido en iframes maliciosos (clickjacking)."
        ),
        "remediation": "Agregar: X-Frame-Options: DENY (o SAMEORIGIN si necesitas iframes propios).",
    },
    "X-Content-Type-Options": {
        "severity": "Low",
        "cvss": 3.7,
        "category": "Missing Security Header",
        "description": (
            "El header X-Content-Type-Options no está presente. "
            "Los navegadores podrían interpretar archivos con MIME types incorrectos (MIME sniffing)."
        ),
        "remediation": "Agregar: X-Content-Type-Options: nosniff",
    },
    "Referrer-Policy": {
        "severity": "Low",
        "cvss": 3.1,
        "category": "Missing Security Header",
        "description": (
            "El header Referrer-Policy no está definido. "
            "La URL completa podría filtrarse a sitios terceros vía el header Referer."
        ),
        "remediation": "Agregar: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "Permissions-Policy": {
        "severity": "Low",
        "cvss": 2.6,
        "category": "Missing Security Header",
        "description": (
            "El header Permissions-Policy (anteriormente Feature-Policy) no está presente. "
            "APIs del navegador como cámara, micrófono y geolocalización no están restringidas."
        ),
        "remediation": (
            "Agregar: Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()"
        ),
    },
    "Cache-Control": {
        "severity": "Low",
        "cvss": 2.2,
        "category": "Missing Security Header",
        "description": (
            "El header Cache-Control no especifica directivas de seguridad. "
            "Información sensible podría almacenarse en caché del navegador o proxies."
        ),
        "remediation": (
            "Para páginas con datos sensibles: Cache-Control: no-store, no-cache, must-revalidate, private"
        ),
    },
    "Cross-Origin-Opener-Policy": {
        "severity": "Low",
        "cvss": 2.6,
        "category": "Missing Security Header",
        "description": (
            "El header Cross-Origin-Opener-Policy (COOP) no está presente. "
            "Ventanas abiertas desde el sitio podrían interactuar con el contexto original."
        ),
        "remediation": "Agregar: Cross-Origin-Opener-Policy: same-origin",
    },
    "Cross-Origin-Resource-Policy": {
        "severity": "Low",
        "cvss": 2.6,
        "category": "Missing Security Header",
        "description": (
            "El header Cross-Origin-Resource-Policy (CORP) no está presente. "
            "Recursos del sitio podrían ser cargados desde otros orígenes sin restricción."
        ),
        "remediation": "Agregar: Cross-Origin-Resource-Policy: same-origin",
    },
    "Cross-Origin-Embedder-Policy": {
        "severity": "Low",
        "cvss": 2.6,
        "category": "Missing Security Header",
        "description": (
            "El header Cross-Origin-Embedder-Policy (COEP) no está presente. "
            "Necesario junto con COOP para habilitar SharedArrayBuffer y aislamiento cross-origin."
        ),
        "remediation": "Agregar: Cross-Origin-Embedder-Policy: require-corp",
    },
    "X-Permitted-Cross-Domain-Policies": {
        "severity": "Info",
        "cvss": 1.0,
        "category": "Missing Security Header",
        "description": (
            "El header X-Permitted-Cross-Domain-Policies no está presente. "
            "Controla acceso de plugins Adobe Flash/Acrobat a datos cross-domain."
        ),
        "remediation": "Agregar: X-Permitted-Cross-Domain-Policies: none",
    },
}


async def check_headers(url: str) -> CheckResult:
    """
    Analiza los headers de seguridad HTTP de la URL dada.
    Retorna un CheckResult con los findings.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url)

        response_headers = {k.lower(): v for k, v in response.headers.items()}

        for header_name, info in SECURITY_HEADERS.items():
            header_lower = header_name.lower()

            # Para HSTS, solo aplica si el sitio usa HTTPS
            if header_name == "Strict-Transport-Security":
                parsed = urlparse(url)
                if parsed.scheme != "https":
                    # Reportar como info: HSTS no aplica en HTTP
                    findings.append(
                        FindingInput(
                            source="passive_headers",
                            category="HSTS Inapplicable",
                            title=f"El sitio usa HTTP — HSTS no puede aplicarse",
                            severity="Info",
                            cvss_score=0.0,
                            description="HSTS solo funciona sobre HTTPS. El sitio debería migrar a HTTPS.",
                            remediation="Configurar HTTPS con un certificado válido y luego agregar HSTS.",
                        )
                    )
                    continue

            if header_lower not in response_headers:
                findings.append(
                    FindingInput(
                        source="passive_headers",
                        category=info["category"],
                        title=f"Header '{header_name}' no encontrado",
                        severity=info["severity"],
                        cvss_score=info["cvss"],
                        description=info["description"],
                        remediation=info["remediation"],
                    )
                )

    except httpx.ConnectError:
        findings.append(
            FindingInput(
                source="passive_headers",
                category="Connection Error",
                title="No se pudo conectar al target",
                severity="Info",
                cvss_score=0.0,
                description=f"No se pudo establecer conexión con {url}",
                remediation="Verificar que la URL es correcta y el servidor está activo.",
            )
        )
    except Exception as e:
        findings.append(
            FindingInput(
                source="passive_headers",
                category="Scan Error",
                title=f"Error al verificar headers: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_headers")
