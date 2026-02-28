# Entregable 3: Diseño del Módulo Inteligente

## 3.1 Visión General

El módulo inteligente del sistema opera en **3 capas de decisión**, cada una con un nivel creciente de complejidad y abstracción:

```
┌───────────────────────────────────────────────────────────────┐
│                 MÓDULO INTELIGENTE (3 CAPAS)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CAPA 3: Análisis Contextual con LLM                    │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  • Correlación entre hallazgos                     │  │  │
│  │  │  • Priorización por impacto/esfuerzo               │  │  │
│  │  │  • Recomendaciones en español con código           │  │  │
│  │  │  • Detección de combinaciones peligrosas           │  │  │
│  │  │  Modelo: Ollama llama3.2:3b (local, 0 costo)      │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                          ▲ recibe score + findings             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CAPA 2: Scoring Ponderado                              │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  • Factores de penalización por severidad          │  │  │
│  │  │  • Pesos diferenciados por fuente de detección     │  │  │
│  │  │  • Score global 0–100                              │  │  │
│  │  │  • Breakdown por categoría                         │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                          ▲ recibe lista de findings            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CAPA 1: Reglas Deterministas                           │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  • 7 módulos de checks con reglas if-then          │  │  │
│  │  │  • Severidad y CVSS predefinidos por regla         │  │  │
│  │  │  • Herramientas externas (ZAP, Nuclei, testssl)    │  │  │
│  │  │  • Formato estándar: Finding(source, severity...)  │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 3.2 Capa 1: Reglas Deterministas

### Tipo de Inteligencia
Sistema basado en reglas (if-then) con severidad y puntuación CVSS predefinidas.

### Descripción
Cada módulo de análisis aplica un conjunto concreto de reglas de seguridad. Cuando una condición se cumple, se genera un **finding** con datos estructurados.

### Módulos y Reglas

#### Header Checker (12 reglas)

| Condición | Severidad | CVSS | Justificación |
|---|---|---|---|
| HSTS ausente (en sitio HTTPS) | High | 7.4 | Permite ataques de downgrade HTTP |
| Content-Security-Policy ausente | Medium | 5.3 | Sin protección contra XSS |
| X-Frame-Options ausente | Medium | 4.3 | Permite clickjacking |
| X-Content-Type-Options ausente | Low | 3.7 | Posible MIME sniffing |
| Referrer-Policy ausente | Low | 3.1 | Fuga de información en referrers |
| Permissions-Policy ausente | Low | 2.6 | Sin restricción de APIs del navegador |
| Cache-Control ausente | Low | 2.2 | Datos sensibles pueden cachearse |
| COOP ausente | Low | 2.6 | Protección parcial contra Spectre |
| CORP ausente | Low | 2.6 | Sin control de recursos cross-origin |
| COEP ausente | Low | 2.6 | Sin aislamiento cross-origin |
| X-Permitted-Cross-Domain ausente | Info | 1.0 | Header menor de seguridad |

**Lógica especial:** Si el sitio es HTTP (no HTTPS), HSTS se reporta como Info en vez de High, ya que el header no aplica sin cifrado.

#### SSL Checker (4 categorías de reglas)

| Condición | Severidad | CVSS |
|---|---|---|
| Sitio no usa HTTPS | High | 7.4 |
| Certificado expirado | High | 7.5 |
| Certificado self-signed / inválido | High | 7.5 |
| Certificado expira en < 30 días | Medium | 4.0 |
| Protocolo SSLv2, SSLv3, TLS 1.0, TLS 1.1 | Medium | 5.9 |
| Cipher débil (RC4, DES, 3DES, NULL, EXPORT, anon) | Medium | 5.3 |

#### Port Scanner (21 puertos)

| Condición | Severidad | CVSS |
|---|---|---|
| Redis (6379) abierto | High | 8.1 |
| MongoDB (27017) abierto | High | 8.1 |
| Elasticsearch (9200) abierto | High | 8.1 |
| Memcached (11211) abierto | High | 8.1 |
| MySQL (3306) abierto | High | 7.5 |
| PostgreSQL (5432) abierto | High | 7.5 |
| RDP (3389) abierto | High | 8.0 |
| VNC (5900) abierto | High | 8.0 |
| Telnet (23) abierto | High | 8.0 |
| FTP (21) abierto | High | 7.5 |
| SMB (445) abierto | High | 8.0 |
| Puertos estándar (80, 443, 22, etc.) | Info | 0.0 |

#### Cookie Checker (3 reglas por cookie)

| Condición | Severidad | CVSS |
|---|---|---|
| Cookie sin flag `Secure` (en HTTPS) | Medium | 4.3 |
| Cookie sin flag `HttpOnly` | Medium | 4.3 |
| Cookie sin flag `SameSite` | Low | 3.1 |

#### CORS Checker (3 reglas)

| Condición | Severidad | CVSS |
|---|---|---|
| Wildcard `*` + `Access-Control-Allow-Credentials` | Critical | 9.1 |
| Origin reflejado con credenciales | Critical | 9.1 |
| Origin reflejado sin credenciales | High | 7.5 |
| Wildcard `*` sin credenciales | Medium | 5.4 |

#### Info Disclosure (9 rutas + 2 headers)

| Condición | Severidad | CVSS |
|---|---|---|
| `/.env` accesible y contiene claves | Critical | 9.8 |
| `/wp-config.php.bak` accesible | Critical | 9.8 |
| `/.git/config` accesible | High | 8.6 |
| `/.git/HEAD` accesible | High | 8.6 |
| `/server-status` accesible | Medium | 5.3 |
| `/phpinfo.php` accesible | Medium | 5.3 |
| `/.htaccess` accesible | Medium | 5.3 |
| Header `Server` expone versión | Low | 3.7 |
| Header `X-Powered-By` presente | Low | 3.7 |

**Anti-falsos positivos:** Cada ruta se valida verificando que el cuerpo de la respuesta contiene indicadores esperados (ej: `/.env` debe contener "=", `/.git/config` debe contener "[core]").

#### Tech Detector (15+ patrones)

Informativo (Severity: Info, CVSS: 0.0). Detecta tecnologías desde:
- Header `Server`
- Header `X-Powered-By`
- Cookies conocidas (PHPSESSID → PHP, JSESSIONID → Java, etc.)
- Patrones HTML/JavaScript (WordPress, React, Angular, Vue, jQuery, etc.)

### Variables de Entrada (Capa 1)

| Variable | Tipo | Fuente |
|---|---|---|
| URL del target | string | Usuario |
| Response headers HTTP | dict | httpx GET request |
| Response status code | int | httpx GET request |
| Response body (primeros 50KB) | string | httpx GET request |
| Certificado SSL | objeto | ssl.SSLSocket |
| Estado de puertos TCP | bool por puerto | socket.connect_ex() |
| Cookies Set-Cookie | lista | Response headers |

### Salida (Capa 1)
Lista de objetos `Finding`:
```json
{
  "source": "passive_headers",
  "category": "Missing Security Header",
  "title": "Header 'Strict-Transport-Security' no encontrado",
  "severity": "High",
  "cvss_score": 7.4,
  "description": "El header HSTS no está presente...",
  "remediation": "Agregar: Strict-Transport-Security: max-age=31536000; includeSubDomains"
}
```

---

## 3.3 Capa 2: Scoring Ponderado

### Tipo de Inteligencia
Algoritmo de puntuación multi-criterio (decision scoring).

### Descripción
Combina **todos los findings** de las 4 fuentes de detección en un **score global 0–100** que indica el nivel de seguridad del sitio.

### Pseudocódigo

```
FUNCIÓN calcular_score(findings):
    score ← 100.0
    
    // Factores de penalización por nivel de severidad
    factores_severidad ← {
        "Critical": 25,    // Vulnerabilidad explotable directamente
        "High":     15,    // Riesgo significativo
        "Medium":    8,    // Riesgo moderado
        "Low":       3,    // Riesgo menor
        "Info":      0     // Informativo, sin penalización
    }
    
    // Pesos por fuente de detección (suman ~1.0)
    pesos_fuente ← {
        "passive_headers":     0.15,    // Headers de seguridad
        "passive_ssl":         0.10,    // SSL/TLS básico
        "passive_ports":       0.10,    // Puertos abiertos
        "passive_cookies":     0.05,    // Cookies
        "passive_cors":        0.05,    // CORS
        "passive_disclosure":  0.05,    // Info disclosure
        "passive_tech":        0.00,    // Solo informativo
        "testssl":             0.15,    // Auditoría SSL profunda
        "nuclei":              0.15,    // CVEs conocidas
        "zap":                 0.20     // DAST completo
    }
    
    breakdown ← {}
    
    PARA CADA finding EN findings:
        peso ← pesos_fuente[finding.source] O 0.10 (default)
        factor ← factores_severidad[finding.severity] O 0
        penalización ← factor × peso
        score ← score - penalización
        
        // Registrar en breakdown
        breakdown[finding.source].penalty += penalización
        breakdown[finding.source].count += 1
    
    // Clampear resultado
    score ← MAX(0, MIN(100, score))
    
    // Warnings de casos especiales
    SI findings.length == 0:
        AGREGAR warning "Sin findings — análisis puede estar incompleto"
    SI score == 100 Y findings con Info > 0:
        AGREGAR warning "Score perfecto pero existen findings informativos"
    
    RETORNAR {
        global_score: REDONDEAR(score, 1),
        total_findings: findings.length,
        breakdown: breakdown,
        warnings: warnings
    }
