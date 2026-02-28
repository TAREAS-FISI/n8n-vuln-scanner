# Entregable 7: Métricas de Evaluación

## 7.1 Métricas del Módulo Inteligente

Estas métricas evalúan la calidad y precisión de las decisiones inteligentes del sistema.

### M1: Precisión de Detección de Headers

| Parámetro | Valor |
|---|---|
| **Definición** | % de headers de seguridad correctamente identificados como presentes/ausentes, comparado con referencia |
| **Referencia** | securityheaders.com (herramienta de referencia de la industria) |
| **Método** | Comparar findings de `/check/headers` contra informe de securityheaders.com para 5 sitios |
| **Valor esperado** | > 90% de coincidencia |
| **Justificación** | Valida que la Capa 1 (reglas deterministas) funciona correctamente |

**Sitios de prueba sugeridos:**
1. `https://github.com` — excelente configuración
2. `https://google.com` — buena configuración
3. `http://httpbin.org` — configuración mínima
4. `http://dvwa:80` — sin headers de seguridad
5. `https://expired.badssl.com` — caso especial SSL

### M2: Cobertura de ZAP en DVWA

| Parámetro | Valor |
|---|---|
| **Definición** | % de vulnerabilidades conocidas de DVWA detectadas por OWASP ZAP |
| **Referencia** | Lista oficial de vulnerabilidades DVWA (security=low) |
| **Método** | Ejecutar scan ZAP contra DVWA low y verificar detección |
| **Valor esperado** | ≥ 80% (XSS, SQLi, CSRF, File Inclusion) |
| **Justificación** | Valida integración correcta con ZAP como fuente de detección |

**Vulnerabilidades DVWA a detectar:**

| Vulnerabilidad | ¿ZAP debería detectarla? |
|---|---|
| SQL Injection | ✅ Sí |
| Reflected XSS | ✅ Sí |
| Stored XSS | ✅ Sí |
| CSRF | ✅ Sí |
| Command Injection | ⚠️ Posible |
| File Inclusion | ⚠️ Posible |
| File Upload | ⚠️ Posible |
| Brute Force | ❌ No (requiere diccionario) |

### M3: Cobertura de Nuclei (Findings Únicos)

| Parámetro | Valor |
|---|---|
| **Definición** | Número de findings detectados por Nuclei que ZAP no detectó |
| **Método** | Comparar sets de findings de nuclei vs zap por categoría/título |
| **Valor esperado** | ≥ 5 findings únicos |
| **Justificación** | Demuestra valor de tener múltiples fuentes de detección |

**Tipos de findings que Nuclei detecta y ZAP no:**
- CVEs específicas de software (versiones vulnerables)
- Misconfigurations de servidores web
- Paneles de administración expuestos
- Archivos de configuración expuestos (con templates específicos)
- Vulnerabilidades de tecnologías específicas

### M4: Diferencial de Scoring

| Parámetro | Valor |
|---|---|
| **Definición** | Diferencia de score entre DVWA(impossible) y DVWA(low) |
| **Método** | Ejecutar escaneo completo contra ambos niveles y comparar scores |
| **Valor esperado** | ≥ 40 puntos de diferencia |
| **Justificación** | Valida que la Capa 2 (scoring) discrimina correctamente entre niveles de seguridad |

**Resultados esperados:**

| Target | Score estimado | Total findings |
|---|---|---|
| DVWA security=low | 15–35 | 15–25 |
| DVWA security=impossible | 55–80 | 5–12 |
| **Diferencial** | **≥ 40 puntos** | **~10-15 fewer** |

### M5: Relevancia del LLM

| Parámetro | Valor |
|---|---|
| **Definición** | Calidad de las recomendaciones generadas por Ollama (llama3.2:3b) |
| **Método** | Evaluación manual por 3 miembros del equipo en escala 1-5 |
| **Valor esperado** | Promedio ≥ 3.5/5.0 |
| **Justificación** | Valida que la Capa 3 (LLM) agrega valor real sobre las reglas |

