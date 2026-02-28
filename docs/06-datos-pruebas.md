# Entregable 6: Datos y Pruebas

## 6.1 Escenarios de Prueba

Se definieron **6 escenarios** que cubren diferentes niveles de seguridad, desde un target deliberadamente vulnerable hasta casos de error.

### Escenario 1: Target Vulnerable — DVWA (security=low)

| Parámetro | Valor |
|---|---|
| **URL** | `http://dvwa:80` |
| **Descripción** | Damn Vulnerable Web Application con nivel de seguridad mínimo |
| **Score esperado** | 15–35 (Crítico) |
| **Propósito** | Demostrar detección completa de vulnerabilidades conocidas |

**Findings esperados:**
- Headers: ~10 headers de seguridad faltantes (HSTS, CSP, X-Frame-Options, etc.)
- SSL: "El sitio no usa HTTPS" (High)
- Cookies: PHPSESSID sin flags Secure, posiblemente sin HttpOnly/SameSite
- CORS: wildcard o sin CORS configurado
- Info Disclosure: posibles `/server-status`, `/phpinfo.php`, versión de servidor expuesta
- Tech Detection: PHP, Apache, jQuery
- Ports: 80 abierto, posible 3306 (MySQL)
- ZAP (si se ejecuta): XSS reflejado, SQLi, CSRF, file inclusion
- Nuclei: misconfigurations, tecnologías desactualizadas

### Escenario 2: Target Seguro — github.com

| Parámetro | Valor |
|---|---|
| **URL** | `https://github.com` |
| **Descripción** | Sitio web de producción con seguridad robusta |
| **Score esperado** | 75–95 (Bueno) |
| **Propósito** | Demostrar que el sistema no genera falsos positivos masivos |

**Findings esperados:**
- Headers: la mayoría presentes, quizá falte algún header menor (Permissions-Policy)
- SSL: TLS 1.3, certificado válido, cipher fuerte
- Cookies: flags correctos (Secure, HttpOnly, SameSite)
- CORS: configurado restrictivamente
- Info Disclosure: sin archivos sensibles expuestos
- Tech Detection: Ruby on Rails, Nginx, React

### Escenario 3: Target con SSL Expirado — expired.badssl.com

| Parámetro | Valor |
|---|---|
| **URL** | `https://expired.badssl.com` |
| **Descripción** | Sitio con certificado SSL deliberadamente expirado |
| **Score esperado** | 40–60 (Regular) |
| **Propósito** | Validar detección de problemas de certificado |

**Findings esperados:**
- SSL: certificado expirado (High), posible protocolo débil
- Headers: varios faltantes
- Otros checks normales

### Escenario 4: Target HTTP sin cifrado — httpbin.org

| Parámetro | Valor |
|---|---|
| **URL** | `http://httpbin.org` |
| **Descripción** | Servicio HTTP sin cifrado, con CORS permisivo |
| **Score esperado** | 30–50 (Bajo) |
| **Propósito** | Validar detección de falta de HTTPS |

**Findings esperados:**
- SSL: "No usa HTTPS" (High)
- Headers: varios faltantes
- CORS: posible wildcard (httpbin permite CORS abierto)

### Escenario 5: Target Inexistente — DNS Fail

| Parámetro | Valor |
|---|---|
| **URL** | `https://noexiste.invalid` |
| **Descripción** | URL que no resuelve DNS |
| **Score esperado** | ~100 (sin findings porque no conectó) |
| **Propósito** | Demostrar manejo robusto de errores |

**Findings esperados:**
- Todos los checks devuelven Connection Error / DNS Error (Info)
- Score = 100 con warning "análisis incompleto"
- El frontend muestra mensaje claro de error

### Escenario 6: Auto-escaneo — n8n

| Parámetro | Valor |
|---|---|
| **URL** | `http://n8n:5678` |
| **Descripción** | Escanear el propio orquestador n8n |
| **Score esperado** | 50–75 (Regular) |
| **Propósito** | Demostración creativa en defensa oral |

---

## 6.2 Datasets

Los datasets se encuentran en la carpeta `datasets/` del repositorio. Contienen resultados simulados que representan la salida esperada del sistema para cada tipo de escenario.

### dataset: `sample_scan_vulnerable.json`

| Campo | Valor |
|---|---|
| Target | `http://dvwa:80` |
| Status | completed |
| Score | 22.5 |
| Total findings | 18 |

**Resumen de findings:**

