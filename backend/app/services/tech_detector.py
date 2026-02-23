"""
Tech Detector — Detecta tecnologías desde headers, cookies y meta tags.
"""
import logging
import re
import time

import httpx

from app.models.schemas import CheckResult, FindingInput

logger = logging.getLogger(__name__)

# Cookies conocidas → tecnología
COOKIE_TECH_MAP = {
    "PHPSESSID": "PHP",
    "ASP.NET_SessionId": "ASP.NET",
    "JSESSIONID": "Java (Servlet/JSP)",
    "laravel_session": "Laravel (PHP)",
    "ci_session": "CodeIgniter (PHP)",
    "rack.session": "Ruby (Rack)",
    "connect.sid": "Node.js (Express)",
    "_rails_session": "Ruby on Rails",
    "django_session": "Django (Python)",
    "wp_": "WordPress",
    "XSRF-TOKEN": "Laravel / Angular",
}

# Patrones en meta tags y body HTML
HTML_TECH_PATTERNS = [
    (r'<meta[^>]*name=["\']generator["\'][^>]*content=["\']([^"\']+)', "CMS/Generator"),
    (r"wp-content/", "WordPress"),
    (r"wp-includes/", "WordPress"),
    (r"/sites/default/files", "Drupal"),
    (r"Joomla!", "Joomla"),
    (r"shopify\.com", "Shopify"),
    (r"cdn\.shopify\.com", "Shopify"),
    (r"next/static", "Next.js"),
    (r"__next", "Next.js"),
    (r"__nuxt", "Nuxt.js"),
    (r"react", "React"),
    (r"ng-version", "Angular"),
    (r"vue\.js|vuejs", "Vue.js"),
    (r"jquery", "jQuery"),
    (r"bootstrap", "Bootstrap"),
]


async def detect_technologies(url: str) -> CheckResult:
    """
    Detecta tecnologías web del target a partir de headers, cookies y HTML.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []
    detected: set[str] = set()

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url)

        # 1. Detectar desde header Server
        server = response.headers.get("server", "")
        if server:
            detected.add(f"Server: {server}")

        # 2. Detectar desde header X-Powered-By
        xpb = response.headers.get("x-powered-by", "")
        if xpb:
            detected.add(f"X-Powered-By: {xpb}")

        # 3. Detectar desde cookies
        set_cookies = response.headers.get_list("set-cookie")
        for cookie_str in set_cookies:
            cookie_name = cookie_str.split("=")[0].strip()
            for known_cookie, tech in COOKIE_TECH_MAP.items():
                if known_cookie.lower() in cookie_name.lower():
                    detected.add(tech)
                    break

        # 4. Detectar desde HTML (primeros 50KB)
        body = response.text[:50000].lower()
        for pattern, tech in HTML_TECH_PATTERNS:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                if tech == "CMS/Generator":
                    detected.add(f"Generator: {match.group(1)}")
                else:
                    detected.add(tech)

        # 5. Detectar desde header X-Generator
        x_gen = response.headers.get("x-generator", "")
        if x_gen:
            detected.add(f"Generator: {x_gen}")

        # Crear un finding informativo con todas las tecnologías
        if detected:
            findings.append(
                FindingInput(
                    source="passive_tech",
                    category="Technology Detection",
                    title=f"Tecnologías detectadas: {len(detected)}",
                    severity="Info",
                    cvss_score=0.0,
                    description=(
                        "Tecnologías identificadas en el target:\n• "
                        + "\n• ".join(sorted(detected))
                    ),
                    remediation=(
                        "Ocultar información de tecnología donde sea posible para dificultar "
                        "reconocimiento. Mantener todas las tecnologías actualizadas."
                    ),
                    raw_data={"technologies": sorted(detected)},
                )
            )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        logger.warning("Tech detection — conexión fallida para %s: %s", url, e)
        findings.append(
            FindingInput(
                source="passive_tech",
                category="Connection Error",
                title="No se pudo conectar al target",
                severity="Info",
                cvss_score=0.0,
                description=f"No se pudo establecer conexión con {url}: {type(e).__name__}",
            )
        )
    except Exception as e:
        logger.error("Tech detection — error inesperado para %s: %s", url, e, exc_info=True)
        findings.append(
            FindingInput(
                source="passive_tech",
                category="Scan Error",
                title=f"Error al detectar tecnologías: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_tech")
