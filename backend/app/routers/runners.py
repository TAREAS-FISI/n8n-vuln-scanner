"""
Router: Runners — Ejecuta herramientas externas (testssl, nuclei)
via docker exec. Reemplaza los nodos executeCommand de n8n (eliminados
en n8n v2.x).
"""
import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/run", tags=["Runners"])


class RunRequest(BaseModel):
    url: str
    scan_id: str


@router.post("/testssl")
async def run_testssl(body: RunRequest):
    """
    Ejecuta testssl.sh en el contenedor 'testssl' via docker exec.
    Retorna stdout compatible con el nodo 'Parsear testssl' de n8n.
    """
    output_file = f"/tmp/scanner/testssl_{body.scan_id}.json"
    shell_cmd = (
        f"testssl.sh --jsonfile {output_file} --quiet --fast {body.url} 2>/dev/null; "
        f"cat {output_file} 2>/dev/null || echo '[]'"
    )
    cmd = ["docker", "exec", "testssl", "/bin/sh", "-c", shell_cmd]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180.0)
        stdout_str = stdout.decode("utf-8", errors="replace")
        logger.info(
            "testssl %s: returncode=%d stdout_len=%d",
            body.url, proc.returncode, len(stdout_str),
        )
        return {"stdout": stdout_str, "returncode": proc.returncode}
    except asyncio.TimeoutError:
        logger.warning("testssl timeout para %s", body.url)
        return {"stdout": "[]", "returncode": 1}
    except Exception as e:
        logger.error("Error ejecutando testssl: %s", e)
        return {"stdout": "[]", "returncode": 1}


@router.post("/nuclei")
async def run_nuclei(body: RunRequest):
    """
    Ejecuta nuclei en el contenedor 'nuclei' via docker exec.
    Retorna stdout compatible con el nodo 'Parsear Nuclei' de n8n.
    """
    cmd = [
        "docker", "exec", "nuclei",
        "nuclei",
        "-u", body.url,
        "-j",
        "-severity", "critical,high,medium",
        "-silent",
        "-timeout", "5",
        "-retries", "1",
        "-no-color",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180.0)
        stdout_str = stdout.decode("utf-8", errors="replace")
        logger.info(
            "nuclei %s: returncode=%d stdout_len=%d",
            body.url, proc.returncode, len(stdout_str),
        )
        return {"stdout": stdout_str, "returncode": proc.returncode}
    except asyncio.TimeoutError:
        logger.warning("nuclei timeout para %s", body.url)
        return {"stdout": "", "returncode": 1}
    except Exception as e:
        logger.error("Error ejecutando nuclei: %s", e)
        return {"stdout": "", "returncode": 1}
