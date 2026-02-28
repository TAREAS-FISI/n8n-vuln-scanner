# Informe Final — Scanner de Vulnerabilidades Web Inteligente

> **Curso:** Sistemas Inteligentes  
> **Proyecto:** Scanner de Vulnerabilidades Web con n8n + FastAPI + OWASP ZAP + Nuclei + testssl.sh + Ollama  
> **Fecha:** Febrero 2026  
> **Stack:** Docker Compose (10 servicios), 100% localhost, $0 de gasto

---

## Tabla de Contenidos

1. [Definición del Problema](#1-definición-del-problema)
2. [Diseño Conceptual](#2-diseño-conceptual)
3. [Módulo Inteligente](#3-módulo-inteligente)
4. [Arquitectura Técnica](#4-arquitectura-técnica)
5. [Implementación](#5-implementación)
6. [Datos y Pruebas](#6-datos-y-pruebas)
7. [Métricas de Evaluación](#7-métricas-de-evaluación)
8. [Defensa Técnica](#8-defensa-técnica)

---

# 1. Definición del Problema

## 1.1 Contexto

Las organizaciones modernas despliegan aplicaciones web sin auditorías de seguridad adecuadas. Las herramientas existentes son fragmentadas, costosas o requieren expertise manual significativo. Según el OWASP Top 10 (2021), vulnerabilidades como inyección SQL, XSS, configuraciones incorrectas y componentes vulnerables siguen siendo explotadas masivamente.

## 1.2 Problema

**¿Cómo automatizar la detección integral de vulnerabilidades web combinando múltiples fuentes de análisis, un sistema de scoring inteligente y recomendaciones de remediación generadas por IA, todo ejecutable en localhost sin costos?**

## 1.3 Solución

Un sistema inteligente que:
1. Recibe una URL como entrada
2. Orquesta 4 fuentes independientes de detección mediante n8n
3. Combina hallazgos en un score global 0–100 con algoritmo ponderado
4. Genera recomendaciones contextualizadas usando Ollama (LLM local)
5. Presenta resultados en dashboard web interactivo y paneles Grafana

## 1.4 Actores

| Actor | Interacción |
|---|---|
| **Usuario** (desarrollador/admin) | Ingresa URL, consulta reportes |
| **n8n** (orquestador) | Coordina el pipeline de 5 fases |
| **FastAPI** (backend) | 7 checks de seguridad + scoring + CRUD |
| **OWASP ZAP** | Scanner DAST (XSS, SQLi, CSRF) |
| **Nuclei** | Scanner de 9000+ CVEs |
| **testssl.sh** | Auditoría SSL/TLS profunda |
| **Ollama (LLM)** | Análisis contextual + recomendaciones |

## 1.5 Entradas y Salidas

**Entrada:** URL del sitio web a analizar

**Salidas:**
- Reporte de vulnerabilidades con severidad y CVSS
- Score global de seguridad (0–100)
- Análisis LLM con recomendaciones en español
- Dashboard histórico en Grafana

## 1.6 Decisiones Inteligentes

1. **Clasificación de severidad** — reglas deterministas con CVSS
2. **Scoring ponderado** — algoritmo multi-criterio de 4 fuentes
3. **Análisis contextual LLM** — correlaciones, priorización, código de remediación
4. **Detección de anomalías** — distinguir configuraciones inusuales de vulnerabilidades reales

---

# 2. Diseño Conceptual

## 2.1 Pipeline del Sistema

```
Usuario → Next.js → FastAPI → n8n (webhook)
                                  │
          ┌───────────────────────┼───────────────────────┐
          │ FASE 1 (paralelo)     │ FASE 2-4 (secuencial) │
          │ 7 Checks pasivos:     │ testssl.sh (SSL)       │
          │ headers, ssl, ports,  │ Nuclei (CVEs)          │
          │ cookies, cors,        │ OWASP ZAP (DAST)       │
          │ disclosure, tech      │                         │
          └───────────────────────┼───────────────────────┘
                                  │
                           FASE 5: Scoring + Ollama LLM
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼              ▼
                 Next.js      PostgreSQL      Grafana
                 (reporte)    (persistencia)  (dashboard)
```

## 2.2 Flujo de Datos

1. **POST /scan** — Frontend envía URL al backend
2. **INSERT** — Backend crea registro en PostgreSQL (status: pending)
3. **Webhook** — Backend dispara n8n con {url, scan_id}
4. **5 Fases** — n8n ejecuta las fuentes de detección secuencialmente
5. **PUT /findings** — n8n envía findings al backend después de cada fase
6. **POST /score** — n8n solicita cálculo del score global
7. **POST /api/chat** — n8n envía findings a Ollama para análisis
8. **PUT /complete** — n8n marca el scan como completado
9. **Polling** — Frontend consulta GET /scan/{id} cada 3s hasta completion

## 2.3 Eventos del Sistema

| Evento | Acción |
|---|---|
| Scan solicitado | Crear registro + disparar webhook |
| Fase iniciada | PUT phase status: running |
| Findings recibidos | INSERT findings en BD |
| Score calculado | UPDATE global_score en scan |
| Scan completado | UPDATE status: completed |

---

# 3. Módulo Inteligente

## 3.1 Capa 1: Reglas Deterministas

Sistema basado en reglas if-then con severidad y CVSS predefinidos.

### 7 módulos de checks:

| Módulo | # Reglas | Severidad máxima | Ejemplo |
|---|---|---|---|
| Header Checker | 12 | High (7.4) | HSTS ausente |
| SSL Checker | 6 | High (7.5) | Certificado expirado |
| Port Scanner | 21 | High (8.1) | Redis abierto |
| Cookie Checker | 3/cookie | Medium (4.3) | Sin HttpOnly |
| CORS Checker | 4 | Critical (9.1) | Wildcard + credentials |
| Info Disclosure | 11 | Critical (9.8) | .env accesible |
| Tech Detector | 15+ | Info (0.0) | PHP, Apache detectado |

### Reglas clave:

```
SI /.env ACCESIBLE (200) Y body CONTIENE "="  → Critical (CVSS 9.8)
SI CORS: Allow-Origin=* + Credentials=true     → Critical (CVSS 9.1)
SI header HSTS AUSENTE (en HTTPS)              → High (CVSS 7.4)
SI Redis (6379) ABIERTO                        → High (CVSS 8.1)
SI certificado SSL EXPIRADO                    → High (CVSS 7.5)
SI cookie SIN HttpOnly                         → Medium (CVSS 4.3)
SI X-Content-Type-Options AUSENTE              → Low (CVSS 3.7)
```

## 3.2 Capa 2: Scoring Ponderado

Algoritmo: `Score = 100 - Σ(factor_severidad × peso_fuente)`

**Factores de severidad:**

| Severidad | Factor |
|---|---|
| Critical | 25 |
| High | 15 |
| Medium | 8 |
| Low | 3 |
| Info | 0 |

**Pesos por fuente:**

| Fuente | Peso | Justificación |
|---|---|---|
| OWASP ZAP | 0.20 | Detecta vulns explotables (XSS, SQLi) |
| Headers | 0.15 | Configuración de seguridad fundamental |
| testssl.sh | 0.15 | SSL/TLS es crítico para confidencialidad |
| Nuclei | 0.15 | CVEs conocidas con exploit público |
| SSL básico | 0.10 | Verificación de certificado |
| Puertos | 0.10 | Superficie de ataque |
| Cookies | 0.05 | Seguridad de sesión |
| CORS | 0.05 | Cross-origin security |
| Info Disclosure | 0.05 | Exposición de datos sensibles |

**Interpretación del score:**

| Rango | Color | Significado |
|---|---|---|
| 80–100 | Verde | Bueno — pocas vulnerabilidades |
| 50–79 | Amarillo | Regular — requiere atención |
| 30–49 | Naranja | Bajo — problemas significativos |
| 0–29 | Rojo | Crítico — acción urgente |

## 3.3 Capa 3: Análisis Contextual con LLM

**Modelo:** Ollama + llama3.2:3b (local, 0 costo)  
**Temperatura:** 0.3 (baja creatividad → más precisión)  
**Tokens:** 2048 máx (~500 palabras)

**Capacidades:**
1. Análisis de riesgo contextualizado (no genérico)
2. Correlación entre hallazgos (combinaciones peligrosas)
3. Priorización por impacto/esfuerzo
4. Código de remediación (Apache, Nginx, etc.)

**Ejemplo de correlación detectada:**
> "La combinación de CORS wildcard + cookies sin SameSite permite ataques CSRF cross-origin que podrían robar sesiones de usuario"

**Graceful degradation:** Si Ollama no está disponible, el reporte se genera sin análisis LLM.

---

# 4. Arquitectura Técnica

## 4.1 Servicios Docker (10)

| # | Servicio | Imagen | Puerto | Rol |
|---|---|---|---|---|
| 1 | Frontend | Next.js 15 (build local) | 3000 | UI web |
| 2 | Backend | FastAPI Python 3.12 (build local) | 8000 | API + checks + scoring |
| 3 | n8n | n8nio/n8n:latest | 5678 | Orquestador |
| 4 | PostgreSQL | postgres:16-alpine | 5432 | Base de datos |
| 5 | OWASP ZAP | zaproxy/zaproxy:stable | 8080 | Scanner DAST |
| 6 | Ollama | ollama/ollama:latest | 11434 | LLM local |
| 7 | Grafana | grafana/grafana-oss:latest | 3001 | Dashboards |
| 8 | DVWA | vulnerables/web-dvwa | 8081 | Target de prueba |
| 9 | Nuclei | projectdiscovery/nuclei:latest | — | Scanner CVE (CLI) |
| 10 | testssl | drwetter/testssl.sh:latest | — | Auditor SSL (CLI) |

## 4.2 Modelo de Datos

```
scans (1) ──► (N) scan_phases     5 fases por scan
scans (1) ──► (N) findings        N hallazgos por scan
scans (1) ──► (N) llm_analyses    1+ análisis LLM por scan
```

**4 tablas + 4 vistas de Grafana + 7 índices**

## 4.3 Decisiones Técnicas

| Decisión | Elegimos | Razón |
|---|---|---|
| Scanner DAST | OWASP ZAP | API REST completa, comunidad activa |
| Scanner CVEs | Nuclei | 9000+ templates, JSON output |
| SSL profundo | testssl.sh | Cubre Heartbleed, POODLE, BEAST |
| LLM | Ollama + llama3.2:3b | 100% localhost, sin costos |
| Frontend | Next.js + Tailwind | Equipo domina React |
| BD | PostgreSQL | Grafana lo consulta directo, n8n lo soporta |
| Scoring | CVSS simplificado + pesos | Más comprensible, igualmente válido |

---

# 5. Implementación

## 5.1 Repositorio

**URL:** `https://github.com/TAREAS-FISI/n8n-vuln-scanner`

**Estructura:**
- `frontend/` — Next.js 15 + Tailwind CSS + TypeScript (7 componentes)
- `backend/` — FastAPI + Python 3.12 (7 services + 3 routers + 14 schemas)
- `n8n-workflows/` — 6 workflows JSON exportados
- `grafana/` — Provisioning + dashboard con 8 paneles
- `db/` — Schema SQL (4 tablas + 4 vistas)
- `datasets/` — 3 datasets de prueba + escenarios
- `docs/` — 8 entregables + informe final

## 5.2 Despliegue

```bash
git clone https://github.com/TAREAS-FISI/n8n-vuln-scanner
cd n8n-vuln-scanner
docker compose up -d                              # 10 servicios
docker exec ollama ollama pull llama3.2:3b        # Modelo LLM
# Configurar DVWA en http://localhost:8081/setup.php
```

**Requisitos:** Docker Desktop v24+, 8 GB RAM mínimo, 20 GB disco.

---

# 6. Datos y Pruebas

## 6.1 Escenarios Ejecutados

| # | Escenario | URL | Score | Findings | Resultado |
|---|---|---|---|---|---|
| 1 | Vulnerable | `http://dvwa:80` | 22.5 | 18 | 🔴 Múltiples vulns detectadas |
| 2 | Seguro | `https://github.com` | 88.5 | 5 | 🟢 Pocas deficiencias menores |
| 3 | Error | `https://noexiste.invalid` | 100.0 | 7 (Info) | ⚪ Error graceful |

## 6.2 Análisis Comparativo

**Diferencial vulnerable vs seguro: 66 puntos** (supera el mínimo de 40).

| Severidad | Vulnerable | Seguro | Error |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| High | 5 | 0 | 0 |
| Medium | 7 | 0 | 0 |
| Low | 4 | 2 | 0 |
| Info | 2 | 3 | 7 |

## 6.3 Validación

- **Sin falsos positivos graves** en target seguro (solo Low/Info)
- **Manejo robusto de errores** para URLs inexistentes (no crash)
- **Detección completa** en DVWA: headers, SSL, cookies, ports, ZAP findings

---

# 7. Métricas de Evaluación

## 7.1 Métricas del Módulo Inteligente

| # | Métrica | Valor Esperado | Método |
|---|---|---|---|
| M1 | Precisión headers | > 90% | vs securityheaders.com |
| M2 | Cobertura ZAP/DVWA | ≥ 80% | vs lista DVWA |
| M3 | Findings únicos Nuclei | ≥ 5 | vs findings ZAP |
| M4 | Diferencial scoring | ≥ 40 pts | DVWA impossible vs low |
| M5 | Relevancia LLM | ≥ 3.5/5.0 | Evaluación manual |
| M6 | Latencia LLM | < 30s (GPU) | BD duration_ms |
| M7 | Correlaciones LLM | ≥ 1/scan | Revisión manual |

## 7.2 Métricas Operativas

| # | Métrica | Valor Esperado | Método |
|---|---|---|---|
| O1 | Tiempo end-to-end | < 10 min | BD timestamps |
| O2 | Tiempo Fase 1 | < 15s | BD timestamps |
| O3 | Tiempo Fase 4 (ZAP) | < 8 min | BD timestamps |
| O4 | Throughput | ≥ 3/hora | Conteo |
| O5 | Tasa error n8n | < 5% | Logs n8n |
| O6 | Disponibilidad | > 99% | Docker events |
| O7 | TTFB frontend | < 500ms | DevTools |

## 7.3 Medición desde PostgreSQL

```sql
-- Diferencial de scoring
SELECT target_url, global_score FROM scans WHERE status = 'completed';

-- Latencia LLM
SELECT duration_ms, model_used FROM llm_analyses;

-- Tiempo por fase
SELECT phase_name, EXTRACT(EPOCH FROM (completed_at - started_at)) AS seconds
FROM scan_phases WHERE status = 'completed';
```

---

# 8. Defensa Técnica

## 8.1 Estructura de la Presentación (25–35 min)

| # | Tema | Responsable | Duración |
|---|---|---|---|
| 1 | Introducción + Problema | E | 5 min |
| 2 | Diseño Conceptual | C | 5 min |
| 3 | Módulo Inteligente | B | 7 min |
| 4 | Arquitectura + Demo | D | 8 min |
| 5 | Resultados + Métricas | A | 5 min |

## 8.2 Demo en Vivo

1. Mostrar `docker compose ps` → 10 servicios corriendo
2. Abrir http://localhost:3000 → escanear `http://dvwa:80`
3. Mostrar progreso en tiempo real (5 fases)
4. Mostrar reporte: score gauge + findings + LLM analysis
5. Mostrar Grafana: dashboard con métricas históricas

## 8.3 Modificaciones en Vivo

El equipo está preparado para:
- **Cambiar umbrales de scoring** → editar `scorer.py`
- **Agregar headers al checker** → editar `header_checker.py`
- **Modificar prompt de Ollama** → editar en n8n UI
- **Agregar puertos al scanner** → editar `port_scanner.py`

Cada cambio requiere solo un `docker compose restart backend`.

## 8.4 Conclusiones

El sistema demuestra que es posible construir una plataforma de análisis de seguridad web completa usando exclusivamente herramientas open source en localhost. La combinación de 4 fuentes de detección, un algoritmo de scoring ponderado y análisis por IA local produce reportes accionables que superan lo que cualquier herramienta individual ofrece.

**Contribución clave:** La integración inteligente de múltiples fuentes heterogéneas mediante n8n como orquestador, con un módulo de 3 capas de decisión que escala desde reglas deterministas hasta IA generativa.

---

> **Nota:** Los documentos detallados de cada entregable se encuentran en la carpeta `docs/` del repositorio:
> - [01-definicion-problema.md](01-definicion-problema.md)
> - [02-diseno-conceptual.md](02-diseno-conceptual.md)
> - [03-modulo-inteligente.md](03-modulo-inteligente.md)
> - [04-arquitectura-tecnica.md](04-arquitectura-tecnica.md)
> - [05-implementacion.md](05-implementacion.md)
> - [06-datos-pruebas.md](06-datos-pruebas.md)
> - [07-metricas-evaluacion.md](07-metricas-evaluacion.md)
> - [08-defensa-tecnica.md](08-defensa-tecnica.md)
