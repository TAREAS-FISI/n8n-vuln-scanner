#!/bin/sh
# n8n Auto-Init: setup owner, login, import & activate workflows
# Runs as a one-shot container alongside docker compose up

set -e

apk add --no-cache jq >/dev/null 2>&1 || true

N8N_URL="${N8N_URL:-http://n8n:5678}"
N8N_EMAIL="${N8N_EMAIL:-admin@vulnscanner.local}"
N8N_PASSWORD="${N8N_PASSWORD:-Admin123!}"
WORKFLOWS_DIR="/workflows"
COOKIES="/tmp/n8n-cookies.txt"

log()  { echo "[init-n8n] $*"; }
ok()   { echo "[init-n8n] OK: $*"; }
fail() { echo "[init-n8n] FAIL: $*"; }
sep()  { echo "══════════════════════════════════════════════════"; }

# ─── 1. Wait for n8n ─────────────────────────────────────────
log "Waiting for n8n at $N8N_URL ..."
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$N8N_URL/healthz" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    ok "n8n is healthy"
    break
  fi
  if [ "$i" -eq 60 ]; then
    fail "n8n did not respond after 60 attempts"
    exit 1
  fi
  sleep 2
done
sleep 3

# ─── 2. Create owner account ─────────────────────────────────
sep
log "Setting up owner account ($N8N_EMAIL)..."

cat > /tmp/setup.json << JSONEOF
{"email":"$N8N_EMAIL","password":"$N8N_PASSWORD","firstName":"Admin","lastName":"VulnScanner"}
JSONEOF

setup_response=$(curl -s -w "\n%{http_code}" \
  "$N8N_URL/rest/owner/setup" \
  -H "Content-Type: application/json" \
  -c "$COOKIES" \
  --data-binary @/tmp/setup.json 2>/dev/null)

setup_code=$(echo "$setup_response" | tail -1)

if [ "$setup_code" = "200" ] || [ "$setup_code" = "201" ]; then
  ok "Owner account created (cookie saved)"
else
  log "Owner setup returned HTTP $setup_code (may already exist)"
  # ─── 3. Login if owner already exists ───────────────────────
  log "Logging in..."
  cat > /tmp/login.json << JSONEOF
{"emailOrLdapLoginId":"$N8N_EMAIL","password":"$N8N_PASSWORD"}
JSONEOF

  login_code=$(curl -s -o /dev/null -w "%{http_code}" \
    "$N8N_URL/rest/login" \
    -H "Content-Type: application/json" \
    -c "$COOKIES" \
    --data-binary @/tmp/login.json 2>/dev/null)

  if [ "$login_code" = "200" ]; then
    ok "Logged in"
  else
    fail "Could not login (HTTP $login_code). Aborting."
    exit 1
  fi
fi

# ─── 4. Import workflows ─────────────────────────────────────
sep
log "Importing workflows..."

IMPORTED=0
FAILED=0

for wf_file in "$WORKFLOWS_DIR"/0*.json; do
  [ -f "$wf_file" ] || continue
  filename=$(basename "$wf_file")
  wf_name=$(jq -r '.name // "unknown"' "$wf_file" 2>/dev/null || echo "$filename")

  log "Importing: $wf_name ($filename)"

  # Strip tags (they need IDs that don't exist yet) and id field
  jq 'del(.tags, .id)' "$wf_file" > /tmp/wf-clean.json

  response=$(curl -s -w "\n%{http_code}" \
    "$N8N_URL/rest/workflows" \
    -H "Content-Type: application/json" \
    -b "$COOKIES" \
    --data-binary @/tmp/wf-clean.json 2>/dev/null)

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    wf_id=$(echo "$body" | jq -r '.data.id // .id // "?"' 2>/dev/null || echo "?")
    ok "Imported $wf_name (ID: $wf_id)"
    IMPORTED=$((IMPORTED + 1))

    # ─── 5. Activate workflows 01 and 06 ──────────────────────
    if echo "$filename" | grep -qE "^01-|^06-"; then
      log "Activating $wf_name ..."

      # n8n 2.x requires versionId for activation
      version_id=$(echo "$body" | jq -r '.data.versionId // .versionId // empty' 2>/dev/null || echo "")
      if [ -z "$version_id" ]; then
        # Fetch versionId from workflow detail
        wf_detail=$(curl -s "$N8N_URL/rest/workflows/$wf_id" -b "$COOKIES" 2>/dev/null)
        version_id=$(echo "$wf_detail" | jq -r '.data.versionId // .versionId // empty' 2>/dev/null || echo "")
      fi

      if [ -n "$version_id" ]; then
        cat > /tmp/activate.json << JSONEOF
{"versionId":"$version_id"}
JSONEOF

        act_code=$(curl -s -o /dev/null -w "%{http_code}" \
          -X POST "$N8N_URL/rest/workflows/$wf_id/activate" \
          -H "Content-Type: application/json" \
          -b "$COOKIES" \
          --data-binary @/tmp/activate.json 2>/dev/null)

        if [ "$act_code" = "200" ]; then
          ok "Activated $wf_name"
        else
          fail "Could not activate $wf_name (HTTP $act_code)"
        fi
      else
        fail "Could not get versionId for $wf_name"
      fi
    fi
  else
    fail "Error importing $filename (HTTP $http_code)"
    FAILED=$((FAILED + 1))
  fi
done

# ─── Summary ─────────────────────────────────────────────────
sep
log "Done! $IMPORTED imported, $FAILED failed"
log "n8n UI: $N8N_URL"
sep

rm -f "$COOKIES" /tmp/setup.json /tmp/login.json /tmp/wf-clean.json /tmp/activate.json
exit 0
