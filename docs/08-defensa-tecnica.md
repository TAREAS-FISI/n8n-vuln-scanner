# Entregable 8: Guía para la Defensa Técnica

## 8.1 Estructura de la Presentación

**Duración total:** 25–35 minutos (5–7 minutos por integrante)

### Orden sugerido

| # | Tema | Responsable | Duración | Contenido |
|---|---|---|---|---|
| 1 | Introducción + Problema | E | 5 min | Contexto, problema, solución propuesta |
| 2 | Diseño Conceptual | C | 5 min | Pipeline n8n, flujo de datos, 5 fases |
| 3 | Módulo Inteligente | B | 7 min | 3 capas: reglas, scoring, LLM |
| 4 | Arquitectura + Demo | D | 8 min | Docker Compose, demo en vivo |
| 5 | Resultados + Métricas | A | 5 min | Datasets, métricas, conclusiones |

---

## 8.2 Demo en Vivo — Guión

### Preparación previa (antes de la defensa)

```bash
# 1. Verificar que todo está corriendo
docker compose ps

# 2. Verificar que Ollama tiene el modelo
docker exec ollama ollama list

# 3. Tener DVWA configurado y logueado
# 4. Tener 2 pestañas abiertas:
#    - http://localhost:3000 (Frontend)
#    - http://localhost:3001 (Grafana)
# 5. Tener terminal lista para curl / docker commands
```

### Demo paso a paso

1. **Mostrar la arquitectura** (30s)
   - Abrir `docker compose ps` → mostrar los 10 servicios corriendo
   - Explicar brevemente cada servicio

2. **Escanear DVWA** (2 min)
   - Abrir http://localhost:3000
   - Ingresar `http://dvwa:80` en el formulario
   - Click "Escanear"
   - Mostrar la barra de progreso avanzando por las 5 fases
   - Mientras espera, explicar qué hace cada fase

3. **Mostrar el reporte** (2 min)
   - Cuando complete, mostrar el gauge de score (debería ser ~20-35)
   - Recorrer la tabla de findings: headers, SSL, ports, cookies
   - Expandir un finding para ver detalles
   - Mostrar las recomendaciones del LLM en español
   - Señalar las correlaciones identificadas por el LLM

4. **Mostrar Grafana** (1 min)
   - Cambiar a la pestaña de Grafana
   - Mostrar el dashboard con los datos del escaneo
   - Señalar: gauge de score, pie chart de severidad, tabla de scans

5. **Swagger API** (30s, opcional)
   - Abrir http://localhost:8000/docs
   - Mostrar los endpoints disponibles
   - Ejecutar un check individual (ej: `/check/headers`)

### Plan B (si la demo falla)

- Tener screenshots preparados de un escaneo exitoso previo
- Tener los JSON de datasets para mostrar resultados simulados
- Poder mostrar el código fuente directamente si el servicio no responde

---

## 8.3 Preguntas Frecuentes (FAQ) para la Defensa

### Sobre el problema y solución

**P: ¿Por qué no usar solo OWASP ZAP?**
> R: ZAP es excelente para DAST (XSS, SQLi) pero no verifica headers de seguridad, configuración SSL/TLS profunda, ni puertos abiertos. Combinando 4 fuentes obtenemos una visión más completa. Además, nuestros checks pasivos tardan <15s vs los 5-8 min de ZAP.

**P: ¿Por qué no usar una API de LLM en la nube (OpenAI, Claude)?**
> R: Requisito del curso: todo en localhost, $0 de gasto. Ollama con llama3.2:3b corre local, es gratuito, y genera análisis de calidad aceptable para nuestro caso de uso.

**P: ¿Qué pasa si el target bloquea los escaneos?**
> R: Los checks pasivos (Fase 1) no son intrusivos y rara vez se bloquean. ZAP y Nuclei pueden ser bloqueados por WAFs, lo que el sistema maneja como "fase con 0 findings" o "fase fallida" sin crashear.

### Sobre el módulo inteligente

