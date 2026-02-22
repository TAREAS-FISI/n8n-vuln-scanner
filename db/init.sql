-- ══════════════════════════════════════════════════════════════
-- n8n-vuln-scanner — Schema Inicial de PostgreSQL
-- ══════════════════════════════════════════════════════════════

-- Extensión para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Tabla: scans ────────────────────────────────────────────
-- Registro principal de cada escaneo solicitado
CREATE TABLE scans (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_url      VARCHAR(2048) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- status: pending | running | completed | failed
    global_score    NUMERIC(5,1),
    total_findings  INTEGER DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE,
    error_message   TEXT
);

-- Índices para consultas frecuentes
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_created_at ON scans(created_at DESC);

-- ─── Tabla: scan_phases ──────────────────────────────────────
-- Seguimiento de cada fase del pipeline (para barra de progreso)
CREATE TABLE scan_phases (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id         UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    phase_name      VARCHAR(50) NOT NULL,
    -- phase_name: passive_checks | testssl | nuclei | zap | scoring_llm
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- status: pending | running | completed | failed | skipped
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    findings_count  INTEGER DEFAULT 0,
    error_message   TEXT
);

CREATE INDEX idx_scan_phases_scan_id ON scan_phases(scan_id);

-- ─── Tabla: findings ─────────────────────────────────────────
-- Cada hallazgo/vulnerabilidad detectada
CREATE TABLE findings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id         UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    source          VARCHAR(50) NOT NULL,
    -- source: passive_headers | passive_ssl | passive_ports | passive_cookies |
    --         passive_cors | passive_disclosure | testssl | nuclei | zap
    category        VARCHAR(100) NOT NULL,
    title           VARCHAR(500) NOT NULL,
    severity        VARCHAR(20) NOT NULL DEFAULT 'Info',
    -- severity: Critical | High | Medium | Low | Info
    cvss_score      NUMERIC(3,1) DEFAULT 0.0,
    description     TEXT,
    remediation     TEXT,
    raw_data        JSONB,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_findings_scan_id ON findings(scan_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_source ON findings(source);

-- ─── Tabla: llm_analyses ─────────────────────────────────────
-- Análisis generado por Ollama (LLM local)
CREATE TABLE llm_analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id         UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    raw_prompt      TEXT,
    raw_response    TEXT,
    recommendations_json JSONB,
    model_used      VARCHAR(100),
    duration_ms     INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_llm_analyses_scan_id ON llm_analyses(scan_id);

-- ─── Vistas útiles para Grafana ──────────────────────────────

-- Vista: resumen de findings por severidad
CREATE VIEW v_findings_by_severity AS
SELECT
    s.id AS scan_id,
    s.target_url,
    s.global_score,
    s.created_at,
    f.severity,
    COUNT(*) AS count
FROM scans s
JOIN findings f ON f.scan_id = s.id
GROUP BY s.id, s.target_url, s.global_score, s.created_at, f.severity;

-- Vista: resumen de findings por fuente
CREATE VIEW v_findings_by_source AS
SELECT
    s.id AS scan_id,
    s.target_url,
    s.created_at,
    f.source,
    COUNT(*) AS count
FROM scans s
JOIN findings f ON f.scan_id = s.id
GROUP BY s.id, s.target_url, s.created_at, f.source;

-- Vista: últimos escaneos con estadísticas
CREATE VIEW v_recent_scans AS
SELECT
    s.id,
    s.target_url,
    s.status,
    s.global_score,
    s.total_findings,
    s.created_at,
    s.completed_at,
    EXTRACT(EPOCH FROM (s.completed_at - s.created_at)) AS duration_seconds
FROM scans s
ORDER BY s.created_at DESC
LIMIT 50;

-- Vista: categorías de vulnerabilidad más frecuentes
CREATE VIEW v_top_categories AS
SELECT
    f.category,
    f.severity,
    COUNT(*) AS occurrences
FROM findings f
GROUP BY f.category, f.severity
ORDER BY occurrences DESC
LIMIT 20;
