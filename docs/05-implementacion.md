# Entregable 5: Implementación — Repositorio y Despliegue

## 5.1 Repositorio Git

**URL del repositorio:** `https://github.com/TAREAS-FISI/n8n-vuln-scanner`

### Estructura del repositorio

```
n8n-vuln-scanner/
│
├── docker-compose.yml              # Orquestación de los 10 servicios
├── .env                            # Variables de entorno
├── .env.example                    # Plantilla de variables
├── .gitignore                      # Archivos excluidos de Git
├── README.md                       # Instrucciones completas de setup
│
├── frontend/                       # ── NEXT.JS 15 + TAILWIND CSS ──
│   ├── Dockerfile                  # Multi-stage build: deps → build → runner
│   ├── package.json                # Dependencias npm
│   ├── next.config.ts              # output: 'standalone' para Docker
│   ├── tsconfig.json               # Configuración TypeScript
│   ├── eslint.config.mjs           # Linting
│   ├── postcss.config.mjs          # PostCSS para Tailwind
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # Layout global con navbar
│       │   ├── page.tsx            # Home: ScanForm + escaneos recientes
│       │   ├── globals.css         # Estilos globales + Tailwind
│       │   ├── scan/
│       │   │   └── [id]/
│       │   │       └── page.tsx    # Detalle: progreso + reporte final
│       │   └── dashboard/
│       │       └── page.tsx        # Embed de Grafana
│       ├── components/
│       │   ├── ScanForm.tsx        # Input URL + botón "Escanear"
│       │   ├── ScanProgress.tsx    # Barra de progreso por 5 fases
│       │   ├── ScoreGauge.tsx      # Gauge circular SVG (0-100)
│       │   ├── SeverityBadge.tsx   # Badge coloreado por severidad
│       │   ├── ReportCard.tsx      # Tarjeta expandible de finding
│       │   ├── FindingsTable.tsx   # Tabla filtrable/ordenable
│       │   └── LLMRecommendation.tsx # Recomendaciones del LLM
│       └── lib/
│           ├── api.ts              # Cliente HTTP → FastAPI
│           └── types.ts            # TypeScript interfaces + constantes
│
├── backend/                        # ── FASTAPI + PYTHON 3.12 ──
│   ├── Dockerfile                  # python:3.12-slim + requirements
│   ├── requirements.txt            # 8 dependencias principales
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app + CORS + routers
│       ├── config.py               # Pydantic BaseSettings
│       ├── routers/
│       │   ├── health.py           # GET /health
│       │   ├── checks.py          # 7 endpoints POST /check/*
│       │   └── scans.py            # CRUD de scans + webhook n8n
│       ├── services/
│       │   ├── header_checker.py   # 12 headers HTTP de seguridad
│       │   ├── ssl_checker.py      # Certificado, protocolo, cipher
│       │   ├── port_scanner.py     # 21 puertos TCP peligrosos
│       │   ├── cookie_checker.py   # Flags Secure, HttpOnly, SameSite
│       │   ├── cors_checker.py     # Wildcard, reflected origin
│       │   ├── info_disclosure.py  # 9 rutas sensibles + version disclosure
│       │   ├── tech_detector.py    # 15+ patrones de detección
│       │   └── scorer.py           # Algoritmo de scoring ponderado
│       └── models/
│           ├── schemas.py          # 14 Pydantic schemas
│           └── database.py         # SQLAlchemy async models + engine
│
├── n8n-workflows/                  # ── WORKFLOWS EXPORTADOS (JSON) ──
│   ├── 01-scan-pipeline.json       # Workflow principal (5 fases)
│   ├── 02-zap-scan.json            # Sub-workflow ZAP
│   ├── 03-nuclei-scan.json         # Sub-workflow Nuclei
│   ├── 04-testssl-scan.json        # Sub-workflow testssl.sh
│   ├── 05-llm-analysis.json        # Sub-workflow Ollama
│   ├── 06-daily-report.json        # Reporte diario automatizado
│   ├── import-workflows.sh         # Script de importación
│   └── README.md                   # Documentación de workflows
│
├── grafana/                        # ── GRAFANA PROVISIONING ──
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasource.yml      # PostgreSQL como data source
│   │   └── dashboards/
│   │       └── dashboard.yml       # Auto-provisioning de dashboards
│   └── dashboards/
│       └── security-overview.json  # 8 paneles de seguridad
│
├── db/                             # ── DATABASE SCHEMA ──
│   └── init.sql                    # 4 tablas + 4 vistas + índices
│
├── datasets/                       # ── DATOS DE PRUEBA ──
│   ├── sample_scan_vulnerable.json # Resultado: DVWA vulnerable (score ~22)
│   ├── sample_scan_secure.json     # Resultado: target seguro (score ~88)
│   ├── sample_scan_error.json      # Resultado: URL inexistente
│   └── test_scenarios.md           # 6 escenarios documentados
│
└── docs/                           # ── DOCUMENTACIÓN ──
    ├── 01-definicion-problema.md
    ├── 02-diseno-conceptual.md
    ├── 03-modulo-inteligente.md
    ├── 04-arquitectura-tecnica.md
    ├── 05-implementacion.md
    ├── 06-datos-pruebas.md
    ├── 07-metricas-evaluacion.md
    ├── 08-defensa-tecnica.md
    └── informe-final.md
```

## 5.2 Instrucciones de Despliegue

### Requisitos previos