**Criterios de evaluación (1-5):**

| Criterio | Peso | Descripción |
|---|---|---|
| **Precisión** | 25% | ¿Las recomendaciones son técnicamente correctas? |
| **Relevancia** | 25% | ¿Las recomendaciones aplican al contexto específico del scan? |
| **Accionabilidad** | 25% | ¿Los pasos de remediación son claros y ejecutables? |
| **Correlaciones** | 15% | ¿Identifica combinaciones peligrosas entre hallazgos? |
| **Idioma** | 10% | ¿Responde en español correcto y comprensible? |

### M6: Latencia del LLM

| Parámetro | Valor |
|---|---|
| **Definición** | Tiempo de respuesta de Ollama por análisis |
| **Método** | Medir `duration_ms` en tabla `llm_analyses` |
| **Valor esperado** | < 30 segundos (GPU) / < 60 segundos (CPU) |
| **Justificación** | Uso práctico requiere tiempos de respuesta razonables |

### M7: Correlaciones Detectadas por LLM

| Parámetro | Valor |
|---|---|
| **Definición** | Número de correlaciones válidas entre hallazgos identificadas por el LLM |
| **Método** | Revisión manual de la respuesta del LLM buscando correlaciones |
| **Valor esperado** | ≥ 1 correlación válida por scan (en targets vulnerables) |
| **Justificación** | Esta capacidad diferencia al LLM de un simple listado de reglas |

**Ejemplos de correlaciones válidas:**
- "Sin HTTPS + cookies sin Secure = sesiones pueden interceptarse"
- "CORS wildcard + cookies sin SameSite = posible CSRF cross-origin"
- "Server version expuesta + CVE conocida = ruta de explotación directa"
- "Sin CSP + XSS detectado por ZAP = XSS fácilmente explotable"

---

## 7.2 Métricas Operativas

Estas métricas evalúan el rendimiento y confiabilidad del sistema como un todo.

### O1: Tiempo Total End-to-End

| Parámetro | Valor |
|---|---|
| **Definición** | Tiempo desde que el usuario envía la URL hasta que recibe el reporte completo |
| **Método** | `completed_at - created_at` en tabla `scans` |
| **Valor esperado** | < 10 minutos (sitio pequeño como DVWA) |
| **Fórmula** | T_total = T_passive + T_testssl + T_nuclei + T_zap + T_scoring_llm |

**Desglose estimado por fase:**

| Fase | Tiempo estimado | % del total |
|---|---|---|
| Fase 1: Checks pasivos | 5–15 s | ~2% |
| Fase 2: testssl.sh | 30–60 s | ~10% |
| Fase 3: Nuclei | 60–180 s | ~25% |
| Fase 4: OWASP ZAP | 180–480 s | ~55% |
| Fase 5: Scoring + LLM | 10–30 s | ~5% |
| **TOTAL** | **~5-12 min** | **100%** |

### O2: Tiempo Fase 1 (Checks Pasivos)

| Parámetro | Valor |
|---|---|
| **Definición** | Duración de los 7 checks pasivos ejecutados en paralelo |
| **Método** | `completed_at - started_at` de la fase `passive_checks` en `scan_phases` |
| **Valor esperado** | < 15 segundos |
| **Justificación** | Los checks pasivos son HTTP requests simples, deben ser rápidos |

### O3: Tiempo Fase 4 (ZAP)

| Parámetro | Valor |
|---|---|
| **Definición** | Duración del spider + active scan de OWASP ZAP |
| **Método** | `completed_at - started_at` de la fase `zap` en `scan_phases` |
| **Valor esperado** | < 8 minutos (sitio pequeño) |
| **Nota** | ZAP es la fase más lenta por el spider + active scanning completo |

### O4: Throughput

