"""
SSL/TLS Checker — Verifica certificado, protocolo, cipher y expiración.
"""
import ssl
import socket
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.models.schemas import CheckResult, FindingInput


def _parse_host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or parsed.path
    port = parsed.port or (443 if parsed.scheme == "https" else 443)
    return host, port


async def check_ssl(url: str) -> CheckResult:
    """
    Verifica el certificado SSL/TLS del target.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    parsed = urlparse(url)
    if parsed.scheme == "http" and not parsed.port:
        # HTTP sin puerto → probablemente no tiene SSL
        findings.append(
            FindingInput(
                source="passive_ssl",
                category="No HTTPS",
                title="El sitio no usa HTTPS",
                severity="High",
                cvss_score=7.4,
                description=(
                    "El sitio se sirve sobre HTTP sin cifrado. "
                    "Todo el tráfico (incluyendo credenciales) viaja en texto plano."
                ),
                remediation=(
                    "Configurar HTTPS con un certificado válido. "
                    "Opciones gratuitas: Let's Encrypt (certbot) o Cloudflare."
                ),
            )
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return CheckResult(findings=findings, duration_ms=elapsed, source="passive_ssl")

    host, port = _parse_host_port(url)

    try:
        # 1. Conexión con verificación (detecta certs inválidos)
        context_verify = ssl.create_default_context()
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                with context_verify.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    protocol_version = ssock.version()
                    cipher_info = ssock.cipher()
        except ssl.SSLCertVerificationError as e:
            # Certificado inválido — intentar sin verificación para obtener detalles
            findings.append(
                FindingInput(
                    source="passive_ssl",
                    category="Invalid Certificate",
                    title="Certificado SSL no válido",
                    severity="High",
                    cvss_score=7.5,
                    description=f"El certificado no pasó la verificación: {e}",
                    remediation="Obtener un certificado válido de una CA reconocida (Let's Encrypt es gratis).",
                )
            )
            # Reconectar sin verificar para obtener más datos
            context_noverify = ssl.create_default_context()
            context_noverify.check_hostname = False
            context_noverify.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=10) as sock:
                with context_noverify.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=False) or {}
                    protocol_version = ssock.version()
                    cipher_info = ssock.cipher()

        # 2. Verificar expiración del certificado
        if cert and "notAfter" in cert:
            not_after_str = cert["notAfter"]
            # Formato: 'Mon DD HH:MM:SS YYYY GMT'
            try:
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                not_after = not_after.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_left = (not_after - now).days

                if days_left < 0:
                    findings.append(
                        FindingInput(
                            source="passive_ssl",
                            category="Expired Certificate",
                            title=f"Certificado expirado hace {abs(days_left)} días",
                            severity="High",
                            cvss_score=7.5,
                            description=f"El certificado expiró el {not_after_str}.",
                            remediation="Renovar el certificado SSL inmediatamente.",
                        )
                    )
                elif days_left < 30:
                    findings.append(
                        FindingInput(
                            source="passive_ssl",
                            category="Certificate Expiring Soon",
                            title=f"Certificado expira en {days_left} días",
                            severity="Medium",
                            cvss_score=4.0,
                            description=f"El certificado expira el {not_after_str}.",
                            remediation="Renovar el certificado antes de que expire. Considerar auto-renovación con certbot.",
                        )
                    )
            except ValueError:
                pass

        # 3. Verificar versión del protocolo
        if protocol_version:
            weak_protocols = ["SSLv2", "SSLv3", "TLSv1", "TLSv1.0", "TLSv1.1"]
            if protocol_version in weak_protocols:
                findings.append(
                    FindingInput(
                        source="passive_ssl",
                        category="Weak TLS Protocol",
                        title=f"Protocolo débil: {protocol_version}",
                        severity="Medium",
                        cvss_score=5.9,
                        description=(
                            f"El servidor negoció {protocol_version}, que tiene vulnerabilidades conocidas "
                            "(POODLE, BEAST, etc.)."
                        ),
                        remediation=(
                            "Deshabilitar SSLv2, SSLv3, TLS 1.0 y TLS 1.1. "
                            "Usar solo TLS 1.2 y TLS 1.3.\n"
                            "Nginx: ssl_protocols TLSv1.2 TLSv1.3;\n"
                            "Apache: SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1"
                        ),
                    )
                )

        # 4. Verificar cipher suite
        if cipher_info:
            cipher_name = cipher_info[0]
            weak_ciphers = ["RC4", "DES", "3DES", "NULL", "EXPORT", "anon"]
            for weak in weak_ciphers:
                if weak.upper() in cipher_name.upper():
                    findings.append(
                        FindingInput(
                            source="passive_ssl",
                            category="Weak Cipher Suite",
                            title=f"Cipher suite débil: {cipher_name}",
                            severity="Medium",
                            cvss_score=5.3,
                            description=f"El servidor usa el cipher {cipher_name} que se considera inseguro.",
                            remediation=(
                                "Configurar cipher suites fuertes.\n"
                                "Nginx: ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';\n"
                                "Referencia: https://ssl-config.mozilla.org/"
                            ),
                        )
                    )
                    break

    except socket.timeout:
        findings.append(
            FindingInput(
                source="passive_ssl",
                category="Connection Timeout",
                title="Timeout al conectar por SSL/TLS",
                severity="Info",
                cvss_score=0.0,
                description=f"No se pudo establecer conexión SSL con {host}:{port} en 10 segundos.",
            )
        )
    except ConnectionRefusedError:
        findings.append(
            FindingInput(
                source="passive_ssl",
                category="Connection Refused",
                title="Puerto SSL/TLS cerrado",
                severity="Info",
                cvss_score=0.0,
                description=f"El puerto {port} de {host} rechazó la conexión.",
            )
        )
    except Exception as e:
        findings.append(
            FindingInput(
                source="passive_ssl",
                category="Scan Error",
                title=f"Error al verificar SSL: {type(e).__name__}",
                severity="Info",
                cvss_score=0.0,
                description=str(e),
            )
        )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_ssl")