```

### Tabla de Impacto

#### Ejemplo de cálculo para un sitio vulnerable:

| Finding | Source | Severity | Factor | Peso | Penalización |
|---|---|---|---|---|---|
| HSTS ausente | passive_headers | High | 15 | 0.15 | 2.25 |
| CSP ausente | passive_headers | Medium | 8 | 0.15 | 1.20 |
| No usa HTTPS | passive_ssl | High | 15 | 0.10 | 1.50 |
| Redis abierto | passive_ports | High | 15 | 0.10 | 1.50 |
| Cookie sin HttpOnly | passive_cookies | Medium | 8 | 0.05 | 0.40 |
| `.env` expuesto | passive_disclosure | Critical | 25 | 0.05 | 1.25 |
| XSS detectado (ZAP) | zap | High | 15 | 0.20 | 3.00 |
| SQLi detectado (ZAP) | zap | High | 15 | 0.20 | 3.00 |
| CVE-2021-XXXX (Nuclei) | nuclei | Critical | 25 | 0.15 | 3.75 |
| **TOTAL** | | | | | **17.85** |

**Score final: 100 - 17.85 = 82.15 → 82.2**

### Interpretación del Score

| Rango | Color | Categoría | Significado |
|---|---|---|---|
| 80–100 | 🟢 Verde | **Bueno** | Pocas vulnerabilidades, configuración mayormente correcta |
| 50–79 | 🟡 Amarillo | **Regular** | Vulnerabilidades moderadas, requiere atención |
| 30–49 | 🟠 Naranja | **Bajo** | Problemas significativos de seguridad |
| 0–29 | 🔴 Rojo | **Crítico** | Múltiples vulnerabilidades graves, acción urgente |

### Casos Límite

| Caso | Comportamiento | Razonamiento |
|---|---|---|
| 0 findings | Score = 100 + warning | Podría indicar fallo en detección |
| Solo findings Info | Score ≈ 100 | Findings informativos no penalizan |
| 1 finding Critical | Score ≈ 75–95 | Depende de la fuente (peso) |
| >100 findings | Score puede llegar a 0 | Cap correcto, indica sitio muy vulnerable |
| Fuente desconocida | Peso default = 0.10 | Manejo seguro de fuentes no mapeadas |

---

## 3.4 Capa 3: Análisis Contextual con LLM

### Tipo de Inteligencia
IA generativa local (Ollama + modelo llama3.2:3b).

### Descripción
El LLM recibe **todos los findings brutos** junto con el score calculado y genera un análisis multidimensional que va más allá de lo que las reglas deterministas pueden ofrecer.

### Capacidades del LLM

1. **Análisis de riesgo contextualizado**: no dice simplemente "falta HSTS", sino explica que "su sitio es vulnerable a ataques de downgrade porque no fuerza HTTPS, lo que permite interceptar tráfico en redes WiFi públicas".

2. **Correlación entre hallazgos**: identifica combinaciones peligrosas, por ejemplo "la combinación de CORS wildcard + cookies sin SameSite permite ataques CSRF cross-origin que podrían robar sesiones de usuario".

3. **Priorización accionable**: ordena las remediaciones por ratio impacto/esfuerzo, indicando qué cambios son rápidos y de alto impacto.

4. **Código de ejemplo**: genera snippets de configuración para Apache, Nginx, etc.

### Prompt del Sistema

```
Eres un experto en ciberseguridad web con 15 años de experiencia.
Analiza los hallazgos de un escaneo de seguridad de la URL: {url}