| Parámetro | Valor |
|---|---|
| **Definición** | Cantidad de escaneos exitosos completados por hora |
| **Método** | Contar scans con status=`completed` en una ventana de 1 hora |
| **Valor esperado** | ≥ 3 escaneos/hora |
| **Limitante** | ZAP procesa un scan a la vez (secuencial) |

### O5: Tasa de Error n8n

| Parámetro | Valor |
|---|---|
| **Definición** | Porcentaje de ejecuciones de workflow que fallan |
| **Método** | (workflows fallidos / total ejecutados) × 100 |
| **Valor esperado** | < 5% |
| **Fuentes de error comunes** | Timeout de herramientas, servicios no disponibles, URLs inaccesibles |

### O6: Disponibilidad

| Parámetro | Valor |
|---|---|
| **Definición** | Porcentaje de tiempo que cada contenedor Docker está UP en 24 horas |
| **Método** | `docker compose ps` periódicamente + `docker events` |
| **Valor esperado** | > 99% para servicios persistentes |

### O7: TTFB Frontend

| Parámetro | Valor |
|---|---|
| **Definición** | Time to First Byte de Next.js |
| **Método** | Chrome DevTools → Network → primer request |
| **Valor esperado** | < 500 ms |

---

## 7.3 Tabla Resumen de Métricas

| # | Tipo | Métrica | Método | Valor Esperado |
|---|---|---|---|---|
| M1 | Inteligente | Precisión headers | vs securityheaders.com | > 90% |
| M2 | Inteligente | Cobertura ZAP/DVWA | vs lista DVWA | ≥ 80% |
| M3 | Inteligente | Findings únicos Nuclei | Comparar vs ZAP | ≥ 5 |
| M4 | Inteligente | Diferencial scoring | DVWA impossible vs low | ≥ 40 pts |
| M5 | Inteligente | Relevancia LLM | Evaluación manual 1-5 | ≥ 3.5/5.0 |
| M6 | Inteligente | Latencia LLM | duration_ms en BD | < 30s (GPU) |
| M7 | Inteligente | Correlaciones LLM | Revisión manual | ≥ 1/scan |
| O1 | Operativa | Tiempo end-to-end | BD timestamps | < 10 min |
| O2 | Operativa | Tiempo Fase 1 | BD timestamps | < 15s |
| O3 | Operativa | Tiempo Fase 4 (ZAP) | BD timestamps | < 8 min |
| O4 | Operativa | Throughput | Conteo por hora | ≥ 3/hora |
| O5 | Operativa | Tasa error n8n | Logs n8n | < 5% |
| O6 | Operativa | Disponibilidad | Docker events | > 99% |
| O7 | Operativa | TTFB frontend | DevTools | < 500ms |

---

## 7.4 Cómo Medir las Métricas

### Desde PostgreSQL

```sql
-- M4: Diferencial de scoring
SELECT target_url, global_score FROM scans 
WHERE status = 'completed' 
ORDER BY created_at DESC LIMIT 10;

-- M6: Latencia LLM
SELECT scan_id, duration_ms, model_used FROM llm_analyses;

-- O1: Tiempo end-to-end
SELECT id, target_url, 
       EXTRACT(EPOCH FROM (completed_at - created_at)) AS seconds
FROM scans WHERE status = 'completed';

-- O2/O3: Tiempo por fase
SELECT scan_id, phase_name, 
       EXTRACT(EPOCH FROM (completed_at - started_at)) AS seconds
FROM scan_phases WHERE status = 'completed';

-- O4: Throughput
SELECT COUNT(*) AS scans_completados, 
       DATE_TRUNC('hour', completed_at) AS hora
FROM scans WHERE status = 'completed'
GROUP BY DATE_TRUNC('hour', completed_at);
```

### Desde n8n

```
# O5: Tasa de error
En n8n UI → Executions → filtrar por "Error" → contar vs total
```

### Desde el navegador

```
# O7: TTFB
Chrome DevTools → Network → Reload → 
Primer request → Timing → Waiting for server response
```
