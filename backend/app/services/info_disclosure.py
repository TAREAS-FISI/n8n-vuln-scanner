"""
Information Disclosure Checker — Busca archivos y rutas sensibles expuestas.
"""
import logging
import time
from urllib.parse import urljoin

import httpx

from app.models.schemas import CheckResult, FindingInput

logger = logging.getLogger(__name__)

# Rutas sensibles a verificar con su severidad
SENSITIVE_PATHS = [
    {
        "path": "/.env",
        "title": "Archivo .env expuesto",
        "severity": "Critical",
        "cvss": 9.8,
        "description": (
            "El archivo .env está accesible públicamente. "
            "Contiene variables de entorno con credenciales, API keys y configuración secreta."
        ),
        "remediation": "Bloquear acceso a .env desde el servidor web. Nginx: location ~ /\\.env { deny all; }",
        "check_content": True,
        "content_indicators": ["=", "DB_", "SECRET", "KEY", "PASSWORD", "TOKEN"],
    },
    {
        "path": "/.git/config",
        "title": "Repositorio Git expuesto (.git/config)",
        "severity": "High",
        "cvss": 8.6,
        "description": (
            "El directorio .git está accesible. Un atacante puede descargar "
            "el código fuente completo del proyecto, incluyendo historial de commits."
        ),
        "remediation": "Bloquear acceso al directorio .git. Nginx: location ~ /\\.git { deny all; }",
        "check_content": True,
        "content_indicators": ["[core]", "[remote", "repositoryformatversion"],
    },
    {
        "path": "/.git/HEAD",
        "title": "Repositorio Git expuesto (.git/HEAD)",
        "severity": "High",
        "cvss": 8.6,
        "description": "El archivo .git/HEAD es accesible, confirmando que el repositorio git está expuesto.",
        "remediation": "Bloquear acceso al directorio .git completo.",
        "check_content": True,
        "content_indicators": ["ref:", "refs/heads/"],
    },
    {
        "path": "/wp-config.php.bak",
        "title": "Backup de wp-config.php accesible",
        "severity": "Critical",
        "cvss": 9.8,
        "description": "Un backup del archivo de configuración de WordPress está expuesto con credenciales de BD.",
        "remediation": "Eliminar archivos .bak del servidor. Bloquear acceso a archivos de backup.",
        "check_content": True,
        "content_indicators": ["DB_NAME", "DB_USER", "DB_PASSWORD"],
    },
    {
        "path": "/server-status",
        "title": "Apache server-status expuesto",
        "severity": "Medium",
        "cvss": 5.3,
        "description": "El módulo mod_status de Apache está accesible públicamente mostrando información interna.",
        "remediation": "Restringir /server-status a IPs internas. Apache: <Location /server-status> Require local </Location>",
        "check_content": True,
        "content_indicators": ["Apache Server Status", "Server uptime", "requests/sec"],
    },
    {
        "path": "/phpinfo.php",
        "title": "phpinfo() accesible",
        "severity": "Medium",
        "cvss": 5.3,
        "description": "phpinfo() expone configuración detallada del servidor PHP, paths y variables de entorno.",
        "remediation": "Eliminar el archivo phpinfo.php del servidor de producción.",
        "check_content": True,
        "content_indicators": ["phpinfo()", "PHP Version", "Configuration"],
    },
    {
        "path": "/.htaccess",
        "title": "Archivo .htaccess accesible",
        "severity": "Medium",
        "cvss": 5.3,
        "description": "El archivo .htaccess está accesible, revelando reglas de configuración del servidor.",
        "remediation": "Bloquear acceso a archivos ocultos: location ~ /\\. { deny all; }",
        "check_content": True,
        "content_indicators": ["RewriteEngine", "RewriteRule", "AuthType"],
    },
    {
        "path": "/.DS_Store",
        "title": "Archivo .DS_Store expuesto",
        "severity": "Low",
        "cvss": 3.7,
        "description": "Archivo de macOS que puede revelar la estructura de directorios del servidor.",
        "remediation": "Eliminar .DS_Store y bloquear su acceso. Agregar a .gitignore.",
        "check_content": False,
    },
    {
        "path": "/crossdomain.xml",
        "title": "crossdomain.xml permisivo",
        "severity": "Medium",
        "cvss": 4.3,
        "description": "Política crossdomain.xml permite acceso desde cualquier dominio a plugins Flash/Silverlight.",
        "remediation": "Restringir crossdomain.xml a dominios de confianza o eliminar si Flash no se usa.",
        "check_content": True,
        "content_indicators": ['allow-access-from domain="*"'],
    },
]