INSTRUCCIONES:
1. Para cada vulnerabilidad crítica y alta, explica:
   - Qué riesgo representa EN CONTEXTO (no genérico)
   - Cómo podría ser explotada (escenario realista)
   - Pasos de remediación con código/configuración
2. Identifica CORRELACIONES entre hallazgos que aumenten el riesgo combinado
3. Genera un RESUMEN EJECUTIVO de 3 líneas al inicio
4. Ordena las recomendaciones de MAYOR a MENOR impacto
5. Responde SIEMPRE en español

Score actual: {score}/100
Hallazgos ({count} total):
{findings_json}
```

### Parámetros del Modelo

| Parámetro | Valor | Justificación |
|---|---|---|
| `model` | llama3.2:3b | Modelo compacto, ejecutable en CPU/GPU local |
| `temperature` | 0.3 | Baja creatividad → respuestas más precisas y consistentes |
| `num_predict` | 2048 | Suficiente para análisis detallado (~500 palabras) |
| `stream` | false | Respuesta completa de una vez (para parsear) |

### Variables de Entrada (Capa 3)

| Variable | Tipo | Fuente |
|---|---|---|
| URL escaneada | string | Registro del scan |
| Score global | float 0–100 | Capa 2 |
| Lista de findings | JSON array | Capa 1 + herramientas externas |
| Count de findings | int | Calculado |

### Salida (Capa 3)

```json
{
  "raw_prompt": "Eres un experto...",
  "raw_response": "## Resumen Ejecutivo\n\nEl sitio analizado presenta...",
  "recommendations_json": [
    {
      "priority": 1,
      "title": "Implementar HTTPS y HSTS",
      "impact": "Critical",
      "effort": "Low",
      "description": "...",
      "code_example": "# Nginx config\nadd_header Strict-Transport-Security..."
    }
  ],
  "model_used": "llama3.2:3b",
  "duration_ms": 15230
}
```

### Casos Límite (Capa 3)

| Caso | Comportamiento |
|---|---|
| **Ollama no disponible** | Reporte se genera sin análisis LLM; campo `llm_analysis: null`; frontend muestra "Análisis IA no disponible" |
| **>50 findings** | Se truncan a los top 30 por severidad (Critical primero) antes de enviar al LLM para respetar el límite de contexto del modelo |
| **Respuesta incoherente** (<100 chars) | Se reintenta 1 vez; si falla de nuevo, se retorna null |
| **Timeout (>60s)** | Se retorna contenido parcial si hay; sino null |

---

## 3.5 Integración de las 3 Capas

```
DATOS BRUTOS                    CAPA 1                CAPA 2              CAPA 3
─────────────                   ──────                ──────              ──────
                                                                         
Headers HTTP ──────► Header     ┐                                        
Cert SSL     ──────► SSL        │                                        
Puertos TCP  ──────► Ports      ├─► Findings ──► Scoring ──► Score ──┐   
Cookies      ──────► Cookies    │               Ponderado    0-100   ├──► LLM
CORS headers ──────► CORS       │                                    │   Análisis
Rutas /.env  ──────► Disclosure │                                    │   Contextual
Server header──────► Tech       ┘                                    │   
ZAP alerts   ──────► Transform  ─► Findings ─────────────────────────┤   
Nuclei JSONL ──────► Transform  ─► Findings ─────────────────────────┤   
testssl JSON ──────► Transform  ─► Findings ─────────────────────────┘   
                                                                     │
                                                                     ▼
                                                              REPORTE FINAL
                                                              Score + Findings
                                                              + Recomendaciones
                                                              + Correlaciones
```

### Flujo de datos entre capas

1. **Capa 1** produce una lista heterogénea de findings desde 9+ fuentes
2. **Capa 2** consume esa lista y produce un score numérico con breakdown
3. **Capa 3** consume tanto los findings como el score y produce análisis natural en español

Cada capa agrega un nivel de abstracción y valor inteligente sobre la anterior.
