# Entregable 2: Diseño Conceptual — Diagrama de Flujo

## 2.1 Flujo Lógico del Sistema

El siguiente diagrama de flujo describe el recorrido completo de un escaneo desde que el usuario ingresa una URL hasta que recibe el reporte final.

```
┌───────────────────────────────────────────────────────────────────────┐
│                        FLUJO DEL SISTEMA                              │
└───────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │ USUARIO │
    └────┬────┘
         │ Ingresa URL en formulario web
         ▼
    ┌─────────────┐
    │  NEXT.JS    │  Valida formato URL
    │  Frontend   │  POST /scan { target_url }
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐     Crea registro en PostgreSQL
    │  FASTAPI    │──── status: "pending"
    │  Backend    │     Genera scan_id (UUID)
    └──────┬──────┘
           │ Dispara webhook POST /webhook/scan
           │ { url, scan_id }
           ▼
    ┌─────────────┐
    │    N8N      │  Recibe webhook
    │ Orquestador │  Inicia pipeline de 5 fases
    └──────┬──────┘
           │
    ═══════╪═══════════════════════════════════════════
    FASE 1 │  CHECKS PASIVOS (paralelo, ~10s)
    ═══════╪═══════════════════════════════════════════
           │
           ├──► FastAPI /check/headers ──────► 0-12 findings
           ├──► FastAPI /check/ssl ──────────► 0-5 findings
           ├──► FastAPI /check/ports ────────► 0-21 findings
           ├──► FastAPI /check/cookies ──────► 0-10 findings
           ├──► FastAPI /check/cors ─────────► 0-3 findings
           ├──► FastAPI /check/disclosure ───► 0-10 findings
           └──► FastAPI /check/tech ─────────► 1 finding (info)
           │
           ▼ [Merge + PUT /scan/{id}/findings]
           │
    ═══════╪═══════════════════════════════════════════
    FASE 2 │  TESTSSL.SH — Auditoría SSL/TLS (~30-60s)
    ═══════╪═══════════════════════════════════════════
           │
           ▼
    ┌──────────────┐
    │ testssl.sh   │  Execute Command (Docker)
    │ Protocolo,   │  --jsonfile output
    │ Cipher,      │  Parsear JSON
    │ BEAST, etc.  │  Transformar al formato estándar
    └──────┬───────┘
           │
           ▼ [PUT /scan/{id}/findings]
           │
    ═══════╪═══════════════════════════════════════════
    FASE 3 │  NUCLEI — Scanner CVEs (~1-3min)
    ═══════╪═══════════════════════════════════════════
           │
           ▼
    ┌──────────────┐
    │   Nuclei     │  Execute Command (Docker)
    │  9000+ CVE   │  -j -o output.jsonl
    │  templates   │  Parsear JSONL
    │              │  Transformar al formato estándar
    └──────┬───────┘
           │
           ▼ [PUT /scan/{id}/findings]
           │
    ═══════╪═══════════════════════════════════════════
    FASE 4 │  OWASP ZAP — DAST Spider + Active Scan (~3-8min)
    ═══════╪═══════════════════════════════════════════
           │
           ▼
    ┌──────────────┐     ┌──────────────┐
    │  ZAP Spider  │────►│ ZAP Active   │
    │  Crawl web   │     │ Scan (DAST)  │
    │  Polling 5s  │     │ Polling 10s  │
    └──────────────┘     └──────┬───────┘
                                │
                                ▼ Fetch Alerts
                                │ Transformar al formato estándar
                                │
           ▼ [PUT /scan/{id}/findings]
           │
    ═══════╪═══════════════════════════════════════════
    FASE 5 │  SCORING + ANÁLISIS LLM (~10-30s)
    ═══════╪═══════════════════════════════════════════
           │
           ├──► FastAPI POST /score
           │    Lee TODOS los findings de BD
           │    Aplica algoritmo de scoring ponderado
           │    Score = 100 - Σ(factor_severidad × peso_fuente)
           │    Guarda global_score en BD
           │
           └──► Ollama POST /api/chat
                Prompt con hallazgos + score
                Modelo: llama3.2:3b
                Genera: análisis contextual + correlaciones
                        + remediaciones en español
                │
                ▼ [PUT /scan/{id}/llm-analysis]
                │
                ▼ [PUT /scan/{id}/complete]
                │
    ════════════╪══════════════════════════════════════
                │
                ▼
    ┌─────────────┐     ┌─────────────┐
    │  NEXT.JS    │     │  GRAFANA    │
    │  Reporte    │     │  Dashboard  │
    │  Score +    │     │  Histórico  │
    │  Findings + │     │  Tendencias │
    │  LLM Análs. │     │             │
    └─────────────┘     └─────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ USUARIO │          │ USUARIO │
    └─────────┘          └─────────┘
```

## 2.2 Diagrama de Flujo — Mermaid