| Requisito | Versión mínima | Notas |
|---|---|---|
| Docker Desktop | v24+ | Con Docker Compose v2 |
| RAM | 8 GB mínimo | 16 GB recomendado para Ollama |
| Disco | 20 GB libres | Imágenes Docker + modelo LLM |
| GPU NVIDIA (opcional) | — | Acelera Ollama (5-10s vs 30-60s sin GPU) |

### Paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/TAREAS-FISI/n8n-vuln-scanner
cd n8n-vuln-scanner

# 2. Verificar que el .env existe (incluido en el repo)
cat .env

# 3. Levantar todos los servicios (primera vez ~10 min descargando imágenes)
docker compose up -d

# 4. Verificar que los 10 servicios están corriendo
docker compose ps

# 5. Descargar el modelo LLM de Ollama (~2 GB, una sola vez)
docker exec ollama ollama pull llama3.2:3b

# 6. Configurar DVWA (primera vez)
#    - Abrir http://localhost:8081
#    - Login: admin / password
#    - Ir a http://localhost:8081/setup.php
#    - Click "Create / Reset Database"
#    - Re-login: admin / password

# 7. Importar workflows en n8n (si no se auto-importan)
#    - Abrir http://localhost:5678
#    - Settings → Import Workflow
#    - Importar los JSON de n8n-workflows/

# 8. Verificar servicios
curl http://localhost:8000/health          # FastAPI OK
curl http://localhost:5678/healthz         # n8n OK
curl http://localhost:8080/JSON/core/view/version/  # ZAP OK
curl http://localhost:11434/api/tags       # Ollama + modelo OK
```

### Accesos

| Servicio | URL | Credenciales |
|---|---|---|
| Frontend (Next.js) | http://localhost:3000 | — |
| FastAPI Docs (Swagger) | http://localhost:8000/docs | — |
| n8n | http://localhost:5678 | admin / admin |
| Grafana | http://localhost:3001 | admin / admin |
| DVWA | http://localhost:8081 | admin / password |
| ZAP API | http://localhost:8080 | — |
| Ollama API | http://localhost:11434 | — |

## 5.3 Docker Compose — Configuración Clave

### Servicios que construyen imagen local

| Servicio | Dockerfile | Base image | Strategy |
|---|---|---|---|
| **frontend** | `frontend/Dockerfile` | `node:20-alpine` | Multi-stage (deps → build → standalone) |
| **backend** | `backend/Dockerfile` | `python:3.12-slim` | Single stage con requirements.txt |

### Comunicación entre servicios

Todos los servicios se comunican dentro de la red Docker `scanner-net` usando nombres de servicio como hostname:

- Frontend → Backend: `http://backend:8000`
- Backend → n8n: `http://n8n:5678`
- n8n → Backend: `http://backend:8000`
- n8n → ZAP: `http://zap:8080`
- n8n → Ollama: `http://ollama:11434`
- Backend → PostgreSQL: `postgresql+asyncpg://scanner:***@postgres:5432/vulnscanner`
- Grafana → PostgreSQL: `postgres:5432` (SQL directo)

### Persistencia

| Volumen Docker | Servicio | Datos |
|---|---|---|
| `postgres_data` | PostgreSQL | Base de datos completa |
| `n8n_data` | n8n | Workflows, credenciales, ejecuciones |
| `ollama_data` | Ollama | Modelo llama3.2:3b descargado |
| `grafana_data` | Grafana | Configuración personalizada |
| `zap_data` | ZAP | Datos de sesiones de escaneo |
| `scanner-shared` | n8n, nuclei, testssl | Archivos de resultados temporales |

### Comandos útiles

```bash
# Ver logs en tiempo real (todos los servicios)
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend

# Reiniciar un servicio sin detener los demás
docker compose restart backend

# Detener todo
docker compose down

# Reset completo (eliminar datos)
docker compose down -v

# Reconstruir imágenes locales
docker compose build --no-cache frontend backend

# Acceder a PostgreSQL directamente
docker exec -it postgres psql -U scanner -d vulnscanner
```

## 5.4 Código Destacado

### Backend: Scoring Algorithm

```python
# backend/app/services/scorer.py
def calculate_score(findings: list[dict]) -> dict:
    score = 100.0
    severity_factors = {"Critical": 25, "High": 15, "Medium": 8, "Low": 3, "Info": 0}
    source_weights = {
        "zap": 0.20, "passive_headers": 0.15, "testssl": 0.15,
        "nuclei": 0.15, "passive_ssl": 0.10, "passive_ports": 0.10,
        "passive_cookies": 0.05, "passive_cors": 0.05, "passive_disclosure": 0.05,
    }
    for finding in findings:
        penalty = severity_factors[finding["severity"]] * source_weights.get(finding["source"], 0.10)
        score -= penalty
    return {"global_score": round(max(0, min(100, score)), 1)}
```

### Frontend: Score Gauge

```tsx
// frontend/src/components/ScoreGauge.tsx
// SVG circular gauge con colores dinámicos:
// ≥80 verde ("Bueno"), ≥50 amarillo ("Regular"),
// ≥30 naranja ("Bajo"), <30 rojo ("Crítico")
// Animación CSS: strokeDashoffset transition 1s ease-out
```

### n8n: Webhook trigger + 5 fases secuenciales

Los workflows de n8n están exportados como JSON en `n8n-workflows/` y se importan en la interfaz web de n8n. El workflow principal (`01-scan-pipeline.json`) inicia con un Webhook Trigger y ejecuta las 5 fases del pipeline.
