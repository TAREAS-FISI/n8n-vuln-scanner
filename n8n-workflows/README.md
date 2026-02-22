# Workflows n8n — Guía de Configuración

## Workflows Incluidos

| Archivo | Nombre | Descripción |
|---|---|---|
| `01-scan-pipeline.json` | Scan Pipeline Principal | Workflow completo con las 5 fases del escaneo |
| `02-zap-scan.json` | ZAP Scan (Sub-workflow) | Spider + Active Scan con OWASP ZAP |
| `03-nuclei-scan.json` | Nuclei Scan (Sub-workflow) | Detección de CVEs con Nuclei |
| `04-testssl-scan.json` | testssl Scan (Sub-workflow) | Auditoría SSL/TLS con testssl.sh |
| `05-llm-analysis.json` | LLM Analysis (Sub-workflow) | Análisis inteligente con Ollama |
| `06-daily-report.json` | Reporte Diario | Resumen automático diario a las 8am |

## Importar Workflows

### Opción 1: Importar Manualmente (Recomendado)

1. Abrir n8n en `http://localhost:5678` (admin/admin)
2. Ir a **Workflows** → **Import from File**
3. Importar **primero** los sub-workflows (02-05)
4. Luego importar el pipeline principal (01) y el reporte diario (06)
5. **Activar** el workflow `01 — Scan Pipeline Principal`

### Opción 2: Script Automático

```bash
bash n8n-workflows/import-workflows.sh
```

## Pipeline Principal (01-scan-pipeline.json)

### Flujo

```
[Webhook POST /webhook/scan]
    │
    ├─── FASE 1: Checks Pasivos (paralelo, ~10s) ────────────
    │    ├── POST /check/headers
    │    ├── POST /check/ssl  
    │    ├── POST /check/ports
    │    ├── POST /check/cookies
    │    ├── POST /check/cors
    │    └── POST /check/disclosure
    │    → Merge → Guardar findings → Marcar fase completada
    │
    ├─── FASE 2: testssl.sh (secuencial, ~30-60s) ───────────
    │    └── docker exec testssl testssl.sh → parsear JSON
    │    → Guardar findings → Marcar fase completada
    │
    ├─── FASE 3: Nuclei (secuencial, ~1-3min) ───────────────
    │    └── docker exec nuclei nuclei -u {url} → parsear JSONL
    │    → Guardar findings → Marcar fase completada
    │
    ├─── FASE 4: OWASP ZAP (secuencial, ~3-8min) ────────────
    │    ├── Spider → polling cada 5s
    │    └── Active Scan → polling cada 10s
    │    → Fetch alertas → Guardar findings → Marcar fase completada
    │
    └─── FASE 5: Scoring + LLM (secuencial, ~10-30s) ────────
         ├── POST /score → calcula score global
         ├── POST ollama/api/chat → análisis inteligente
         └── Guardar LLM analysis → Marcar scan completado
```

### Webhook

- **Método:** POST
- **URL:** `http://n8n:5678/webhook/scan` (interno) o `http://localhost:5678/webhook/scan` (externo)
- **Body:**
```json
{
  "url": "http://dvwa:8081",
  "scan_id": "uuid-del-scan"
}
```

### Manejo de Errores

Cada fase tiene error handlers que:
- Marcan la fase como `failed` o `skipped`
- Continúan con la siguiente fase (no detienen el pipeline)
- Registran el error para debugging

## Requisitos para Execute Command

El workflow principal usa `docker exec` para ejecutar testssl.sh y Nuclei en sus contenedores respectivos. Para que esto funcione:

1. El contenedor de n8n **debe** tener acceso al Docker socket (`/var/run/docker.sock`)
2. El contenedor de n8n **debe** ejecutarse como root (ya configurado en docker-compose)
3. Los contenedores `nuclei` y `testssl` deben estar en la misma red Docker

## Probar el Pipeline

```bash
# 1. Verificar que n8n está corriendo
curl http://localhost:5678/healthz

# 2. Disparar un escaneo manualmente
curl -X POST http://localhost:5678/webhook/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "http://dvwa:8081", "scan_id": "test-123"}'

# 3. O mejor, desde el backend (que crea el registro en BD):
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "http://dvwa:8081"}'
```

## Notas

- Los workflows usan `http://backend:8000` (nombre interno Docker)
- ZAP se accede en `http://zap:8080` (interno)
- Ollama en `http://ollama:11434` (interno)
- El modelo Ollama (`llama3.2:3b`) debe estar descargado antes del primer escaneo:
  ```bash
  docker exec ollama ollama pull llama3.2:3b
  ```