async def check_info_disclosure(url: str) -> CheckResult:
    """
    Verifica si rutas/archivos sensibles están accesibles públicamente.
    También revisa headers que revelan información del servidor.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=False, verify=False
        ) as client:

            # 1. Verificar rutas sensibles
            for item in SENSITIVE_PATHS:
                try:
                    target_url = urljoin(url.rstrip("/") + "/", item["path"].lstrip("/"))
                    response = await client.get(target_url)

                    if response.status_code == 200:
                        # Verificar contenido si es necesario (evitar falsos positivos)
                        is_real = True
                        if item.get("check_content") and item.get("content_indicators"):
                            body = response.text[:5000]
                            is_real = any(
                                indicator in body
                                for indicator in item["content_indicators"]
                            )

                        if is_real:
                            findings.append(
                                FindingInput(
                                    source="passive_disclosure",
                                    category="Information Disclosure",
                                    title=item["title"],
                                    severity=item["severity"],
                                    cvss_score=item["cvss"],
                                    description=item["description"],
                                    remediation=item.get("remediation"),
                                    raw_data={"path": item["path"], "status_code": 200},
                                )
                            )
                except Exception:
                    continue

            # 2. Verificar robots.txt por paths sensibles
            try:
                robots_url = urljoin(url.rstrip("/") + "/", "robots.txt")
                response = await client.get(robots_url)
                if response.status_code == 200 and "disallow" in response.text.lower():
                    sensitive_disallows = []
                    for line in response.text.splitlines():
                        line = line.strip().lower()
                        if line.startswith("disallow:"):
                            path = line.split(":", 1)[1].strip()
                            sensitive_keywords = [
                                "admin", "login", "api", "backup", "config",
                                "secret", "private", "internal", "dashboard",
                            ]
                            if any(kw in path.lower() for kw in sensitive_keywords):
                                sensitive_disallows.append(path)

                    if sensitive_disallows:
                        findings.append(
                            FindingInput(
                                source="passive_disclosure",
                                category="Information Disclosure",
                                title="robots.txt revela rutas sensibles",
                                severity="Info",
                                cvss_score=1.0,
                                description=(
                                    f"robots.txt contiene Disallow para rutas potencialmente sensibles: "
                                    f"{', '.join(sensitive_disallows[:10])}"
                                ),
                                remediation=(
                                    "Considerar si las rutas listadas en robots.txt revelan información "
                                    "útil para un atacante. Protegerlas con autenticación."
                                ),
                                raw_data={"sensitive_paths": sensitive_disallows},
                            )
                        )
            except Exception:
                pass

            # 3. Verificar headers que revelan versiones
            try:
                response = await client.get(url)
                server = response.headers.get("server", "")
                xpb = response.headers.get("x-powered-by", "")

                if server and any(c.isdigit() for c in server):
                    findings.append(
                        FindingInput(
                            source="passive_disclosure",
                            category="Server Version Disclosure",
                            title=f"Header Server revela versión: {server}",
                            severity="Low",
                            cvss_score=3.7,
                            description=(
                                f"El header Server expone: '{server}'. "
                                "La versión facilita que un atacante busque vulnerabilidades conocidas."
                            ),
                            remediation=(
                                "Ocultar la versión del servidor.\n"
                                "Nginx: server_tokens off;\n"
                                "Apache: ServerTokens Prod"
                            ),
                        )
                    )

                if xpb:
                    findings.append(
                        FindingInput(
                            source="passive_disclosure",
                            category="Technology Disclosure",
                            title=f"Header X-Powered-By revela tecnología: {xpb}",
                            severity="Low",
                            cvss_score=3.7,
                            description=(
                                f"El header X-Powered-By expone: '{xpb}'. "
                                "Facilita ataques dirigidos a la tecnología específica."
                            ),
                            remediation="Eliminar el header X-Powered-By. PHP: expose_php = Off en php.ini",
                        )
                    )
            except Exception:
                pass

    except Exception as e:
        logger.error("Info disclosure check — error inesperado para %s: %s", url, e, exc_info=True)
        findings.append(
            FindingInput(
                source="passive_disclosure",
                category="Scan Error",
                title=f"Error al verificar disclosure: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_disclosure")