**P: ¿Por qué esos pesos específicos en el scoring?**
> R: Los pesos reflejan la gravedad relativa: ZAP tiene 20% porque detecta vulnerabilidades explotables activamente (XSS, SQLi). Headers tienen 15% porque son configuraciones importantes pero menos críticas que una SQLi. Los pesos se pueden ajustar fácilmente modificando el diccionario en `scorer.py`.

**P: ¿El LLM puede generar falsos positivos?**
> R: El LLM no genera findings — solo analiza los que ya fueron detectados por las herramientas. Su rol es contextualizar y correlacionar, no detectar. Los falsos positivos vienen de las herramientas de detección (Capa 1), no del LLM (Capa 3).

**P: ¿Cómo validan que el LLM genera respuestas correctas?**
> R: Evaluación manual por 3 miembros en escala 1-5 (métrica M5). Además, verificamos que: (1) la respuesta tiene >100 chars, (2) menciona al menos una vulnerabilidad del reporte, (3) está en español. Si falla, se reintenta 1 vez.

**P: ¿Por qué llama3.2:3b y no un modelo más grande?**
> R: Balance entre calidad y recursos. El modelo 3B corre en CPU en <60s y en GPU en <15s. Modelos más grandes (7B, 13B) requieren más RAM y son significativamente más lentos sin GPU dedicada.

### Sobre la arquitectura

**P: ¿Por qué n8n y no código Python directo para orquestar?**
> R: n8n proporciona: (1) interfaz visual del pipeline, (2) retry automático, (3) logging de cada ejecución, (4) fácil modificación sin redeployar código. Además es requisito del curso usar n8n como orquestador.

**P: ¿Por qué PostgreSQL y no MongoDB?**
> R: PostgreSQL es soportado nativamente por Grafana (SQL directo para dashboards) y por n8n. Los datos son naturalmente relacionales (scans → findings → análisis). Además las vistas SQL simplifican queries de Grafana.

**P: ¿Por qué Nuclei y testssl son "one-shot" y no servicios persistentes?**
> R: Son herramientas CLI que no necesitan correr permanentemente. Ejecutarlos on-demand ahorra RAM (~500MB menos de uso constante). n8n usa `docker exec` para invocarlos cuando los necesita.

### Sobre implementación

**P: ¿Puden cambiar el umbral de scoring en vivo?**
> R: Sí. Abrir `backend/app/services/scorer.py`, modificar el diccionario `SEVERITY_FACTORS` o `SOURCE_WEIGHTS`, y reiniciar: `docker compose restart backend`. El cambio es inmediato.

**P: ¿Pueden agregar un header nuevo al checker?**
> R: Sí. Abrir `backend/app/services/header_checker.py`, agregar una entrada al diccionario `SECURITY_HEADERS` con: nombre, severidad, CVSS, descripción y remediación. Reiniciar backend.

**P: ¿Pueden modificar el prompt de Ollama?**
> R: Sí. El prompt se define en el workflow de n8n (`05-llm-analysis.json`). Se puede editar en la interfaz web de n8n sin tocar código. Alternativamente, si se envía desde FastAPI, se modifica en el backend.

---

## 8.4 Puntos Clave por Integrante

### Integrante A (Frontend)

**Debe dominar:**
- Cómo funciona el polling (ScanProgress consulta GET /scan/{id} cada 3s)
- Cómo se renderiza el ScoreGauge (SVG circular con colores dinámicos)
- Cómo la tabla de findings se filtra por severidad
- Cómo se formatean las recomendaciones del LLM (Markdown)
- TypeScript interfaces y su correspondencia con schemas del backend

**También debe saber explicar:**
- Cómo el backend calcula el score (Capa 2)
- Qué es CVSS y qué representan los niveles de severidad

### Integrante B (Backend)

**Debe dominar:**
- Los 7 checks de seguridad: qué verifica cada uno, qué reglas aplica
- El algoritmo de scoring: fórmula, pesos, factores, casos límite
- Los endpoints del API y su interacción con n8n
- SQLAlchemy async y el modelo de datos
- Pydantic schemas de request/response

