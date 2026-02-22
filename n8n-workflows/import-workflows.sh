#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Script para importar workflows de n8n via API
# Ejecutar DESPUÉS de que n8n esté corriendo:
#   docker compose up -d
#   bash n8n-workflows/import-workflows.sh
# ══════════════════════════════════════════════════════════════

set -e

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_USER="${N8N_BASIC_AUTH_USER:-admin}"
N8N_PASS="${N8N_BASIC_AUTH_PASSWORD:-admin}"

echo "═══════════════════════════════════════════"
echo "  Importando workflows a n8n..."
echo "  URL: $N8N_URL"
echo "═══════════════════════════════════════════"
echo ""

# Esperar a que n8n esté listo
echo "⏳ Esperando a que n8n esté disponible..."
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" "$N8N_URL/healthz" | grep -q "200"; then
    echo "✅ n8n está listo!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ n8n no respondió después de 30 intentos. ¿Está corriendo?"
    exit 1
  fi
  echo "   Intento $i/30..."
  sleep 2
done
echo ""

# Importar cada workflow
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPORTED=0
FAILED=0

for wf_file in "$SCRIPT_DIR"/0*.json; do
  filename=$(basename "$wf_file")
  wf_name=$(python3 -c "import json; print(json.load(open('$wf_file'))['name'])" 2>/dev/null || echo "$filename")
  
  echo "📦 Importando: $wf_name ($filename)"
  
  response=$(curl -s -w "\n%{http_code}" \
    -X POST "$N8N_URL/api/v1/workflows" \
    -u "$N8N_USER:$N8N_PASS" \
    -H "Content-Type: application/json" \
    -d @"$wf_file" 2>/dev/null)
  
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | head -n -1)
  
  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    wf_id=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null || echo "?")
    echo "   ✅ Importado (ID: $wf_id)"
    IMPORTED=$((IMPORTED + 1))
    
    # Activar el workflow si es el pipeline principal o el reporte diario
    if echo "$filename" | grep -qE "01-|06-"; then
      activate_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X PATCH "$N8N_URL/api/v1/workflows/$wf_id" \
        -u "$N8N_USER:$N8N_PASS" \
        -H "Content-Type: application/json" \
        -d '{"active": true}' 2>/dev/null)
      
      if [ "$activate_response" = "200" ]; then
        echo "   🟢 Activado"
      else
        echo "   ⚠️  No se pudo activar automáticamente. Activarlo manualmente en n8n UI."
      fi
    fi
  else
    echo "   ❌ Error (HTTP $http_code)"
    FAILED=$((FAILED + 1))
  fi
  echo ""
done

echo "═══════════════════════════════════════════"
echo "  Resumen: $IMPORTED importados, $FAILED fallidos"
echo ""
echo "  Abrir n8n: $N8N_URL  (${N8N_USER}/${N8N_PASS})"
echo ""
echo "  IMPORTANTE: Activar manualmente el workflow"
echo "  '01 — Scan Pipeline Principal' si no se activó."
echo "═══════════════════════════════════════════"
