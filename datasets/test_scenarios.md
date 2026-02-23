# Escenarios de Prueba — n8n Vulnerability Scanner

## 1. Target Vulnerable (DVWA)

**URL:** `http://dvwa:80`

Resultado esperado:
- **Score:** 15–35 (muy bajo)
- **Findings esperados:**
  - Headers: ~10 headers faltantes (HSTS, CSP, X-Frame-Options…)
  - SSL: "El sitio no usa HTTPS" (High)
  - Cookies: PHPSESSID sin Secure, posiblemente sin HttpOnly/SameSite
  - CORS: probable wildcard o sin CORS
  - Info Disclosure: posibles server-status, phpinfo, .env
  - Tech Detection: PHP, Apache, jQuery
  - Ports: 80 abierto (info), posibles MySQL 3306

---

## 2. Target Seguro (ejemplo: github.com)

**URL:** `https://github.com`

Resultado esperado:
- **Score:** 75–95 (alto)
- **Findings esperados:**
  - Headers: la mayoría presentes, quizá falte algún header menor
  - SSL: TLS 1.3, certificado válido, cipher fuerte
  - Cookies: flags correctos (Secure, HttpOnly, SameSite)
  - CORS: configurado restrictivamente
  - Info Disclosure: sin archivos expuestos
  - Tech Detection: Ruby on Rails, Nginx

---

## 3. Target con SSL Expirado (ejemplo: expired.badssl.com)

**URL:** `https://expired.badssl.com`

Resultado esperado:
- **Score:** 40–60
- **Findings esperados:**
  - SSL: certificado expirado (High), posible protocolo débil
  - Headers: varios faltantes
  - Otros checks normales

---

## 4. Target HTTP sin cifrado

**URL:** `http://httpbin.org`

Resultado esperado:
- **Score:** 30–50
- **Findings:**
  - SSL: "No usa HTTPS" (High)
  - HSTS: inaplicable
  - Headers: varios faltantes
  - CORS: wildcard (*) posible (httpbin permite cors)

---

## 5. Target Inexistente / DNS Fail

**URL:** `https://noexiste.invalid`

Resultado esperado:
- **Score:** ~100 (sin findings porque no pudo conectar)
- Todos los checks devuelven Connection Error / DNS Error (Info)
- El pipeline n8n debería manejar gracefully

---

## 6. Target con Ports Peligrosos (red interna)

**URL:** `http://postgres:5432` (dentro de Docker network)

Resultado esperado:
- Puerto 5432 detectado como abierto y peligroso
- Info Disclosure: sin rutas web
- Headers: conexión fallida o respuesta no-HTTP

---

## Cómo ejecutar los tests

### Manual vía API
```bash
# Escanear DVWA (debe estar corriendo en Docker)
curl -X POST http://localhost:8000/scan -H 'Content-Type: application/json' \
  -d '{"target_url": "http://dvwa:80"}'

# Escanear un target HTTPS
curl -X POST http://localhost:8000/scan -H 'Content-Type: application/json' \
  -d '{"target_url": "https://github.com"}'

# Verificar health
curl http://localhost:8000/health
```

### Vía Frontend
1. Abrir http://localhost:3000
2. Ingresar URL en el formulario
3. Observar progreso en la página de detalle
4. Verificar Grafana en http://localhost:3001

### Checks Individuales
```bash
# Solo headers
curl -X POST http://localhost:8000/check/headers \
  -H 'Content-Type: application/json' -d '{"url": "https://github.com"}'

# Solo SSL
curl -X POST http://localhost:8000/check/ssl \
  -H 'Content-Type: application/json' -d '{"url": "https://github.com"}'

# Solo ports
curl -X POST http://localhost:8000/check/ports \
  -H 'Content-Type: application/json' -d '{"url": "https://github.com"}'
```