```mermaid
flowchart TD
    A([Usuario ingresa URL]) --> B[Next.js valida URL]
    B --> C[FastAPI: POST /scan]
    C --> D[(PostgreSQL: crear registro scan)]
    C --> E[Webhook → n8n]

    E --> F1{FASE 1: Checks Pasivos}
    F1 --> |paralelo| G1[/check/headers]
    F1 --> |paralelo| G2[/check/ssl]
    F1 --> |paralelo| G3[/check/ports]
    F1 --> |paralelo| G4[/check/cookies]
    F1 --> |paralelo| G5[/check/cors]
    F1 --> |paralelo| G6[/check/disclosure]
    F1 --> |paralelo| G7[/check/tech]

    G1 & G2 & G3 & G4 & G5 & G6 & G7 --> H1[Merge findings Fase 1]
    H1 --> I1[PUT /scan/id/findings]

    I1 --> F2{FASE 2: testssl.sh}
    F2 --> J2[Execute Command: testssl.sh]
    J2 --> K2[Parsear JSON → findings]
    K2 --> I2[PUT /scan/id/findings]

    I2 --> F3{FASE 3: Nuclei}
    F3 --> J3[Execute Command: nuclei]
    J3 --> K3[Parsear JSONL → findings]
    K3 --> I3[PUT /scan/id/findings]

    I3 --> F4{FASE 4: OWASP ZAP}
    F4 --> J4a[Spider: crawl sitio]
    J4a --> J4b[Active Scan: DAST]
    J4b --> K4[Fetch Alerts → findings]
    K4 --> I4[PUT /scan/id/findings]

    I4 --> F5{FASE 5: Scoring + LLM}
    F5 --> L1[FastAPI: calcular score]
    F5 --> L2[Ollama: análisis contextual]
    L1 --> M[PUT /scan/id/complete]
    L2 --> M

    M --> N1[Next.js: mostrar reporte]
    M --> N2[Grafana: actualizar dashboard]

    style F1 fill:#4a90d9,color:white
    style F2 fill:#50b356,color:white
    style F3 fill:#e6a23c,color:white
    style F4 fill:#f56c6c,color:white
    style F5 fill:#9b59b6,color:white
```

## 2.3 Eventos del Sistema

| Evento | Trigger | Acción |
|---|---|---|
| **Scan solicitado** | POST /scan desde frontend | Crear registro en BD + disparar webhook n8n |
| **Fase iniciada** | n8n comienza una fase | PUT /scan/{id}/phase → status: "running" |
| **Fase completada** | n8n termina una fase | PUT /scan/{id}/phase → status: "completed" |
| **Findings recibidos** | n8n envía resultados | PUT /scan/{id}/findings → insertar en BD |
| **Score calculado** | POST /score | Leer findings, ejecutar algoritmo, guardar score |
| **LLM analiza** | POST /api/chat a Ollama | Generar análisis contextual en español |
| **Scan completado** | PUT /scan/{id}/complete | Marcar como "completed" con timestamp |
| **Frontend polling** | Cada 3 segundos | GET /scan/{id} → actualizar UI con progreso |

## 2.4 Reglas de Negocio

1. **Cada escaneo tiene exactamente 5 fases** que se ejecutan en orden secuencial
2. **Los checks de Fase 1 se ejecutan en paralelo** para optimizar tiempo
3. **El score siempre está entre 0 y 100** (se clampea si excede)
4. **Si una fase falla**, se marca como "failed" y el pipeline continúa con las siguientes
5. **Si Ollama no está disponible**, el reporte se genera sin análisis LLM (graceful degradation)
6. **Los findings se deduplicarán** si tienen el mismo título y fuente
7. **El frontend muestra progreso incremental** — el usuario ve resultados parciales mientras el scan continúa

## 2.5 Componentes y Responsabilidades

| Componente | Responsabilidad | Persistencia |
|---|---|---|
| **Next.js** | UI, formulario, visualización de reportes | No (stateless) |
| **FastAPI** | 7 checks de seguridad, scoring, CRUD de scans | Sí (via PostgreSQL) |
| **n8n** | Orquestación del pipeline, integración de herramientas | Sí (workflows) |
| **PostgreSQL** | Almacenamiento de scans, findings, análisis LLM | Sí (volumen Docker) |
| **OWASP ZAP** | Scanner DAST (XSS, SQLi, CSRF, etc.) | Sí (daemon persistente) |
| **Nuclei** | Scanner de CVEs conocidas (9000+ templates) | No (one-shot) |
| **testssl.sh** | Auditoría SSL/TLS profunda | No (one-shot) |
| **Ollama** | Análisis inteligente con LLM local | Sí (modelo persistente) |
| **Grafana** | Dashboard de métricas históricas | Sí (provisioned) |
| **DVWA** | Target de prueba deliberadamente vulnerable | Sí |