**También debe saber explicar:**
- Cómo n8n orquesta el pipeline (Fase 3 → envía findings al backend)
- Cómo el LLM consume los findings para generar análisis

### Integrante C (n8n Workflows)

**Debe dominar:**
- El workflow principal y sus 5 fases
- Cómo se ejecutan Nuclei y testssl (Execute Command)
- Cómo funciona el polling de ZAP (spider + active scan)
- Cómo se parsean los resultados de cada herramienta
- Cómo se envían findings al backend (HTTP Request nodes)

**También debe saber explicar:**
- Qué hace cada check pasivo de FastAPI (Capa 1)
- Cómo el scoring combina resultados (Capa 2)

### Integrante D (DevOps + Grafana)

**Debe dominar:**
- Docker Compose: 10 servicios, redes, volúmenes, healthchecks
- Variables de entorno y configuración
- Grafana: provisioning, datasource, 8 paneles del dashboard
- Consultas SQL de las vistas de Grafana
- Troubleshooting: logs, restart, rebuild

**También debe saber explicar:**
- El flujo completo de datos desde URL hasta reporte
- El modelo de datos PostgreSQL (4 tablas + relaciones)

### Integrante E (Documentación + IA)

**Debe dominar:**
- La definición del problema y justificación como sistema inteligente
- Las 3 capas del módulo inteligente y sus diferencias
- El prompt de Ollama y los parámetros del modelo
- Las métricas de evaluación (7 inteligentes + 7 operativas)
- Los 3 escenarios de prueba y sus resultados esperados

**También debe saber explicar:**
- La arquitectura general del sistema
- Por qué se eligieron las tecnologías usadas (tabla de decisiones)

---

## 8.5 Modificaciones en Vivo (prepararse para)

El docente puede pedir cambios durante la defensa. Preparar estos escenarios:

### 1. Cambiar umbral de scoring

```python
# En scorer.py, cambiar:
SEVERITY_FACTORS = {
    "Critical": 30,   # era 25
    "High": 20,       # era 15
    ...
}
# docker compose restart backend
```

### 2. Agregar un header al checker

```python
# En header_checker.py, agregar al dict SECURITY_HEADERS:
"X-DNS-Prefetch-Control": {
    "severity": "Info",
    "cvss": 1.0,
    "description": "Controla DNS prefetching del navegador",
    "remediation": "Agregar: X-DNS-Prefetch-Control: off"
}
# docker compose restart backend
```

### 3. Modificar prompt del LLM

```
# En n8n UI → abrir el workflow → nodo de Ollama
# Cambiar el system prompt, por ejemplo agregar:
"Incluye también una sección de CUMPLIMIENTO NORMATIVO 
indicando qué regulaciones (GDPR, PCI-DSS, OWASP Top 10) 
se ven afectadas por cada vulnerabilidad."
# Guardar workflow → ejecutar nuevo scan
```

### 4. Agregar un puerto al scanner

```python
# En port_scanner.py, agregar al dict PORTS:
PORTS = {
    ...
    9090: {"name": "Prometheus", "risky": True, "severity": "High", "cvss": 7.5},
}
# docker compose restart backend
```

---

## 8.6 Checklist Pre-Defensa

- [ ] `docker compose ps` → 10 servicios UP
- [ ] DVWA configurado (BD creada, login funciona)
- [ ] Ollama tiene modelo: `docker exec ollama ollama list`
- [ ] Frontend carga: http://localhost:3000
- [ ] Grafana carga con datos: http://localhost:3001
- [ ] Al menos 1 escaneo completado previamente (para Grafana)
- [ ] Tener backup de screenshots por si falla la demo en vivo
- [ ] Cada integrante sabe su sección + 1 sección del compañero
- [ ] Presentación lista (PDF o PowerPoint)
- [ ] Informe PDF impreso o en digital
