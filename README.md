# 🛡️ n8n Vulnerability Scanner

**Scanner de Vulnerabilidades Web Inteligente** — Proyecto de Sistemas Inteligentes

Un sistema que orquesta 4 fuentes de detección de vulnerabilidades (FastAPI checks, OWASP ZAP, Nuclei, testssl.sh), las analiza con IA local (Ollama) y presenta resultados en un dashboard interactivo.

---

## Stack Tecnológico

| Componente | Tecnología | Puerto |
|---|---|---|
| Frontend | Next.js + Tailwind CSS | `3000` |
| Backend / API | FastAPI (Python) | `8000` |
| Orquestador | n8n | `5678` |
| Base de Datos | PostgreSQL 16 | `5432` |
| Scanner DAST | OWASP ZAP | `8080` |
| LLM Local | Ollama (llama3.2:3b) | `11434` |
| Dashboards | Grafana | `3001` |
| Target de prueba | DVWA | `8081` |
| Scanner CVEs | Nuclei | — (CLI) |
| Auditoría SSL | testssl.sh | — (CLI) |

---

## Requisitos Previos

- **Docker Desktop** (v24+) con Docker Compose v2
- **8 GB RAM** mínimo (16 GB recomendado para Ollama)
- **GPU NVIDIA** (opcional, acelera Ollama significativamente)
  - Si no tienes GPU, elimina la sección `deploy` del servicio `ollama` en `docker-compose.yml`
- **20 GB** de espacio en disco (imágenes Docker + modelo LLM)

---

## Instalación y Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/TAREAS-FISI/n8n-vuln-scanner
cd n8n-vuln-scanner
```

### 2. Configurar variables de entorno

```bash
# El archivo .env ya está incluido con valores por defecto
# Editar .env si deseas cambiar contraseñas
```

### 3. Levantar todos los servicios

```bash
docker compose up -d
```

> ⏳ La primera ejecución descargará ~10 GB de imágenes Docker. Paciencia.

### 4. Verificar que los servicios están corriendo

```bash
docker compose ps
```

Deberías ver los 10 servicios en estado `running` o `Up`.

### 5. Descargar el modelo de Ollama

```bash
docker exec ollama ollama pull llama3.2:3b
```

> Esto descarga ~2 GB. Solo se hace una vez.

### 6. Configurar DVWA (primera vez)

1. Abrir http://localhost:8081
2. Login: `admin` / `password`
3. Ir a http://localhost:8081/setup.php
4. Click en **"Create / Reset Database"**
5. Volver a login: `admin` / `password`

### 7. Verificar servicios

```bash
# n8n
curl http://localhost:5678/healthz

# ZAP
curl http://localhost:8080/JSON/core/view/version/

# Ollama (verificar modelo)
curl http://localhost:11434/api/tags

# DVWA
curl http://localhost:8081

# FastAPI (cuando esté implementado)
curl http://localhost:8000/health
```

---

## Accesos Rápidos

| Servicio | URL | Credenciales |
|---|---|---|
| **Frontend** | http://localhost:3000 | — |
| **FastAPI Docs** | http://localhost:8000/docs | — |
| **n8n** | http://localhost:5678 | `admin` / `admin` |
| **Grafana** | http://localhost:3001 | `admin` / `admin` |
| **DVWA** | http://localhost:8081 | `admin` / `password` |
| **ZAP API** | http://localhost:8080 | — |
| **Ollama API** | http://localhost:11434 | — |

---

## Arquitectura

```
Usuario → Next.js(:3000) → FastAPI(:8000) → n8n(:5678)
                                                │
                      ┌─────────┬───────────┬───┴────────┐
                      ▼         ▼           ▼            ▼
                  FastAPI    testssl.sh   Nuclei     OWASP ZAP
                  Checks     SSL/TLS     9000+ CVE   Spider+DAST
                      │         │           │            │
                      └─────────┴───────────┴────────────┘
                                        │
                                  Merge + Score
                                        │
                                   Ollama LLM
                                   (análisis IA)
                                        │
                                   PostgreSQL
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                          Next.js              Grafana
                          (reporte)           (dashboard)
```

---

## Comandos Útiles

```bash
# Levantar todo
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f n8n

# Detener todo
docker compose down

# Detener y eliminar volumenes (reset completo)
docker compose down -v

# Ejecutar tests del backend
docker exec backend pytest -v

# Acceder a PostgreSQL
docker exec -it postgres psql -U scanner -d vulnscanner
```

---

## Testing y Datasets

La carpeta `datasets/` contiene escenarios de prueba y resultados simulados:

| Archivo | Descripción |
|---|---|
| `test_scenarios.md` | 6 escenarios de prueba con targets de distinta seguridad |
| `sample_scan_vulnerable.json` | Resultado simulado de un target vulnerable (DVWA) — score ~22 |
| `sample_scan_secure.json` | Resultado simulado de un target seguro (github.com) — score ~88 |
| `sample_scan_error.json` | Resultado simulado cuando el target no existe |

### Quick Test

```bash
# 1. Verificar que el backend responde y la DB está conectada
curl http://localhost:8000/health

# 2. Ejecutar un check individual (no necesita n8n)
curl -X POST http://localhost:8000/check/headers \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://github.com"}'

# 3. Ejecutar un scan completo (requiere n8n y todos los servicios)
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url": "http://dvwa:80"}'
```

---

## Grafana Dashboard

El dashboard de Grafana se provisiona automáticamente con **10 paneles**:

1. **Gauge** — Score promedio de seguridad
2. **Pie Chart** — Distribución de findings por severidad
3. **Bar Chart** — Top 10 vulnerabilidades más frecuentes
4. **Time Series** — Scores de seguridad en el tiempo
5. **Tabla** — Últimos 20 escaneos con estado y score
6. **Stat** — Total escaneos / Total findings / Promedio findings/scan
7. **Bar Chart** — Findings por fuente de detección
8. **Stacked Bar** — Severidad por escaneo (últimos 10)

Acceder a Grafana: http://localhost:3001 (`admin` / `admin`)

---

## Nota sobre GPU

Si **no tienes GPU NVIDIA**, edita `docker-compose.yml` y comenta la sección `deploy` del servicio `ollama`:

```yaml
  ollama:
    image: ollama/ollama:latest
    # Comentar estas líneas si no tienes GPU:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]
```

Ollama funcionará con CPU, pero será más lento (~30-60s por análisis vs ~5-10s con GPU).

---

## Equipo

Proyecto de Sistemas Inteligentes — Curso Universitario (2026)