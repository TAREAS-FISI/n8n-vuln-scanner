# n8n Vulnerability Scanner

Scanner de vulnerabilidades web que orquesta 4 herramientas de deteccion (FastAPI checks, OWASP ZAP, Nuclei, testssl.sh), analiza resultados con IA local (Ollama) y presenta reportes en un dashboard interactivo.

---

## Requisitos

- **Docker Desktop** (v24+) con Docker Compose v2
- **8 GB RAM** minimo (16 GB recomendado)
- **20 GB** de disco (imagenes Docker + modelo LLM)
- **GPU NVIDIA** (opcional, acelera Ollama). Sin GPU, comentar la seccion `deploy` del servicio `ollama` en `docker-compose.yml`

---

## Variables de Entorno

Copiar `.env.example` a `.env` y ajustar los valores:

```bash
cp .env.example .env
```

| Variable | Descripcion | Valor por defecto |
|---|---|---|
| `POSTGRES_USER` | Usuario de PostgreSQL | `scanner` |
| `POSTGRES_PASSWORD` | Password de PostgreSQL | `scanner_secret_2026` |
| `POSTGRES_DB` | Nombre de la base de datos | `vulnscanner` |
| `N8N_ENCRYPTION_KEY` | Clave de cifrado de n8n (cambiar en produccion) | `cambiar-esta-clave-en-produccion` |
| `WEBHOOK_URL` | URL base de webhooks de n8n | `http://localhost:5678/` |
| `N8N_OWNER_EMAIL` | Email del owner de n8n | `admin@vulnscanner.local` |
| `N8N_OWNER_PASSWORD` | Password del owner de n8n (min 8 chars, 1 mayuscula, 1 numero) | `Admin123!` |
| `GF_SECURITY_ADMIN_USER` | Usuario admin de Grafana | `admin` |
| `GF_SECURITY_ADMIN_PASSWORD` | Password admin de Grafana | `admin` |
| `OLLAMA_MODEL` | Modelo LLM para analisis | `llama3.2:3b` |
| `DVWA_SECURITY_LEVEL` | Nivel de seguridad de DVWA (`low` para testing) | `low` |

---

## Ejecucion desde Cero

### 1. Clonar y configurar

```bash
git clone https://github.com/TAREAS-FISI/n8n-vuln-scanner
cd n8n-vuln-scanner
cp .env.example .env
```

### 2. Levantar los servicios

```bash
docker compose up -d
```

> La primera ejecucion descarga ~10 GB de imagenes. Paciencia.

### 3. Verificar que todo esta corriendo

```bash
docker compose ps
```

Los 11 servicios deben estar en estado `running` (excepto `n8n-init` que termina con `Exited (0)` tras completar la inicializacion).

### 4. Verificar la inicializacion de n8n

```bash
docker compose logs n8n-init
```

Debe mostrar: owner creado, workflow importado y activado. Si falla, re-ejecutar:

```bash
docker compose restart n8n-init
```

### 5. Descargar el modelo de Ollama

```bash
docker exec ollama ollama pull llama3.2:3b
```

> Descarga ~2 GB. Solo se hace una vez.

### 6. Configurar DVWA (primera vez)

1. Abrir http://localhost:8081
2. Login: `admin` / `password`
3. Ir a http://localhost:8081/setup.php
4. Click en **"Create / Reset Database"**
5. Login de nuevo: `admin` / `password`

### 7. Listo - Lanzar un escaneo

```bash
# Escaneo completo via API
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url": "http://dvwa:80"}'

# O usar el frontend en http://localhost:3000
```

---

## Servicios y Puertos

| Servicio | Tecnologia | Puerto | URL |
|---|---|---|---|
| Frontend | Next.js | `3000` | http://localhost:3000 |
| Backend API | FastAPI | `8000` | http://localhost:8000/docs |
| n8n | Orquestador | `5678` | http://localhost:5678 |
| PostgreSQL | Base de datos | `5432` | — |
| OWASP ZAP | Scanner DAST | `8080` | http://localhost:8080 |
| Ollama | LLM local | `11434` | http://localhost:11434 |
| Grafana | Dashboards | `3001` | http://localhost:3001 |
| DVWA | Target vulnerable | `8081` | http://localhost:8081 |
| Nuclei | Scanner CVEs | — | CLI via backend |
| testssl | Auditoria SSL | — | CLI via backend |
| n8n-init | Auto-init | — | One-shot, termina solo |

### Credenciales

| Servicio | Usuario | Password |
|---|---|---|
| n8n | Valor de `N8N_OWNER_EMAIL` | Valor de `N8N_OWNER_PASSWORD` |
| Grafana | `admin` | `admin` |
| DVWA | `admin` | `password` |

---

## Arquitectura

```
Usuario --> Next.js(:3000) --> FastAPI(:8000) --> n8n(:5678)
                                                    |
                      +----------+-----------+------+----------+
                      v          v           v                 v
                  FastAPI    testssl.sh    Nuclei          OWASP ZAP
                  Checks     SSL/TLS     9000+ CVE        Spider+DAST
                      |          |           |                 |
                      +----------+-----------+-----------------+
                                        |
                                  Merge + Score
                                        |
                                   Ollama LLM
                                  (analisis IA)
                                        |
                                   PostgreSQL
                                        |
                              +---------+---------+
                              v                   v
                          Next.js              Grafana
                         (reporte)           (dashboard)
```

**Pipeline de escaneo (orquestado por n8n):**
1. **passive_checks** — 6 checks en paralelo (headers, SSL, puertos, cookies, CORS, disclosure)
2. **testssl** — Auditoria SSL/TLS profunda
3. **nuclei** — Deteccion de CVEs con 9000+ templates
4. **zap** — Spider + Active Scan (DAST)
5. **scoring_llm** — Analisis y scoring con Ollama

---

## Comandos Utiles

```bash
# Levantar todo
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Logs de un servicio especifico
docker compose logs -f backend
docker compose logs -f n8n

# Detener todo
docker compose down

# Reset completo (elimina datos)
docker compose down -v

# Re-inicializar n8n (re-importar workflows)
docker compose restart n8n-init

# Acceder a PostgreSQL
docker exec -it postgres psql -U scanner -d vulnscanner

# Health checks
curl http://localhost:8000/health
curl http://localhost:5678/healthz
```

---

## Sin GPU NVIDIA

Comentar la seccion `deploy` del servicio `ollama` en `docker-compose.yml`:

```yaml
  ollama:
    image: ollama/ollama:latest
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]
```

Ollama funcionara con CPU (~30-60s por analisis vs ~5-10s con GPU).

---

## Equipo

Proyecto de Sistemas Inteligentes (2026)
