#!/usr/bin/env bash
# =============================================================================
# Pulse — Demo Setup Script
# Liquid Death social crisis + Crosby LLMO drift
#
# Usage:
#   ./run_demo.sh           # full setup (seed + inject + LLMO probe)
#   ./run_demo.sh seed      # seed DB only
#   ./run_demo.sh inject    # inject live tweets only (seed first)
#   ./run_demo.sh stream    # start X filtered stream consumer (needs X API)
#   ./run_demo.sh llmo      # trigger LLMO probe via API
#   ./run_demo.sh mock      # start mock backend (no real DB needed)
# =============================================================================

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
API_URL="${PULSE_API_URL:-http://localhost:8000}"

# Load .env from repo root
if [ -f "$ROOT/.env" ]; then
  set -a; source "$ROOT/.env"; set +a
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}▶ $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠  $*${NC}"; }
error() { echo -e "${RED}✗ $*${NC}"; }

# ---------------------------------------------------------------------------
check_backend() {
  if curl -sf "$API_URL/api/health" > /dev/null 2>&1; then
    info "Backend is running at $API_URL"
    return 0
  else
    warn "Backend not running at $API_URL"
    return 1
  fi
}

# ---------------------------------------------------------------------------
cmd_seed() {
  info "Seeding Liquid Death demo brand + posts + cluster + actions…"
  cd "$BACKEND"
  python scripts/seed_demo.py
  echo ""
  info "Seeding LLMO prompts for Liquid Death + Crosby…"
  python scripts/seed_llmo.py
}

# ---------------------------------------------------------------------------
cmd_inject() {
  info "Injecting 7 demo tweets through the Pulse webhook…"
  if [ -z "$PULSE_BRAND_ID" ]; then
    error "PULSE_BRAND_ID not set. Run './run_demo.sh seed' first and add the brand_id to .env"
    exit 1
  fi
  cd "$BACKEND"
  python scripts/demo_inject.py --delay "${INJECT_DELAY:-4}"
}

# ---------------------------------------------------------------------------
cmd_stream() {
  info "Starting X filtered stream consumer…"
  if [ -z "$X_BEARER_TOKEN" ]; then
    error "X_BEARER_TOKEN not set in .env"
    exit 1
  fi
  if [ -z "$PULSE_BRAND_ID" ]; then
    error "PULSE_BRAND_ID not set. Run './run_demo.sh seed' first."
    exit 1
  fi
  info "Setting up stream rules first…"
  cd "$BACKEND" && python scripts/setup_x_stream.py
  echo ""
  info "Starting consumer (Ctrl+C to stop)…"
  python scripts/x_stream_consumer.py
}

# ---------------------------------------------------------------------------
cmd_llmo() {
  info "Triggering LLMO probe via API…"
  if [ -z "$PULSE_BRAND_ID" ]; then
    error "PULSE_BRAND_ID not set"
    exit 1
  fi
  curl -sf -X POST "$API_URL/api/llmo/probe?brand_id=$PULSE_BRAND_ID" \
    -H "Content-Type: application/json" && echo "" \
    || error "LLMO probe request failed — is the backend running?"
}

# ---------------------------------------------------------------------------
cmd_mock() {
  info "Starting mock backend on port 8000 (no real DB needed)…"
  info "Then open a new terminal and run: cd frontend && npm run dev"
  node "$FRONTEND/mock-server.mjs"
}

# ---------------------------------------------------------------------------
cmd_all() {
  echo ""
  echo "=============================================="
  echo "  Pulse Demo Setup — Liquid Death × Crosby"
  echo "=============================================="
  echo ""

  if ! check_backend; then
    warn "Start the backend first:"
    warn "  cd backend && uvicorn app.main:app --reload"
    warn "Or use './run_demo.sh mock' to start the mock server."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r; echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
  fi

  cmd_seed
  echo ""
  warn "Add the brand_id printed above to your .env as PULSE_BRAND_ID, then press Enter."
  read -p "  PULSE_BRAND_ID: " BRAND_ID_INPUT
  export PULSE_BRAND_ID="$BRAND_ID_INPUT"
  echo "PULSE_BRAND_ID=$BRAND_ID_INPUT" >> "$ROOT/.env"

  echo ""
  echo "Choose demo ingest method:"
  echo "  1) demo_inject.py  — fires pre-written tweets locally (reliable, no X API needed)"
  echo "  2) x_stream_consumer.py — real X filtered stream (requires X Basic access)"
  read -p "  Choice [1/2]: " -n 1 -r INGEST_CHOICE; echo

  if [[ "$INGEST_CHOICE" == "2" ]]; then
    info "Starting X stream in background…"
    cd "$BACKEND" && python scripts/setup_x_stream.py
    python scripts/x_stream_consumer.py &
    STREAM_PID=$!
    echo "  Stream PID: $STREAM_PID"
    info "Now tweet from your demo accounts at @liquiddeathwater or with 'liquid death'"
  else
    cmd_inject
  fi

  echo ""
  info "Triggering LLMO probe for Liquid Death + Crosby…"
  cmd_llmo

  echo ""
  echo "=============================================="
  info "Setup complete. Open http://localhost:3000"
  echo ""
  echo "  Dashboard → Overall 73 / Social 81 / LLMO 65"
  echo "  /feed     → live posts streaming in"
  echo "  /clusters → Critical: 'Metallic taste + stockout — Batch 24B-11'"
  echo "  /queue    → score breakdown columns"
  echo "  /llmo     → ChatGPT high drift on Liquid Death + Crosby"
  echo "  /actions  → 3 pending: response + ticket + escalation"
  echo "=============================================="
}

# ---------------------------------------------------------------------------
CMD="${1:-all}"
case "$CMD" in
  seed)    cmd_seed ;;
  inject)  cmd_inject ;;
  stream)  cmd_stream ;;
  llmo)    cmd_llmo ;;
  mock)    cmd_mock ;;
  all|"")  cmd_all ;;
  *)
    echo "Usage: ./run_demo.sh [seed|inject|stream|llmo|mock]"
    exit 1
    ;;
esac
