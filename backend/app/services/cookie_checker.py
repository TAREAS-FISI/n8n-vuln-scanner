"""
Cookie Checker — Verifica flags de seguridad en cookies (Secure, HttpOnly, SameSite).
"""
import time

import httpx

from app.models.schemas import CheckResult, FindingInput


async def check_cookies(url: str) -> CheckResult:
    """
    Analiza las cookies de la respuesta HTTP y verifica flags de seguridad.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url)

        # Obtener todos los Set-Cookie headers
        set_cookie_headers = response.headers.get_list("set-cookie")

        if not set_cookie_headers:
            elapsed = int((time.perf_counter() - start) * 1000)
            return CheckResult(findings=findings, duration_ms=elapsed, source="passive_cookies")

        is_https = url.startswith("https://")

        for cookie_header in set_cookie_headers:
            # Parsear nombre de la cookie
            parts = cookie_header.split(";")
            cookie_name = parts[0].split("=")[0].strip() if parts else "unknown"
            flags_lower = cookie_header.lower()

            # Verificar flag Secure
            if is_https and "secure" not in flags_lower:
                findings.append(
                    FindingInput(
                        source="passive_cookies",
                        category="Cookie Missing Secure Flag",
                        title=f"Cookie '{cookie_name}' sin flag Secure",
                        severity="Medium",
                        cvss_score=4.3,
                        description=(
                            f"La cookie '{cookie_name}' no tiene el flag Secure. "
                            "Podría ser transmitida en conexiones HTTP no cifradas."
                        ),
                        remediation=f"Agregar flag Secure a la cookie '{cookie_name}': Set-Cookie: {cookie_name}=...; Secure",
                    )
                )

            # Verificar flag HttpOnly
            if "httponly" not in flags_lower:
                findings.append(
                    FindingInput(
                        source="passive_cookies",
                        category="Cookie Missing HttpOnly Flag",
                        title=f"Cookie '{cookie_name}' sin flag HttpOnly",
                        severity="Medium",
                        cvss_score=4.3,
                        description=(
                            f"La cookie '{cookie_name}' no tiene el flag HttpOnly. "
                            "Podría ser accedida por JavaScript, facilitando ataques XSS."
                        ),
                        remediation=f"Agregar flag HttpOnly: Set-Cookie: {cookie_name}=...; HttpOnly",
                    )
                )

            # Verificar flag SameSite
            if "samesite" not in flags_lower:
                findings.append(
                    FindingInput(
                        source="passive_cookies",
                        category="Cookie Missing SameSite Flag",
                        title=f"Cookie '{cookie_name}' sin flag SameSite",
                        severity="Low",
                        cvss_score=3.1,
                        description=(
                            f"La cookie '{cookie_name}' no tiene el flag SameSite. "
                            "Podría ser enviada en requests cross-site, facilitando CSRF."
                        ),
                        remediation=f"Agregar flag SameSite: Set-Cookie: {cookie_name}=...; SameSite=Lax (o Strict)",
                    )
                )

    except httpx.ConnectError:
        findings.append(
            FindingInput(
                source="passive_cookies",
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
                source="passive_cookies",
                category="Scan Error",
                title=f"Error al verificar cookies: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_cookies")