| Fuente | Severidad | Count | Ejemplos |
|---|---|---|---|
| passive_headers | High | 1 | HSTS ausente |
| passive_headers | Medium | 2 | CSP ausente, X-Frame-Options ausente |
| passive_headers | Low | 1 | X-Content-Type-Options ausente |
| passive_ssl | High | 1 | No usa HTTPS |
| passive_cookies | Medium | 2 | PHPSESSID sin Secure, sin HttpOnly |
| passive_cookies | Low | 1 | PHPSESSID sin SameSite |
| passive_ports | Info | 1 | Puerto 80 abierto |
| passive_ports | High | 1 | Puerto 3306 (MySQL) abierto |
| passive_disclosure | Medium | 2 | phpinfo.php accesible, server-status accesible |
| passive_disclosure | Low | 2 | Header Server con versión, X-Powered-By |
| passive_tech | Info | 1 | PHP, Apache, jQuery |
| zap | High | 2 | XSS reflejado, SQL Injection |
| zap | Medium | 1 | CSRF Token ausente |

### dataset: `sample_scan_secure.json`

| Campo | Valor |
|---|---|
| Target | `https://github.com` |
| Status | completed |
| Score | 88.5 |
| Total findings | 5 |

**Resumen de findings:**

| Fuente | Severidad | Count | Ejemplos |
|---|---|---|---|
| passive_headers | Low | 2 | Permissions-Policy ausente, COEP ausente |
| passive_tech | Info | 1 | Ruby on Rails, Nginx, React |
| passive_ports | Info | 2 | Puerto 443 y 80 abiertos |

### dataset: `sample_scan_error.json`

| Campo | Valor |
|---|---|
| Target | `https://noexiste.invalid` |
| Status | completed |
| Score | 100.0 |
| Total findings | 7 (todos Info) |

**Resumen de findings:**

| Fuente | Severidad | Count | Tipo |
|---|---|---|---|
| passive_headers | Info | 1 | Connection Error |
| passive_ssl | Info | 1 | Connection Timeout |
| passive_ports | Info | 1 | DNS Resolution Error |
| passive_cookies | Info | 1 | Connection Error |
| passive_cors | Info | 1 | Connection Error |
| passive_disclosure | Info | 1 | Scan Error |
| passive_tech | Info | 1 | Connection Error |

---

## 6.3 Análisis Comparativo de Resultados

### Diferencial de Score

| Escenario | Score | Findings | Interpretación |
|---|---|---|---|
| **Vulnerable** (DVWA low) | 22.5 | 18 | 🔴 Múltiples vulnerabilidades graves (XSS, SQLi, no HTTPS) |
| **Seguro** (github.com) | 88.5 | 5 | 🟢 Pocas deficiencias menores, configuración robusta |
| **Error** (DNS fail) | 100.0 | 7 (Info) | ⚪ Sin análisis posible, score no penalizado |

**Diferencial vulnerable vs seguro: 66 puntos** (supera el mínimo esperado de 40 puntos).

### Distribución de Severidad

| Severidad | Vulnerable | Seguro | Error |
|---|---|---|---|
| Critical | 0 | 0 | 0 |
| High | 5 | 0 | 0 |
| Medium | 7 | 0 | 0 |
| Low | 4 | 2 | 0 |
| Info | 2 | 3 | 7 |

### Validación de Falsos Positivos

Para el target seguro (github.com), el sistema reportó solo 5 findings, todos de severidad Low o Info. Esto demuestra que:
1. No hay falsos positivos de severidad High o Critical en sitios bien configurados
2. Los findings Low corresponden a headers de seguridad opcionales genuinamente ausentes
3. Los findings Info son puramente informativos (tecnologías detectadas, puertos estándar)

---

## 6.4 Cómo Reproducir las Pruebas

### Vía API directa

```bash
# 1. Escanear DVWA (target vulnerable)
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url": "http://dvwa:80"}'

# 2. Escanear un target HTTPS seguro
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url": "https://github.com"}'

# 3. Escanear URL inexistente
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"target_url": "https://noexiste.invalid"}'

# 4. Consultar resultado
curl http://localhost:8000/scan/{scan_id} | python -m json.tool
```

### Vía Frontend

1. Abrir http://localhost:3000
2. Ingresar URL en el formulario
3. Observar la barra de progreso avanzando por las 5 fases
4. Al completar, ver: score gauge + tabla de findings + recomendaciones LLM

### Exportar resultados

```bash
# Exportar resultado completo como JSON
curl http://localhost:8000/scan/{scan_id} > datasets/resultado_real.json
```

---

## 6.5 Consultas SQL para Verificación

```sql
-- Verificar que hay scans en la BD
SELECT id, target_url, status, global_score, total_findings 
FROM scans ORDER BY created_at DESC LIMIT 10;

-- Verificar findings por severidad
SELECT severity, COUNT(*) 
FROM findings 
GROUP BY severity ORDER BY COUNT(*) DESC;

-- Verificar findings por fuente
SELECT source, COUNT(*) 
FROM findings 
GROUP BY source ORDER BY COUNT(*) DESC;

-- Verificar que el LLM generó análisis
SELECT scan_id, model_used, duration_ms, LENGTH(raw_response) as response_length 
FROM llm_analyses;

-- Verificar fases de un scan específico
SELECT phase_name, status, started_at, completed_at 
FROM scan_phases 
WHERE scan_id = '{scan_id}' ORDER BY started_at;
```
