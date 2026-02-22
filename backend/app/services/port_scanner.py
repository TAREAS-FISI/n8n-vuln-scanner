"""
Port Scanner — Escanea los top 20 puertos peligrosos con socket.
"""
import asyncio
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from app.models.schemas import CheckResult, FindingInput

# Puertos objetivo con servicio asociado y nivel de riesgo
TARGET_PORTS = {
    21: {"service": "FTP", "severity": "Medium", "cvss": 5.3, "risky": True},
    22: {"service": "SSH", "severity": "Info", "cvss": 0.0, "risky": False},
    23: {"service": "Telnet", "severity": "High", "cvss": 7.5, "risky": True},
    25: {"service": "SMTP", "severity": "Low", "cvss": 3.7, "risky": False},
    80: {"service": "HTTP", "severity": "Info", "cvss": 0.0, "risky": False},
    110: {"service": "POP3", "severity": "Low", "cvss": 3.7, "risky": False},
    143: {"service": "IMAP", "severity": "Low", "cvss": 3.7, "risky": False},
    443: {"service": "HTTPS", "severity": "Info", "cvss": 0.0, "risky": False},
    445: {"service": "SMB", "severity": "High", "cvss": 8.1, "risky": True},
    993: {"service": "IMAPS", "severity": "Info", "cvss": 0.0, "risky": False},
    995: {"service": "POP3S", "severity": "Info", "cvss": 0.0, "risky": False},
    3306: {"service": "MySQL", "severity": "High", "cvss": 7.5, "risky": True},
    3389: {"service": "RDP", "severity": "High", "cvss": 7.5, "risky": True},
    5432: {"service": "PostgreSQL", "severity": "High", "cvss": 7.5, "risky": True},
    5900: {"service": "VNC", "severity": "High", "cvss": 7.5, "risky": True},
    6379: {"service": "Redis", "severity": "High", "cvss": 8.0, "risky": True},
    8080: {"service": "HTTP-Proxy", "severity": "Info", "cvss": 0.0, "risky": False},
    8443: {"service": "HTTPS-Alt", "severity": "Info", "cvss": 0.0, "risky": False},
    9200: {"service": "Elasticsearch", "severity": "High", "cvss": 8.0, "risky": True},
    11211: {"service": "Memcached", "severity": "High", "cvss": 7.5, "risky": True},
    27017: {"service": "MongoDB", "severity": "High", "cvss": 8.0, "risky": True},
}


def _scan_port(host: str, port: int, timeout: float = 3.0) -> tuple[int, bool]:
    """Intenta conectar a un puerto. Retorna (puerto, abierto)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except Exception:
        return port, False


async def check_ports(url: str) -> CheckResult:
    """
    Escanea los top 20 puertos peligrosos de un host.
    """
    start = time.perf_counter()
    findings: list[FindingInput] = []

    parsed = urlparse(url)
    host = parsed.hostname or parsed.path

    # Resolver hostname primero
    try:
        socket.getaddrinfo(host, None)
    except socket.gaierror:
        findings.append(
            FindingInput(
                source="passive_ports",
                category="DNS Resolution Error",
                title=f"No se pudo resolver el hostname: {host}",
                severity="Info",
                cvss_score=0.0,
                description=f"El hostname {host} no se pudo resolver vía DNS.",
                remediation="Verificar que la URL es correcta.",
            )
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return CheckResult(findings=findings, duration_ms=elapsed, source="passive_ports")

    # Escanear puertos en paralelo con ThreadPoolExecutor
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=20) as executor:
        tasks = [
            loop.run_in_executor(executor, _scan_port, host, port)
            for port in TARGET_PORTS
        ]
        results = await asyncio.gather(*tasks)

    open_ports = []
    for port, is_open in results:
        if is_open:
            info = TARGET_PORTS[port]
            open_ports.append(port)

            if info["risky"]:
                findings.append(
                    FindingInput(
                        source="passive_ports",
                        category="Dangerous Open Port",
                        title=f"Puerto {port} ({info['service']}) abierto",
                        severity=info["severity"],
                        cvss_score=info["cvss"],
                        description=(
                            f"El puerto {port} ({info['service']}) está abierto y accesible. "
                            f"Este servicio puede ser objetivo de ataques si no está correctamente asegurado."
                        ),
                        remediation=(
                            f"Si no es necesario, cerrar el puerto {port} con firewall. "
                            f"Si es necesario, asegurar que {info['service']} requiere autenticación "
                            f"y está actualizado. Restringir acceso por IP con iptables/firewalld."
                        ),
                    )
                )
            else:
                findings.append(
                    FindingInput(
                        source="passive_ports",
                        category="Open Port",
                        title=f"Puerto {port} ({info['service']}) abierto",
                        severity="Info",
                        cvss_score=0.0,
                        description=f"El puerto {port} ({info['service']}) está abierto (informativo).",
                    )
                )

    elapsed = int((time.perf_counter() - start) * 1000)
    return CheckResult(findings=findings, duration_ms=elapsed, source="passive_ports")
