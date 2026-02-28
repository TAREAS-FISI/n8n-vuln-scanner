# Entregable 1: Definición del Problema

## 1.1 Contexto

Las organizaciones modernas despliegan aplicaciones web de forma continua sin auditorías de seguridad adecuadas. Las herramientas existentes son fragmentadas (cada una detecta solo un tipo de vulnerabilidad), costosas (licencias comerciales como Burp Suite Pro, Acunetix, Nessus) o requieren expertise manual significativo para interpretar los resultados. Esto genera un gap de seguridad donde muchas aplicaciones web quedan expuestas a ataques conocidos y prevenibles.

Según el OWASP Top 10 (2021), vulnerabilidades como inyección SQL, Cross-Site Scripting (XSS), configuraciones incorrectas de seguridad y componentes con vulnerabilidades conocidas siguen siendo explotadas masivamente. La falta de automatización e integración entre herramientas de detección dificulta respuestas rápidas y efectivas.

## 1.2 Problema

**¿Cómo automatizar la detección integral de vulnerabilidades web combinando múltiples fuentes de análisis, un sistema de scoring inteligente y recomendaciones de remediación generadas por IA, todo ejecutable en localhost sin costos?**

Problemas específicos:
1. **Fragmentación de herramientas**: un desarrollador necesita ejecutar ZAP, Nuclei, testssl.sh y análisis manuales por separado
2. **Falta de contextualización**: los reportes brutos de herramientas automatizadas carecen de explicación contextual y priorización
3. **Ausencia de scoring unificado**: no existe una métrica única que combine resultados de múltiples fuentes
4. **Barrera económica**: herramientas comerciales de análisis integral son costosas para equipos pequeños

## 1.3 Solución Propuesta

Un **sistema inteligente de detección de vulnerabilidades web** que:

1. Recibe una URL como entrada
2. Orquesta automáticamente 4 fuentes independientes de detección mediante n8n
3. Combina los hallazgos en un score de seguridad global (0–100) usando un algoritmo de scoring ponderado
4. Genera recomendaciones contextualizadas de remediación usando un LLM local (Ollama con llama3.2:3b)
5. Presenta resultados en un dashboard web interactivo y en paneles históricos de Grafana

## 1.4 Actores del Sistema

| Actor | Descripción | Interacción |
|---|---|---|
| **Usuario** (desarrollador/admin) | Persona que desea evaluar la seguridad de un sitio web | Ingresa URL, consulta reportes, revisa recomendaciones |
| **n8n** (orquestador) | Motor de workflows que coordina el pipeline completo | Dispara las 4 fuentes de detección en secuencia, agrega resultados |
| **FastAPI** (backend) | API que ejecuta 7 checks de seguridad propios y gestiona datos | Procesa cada check, almacena findings, calcula score |
| **OWASP ZAP** | Scanner DAST especializado | Ejecuta spider + active scan para encontrar XSS, SQLi, CSRF |
| **Nuclei** | Scanner de CVEs con 9000+ templates | Detecta vulnerabilidades conocidas y misconfigurations |
| **testssl.sh** | Auditor de SSL/TLS | Analiza protocolos, cifrados, certificados, vulnerabilidades SSL |
| **Ollama (LLM)** | Modelo de lenguaje local | Analiza hallazgos, correlaciona vulnerabilidades, genera remediación |

## 1.5 Entradas del Sistema

| Entrada | Tipo | Ejemplo | Validación |
|---|---|---|---|
| URL del sitio web | `string` (URL válida) | `http://dvwa:8081` | Se valida formato URL; se verifica conectividad |

## 1.6 Salidas del Sistema

| Salida | Tipo | Descripción |
|---|---|---|
| **Reporte de vulnerabilidades** | Lista de findings | Cada finding tiene: fuente, categoría, título, severidad, CVSS, descripción, remediación |
| **Score global de seguridad** | Número 0–100 | Calculado ponderando las 4 fuentes de detección |
| **Análisis LLM** | Texto en español | Explicación contextualizada, correlaciones entre hallazgos, pasos de remediación con código |
| **Dashboard histórico** | Paneles Grafana | Gráficas de tendencia, distribución por severidad, comparativas entre escaneos |

## 1.7 Decisiones Inteligentes del Sistema

El sistema realiza 4 tipos de decisiones inteligentes:

### 1. Clasificación de Severidad (Capa 1 — Reglas Deterministas)
Cada hallazgo se clasifica automáticamente en 5 niveles: Critical, High, Medium, Low, Info. La clasificación se basa en reglas predefinidas alineadas con estándares CVSS v3.1.

### 2. Scoring Ponderado (Capa 2 — Algoritmo de Decisión)
Un algoritmo combina findings de 9 fuentes distintas en un score único 0–100, aplicando pesos diferenciados por fuente y factores de penalización por severidad.

### 3. Análisis Contextual por LLM (Capa 3 — IA Generativa)
Ollama analiza todos los hallazgos para:
- Explicar riesgos en contexto (no genérico)
- Identificar correlaciones entre vulnerabilidades que amplifican el riesgo
- Priorizar remediaciones por impacto/esfuerzo
- Generar código de configuración específico para corregir cada vulnerabilidad

### 4. Detección de Anomalías
El sistema distingue entre configuraciones inusuales (informativas) y vulnerabilidades reales (accionables), evitando falsos positivos.

## 1.8 Justificación como Sistema Inteligente

Este sistema cumple los criterios de un sistema inteligente porque:

1. **Percibe**: recolecta datos de múltiples fuentes heterogéneas (headers HTTP, certificados SSL, puertos TCP, cookies, CORS, archivos expuestos, crawling web, CVEs)
2. **Razona**: aplica reglas deterministas, un algoritmo de scoring ponderado y análisis con LLM para derivar conclusiones
3. **Actúa**: genera reportes accionables con recomendaciones específicas y priorizadas
4. **Aprende** (implícito): el LLM contextualiza hallazgos basándose en su conocimiento previo de ciberseguridad, adaptando sus recomendaciones al conjunto específico de vulnerabilidades detectadas
