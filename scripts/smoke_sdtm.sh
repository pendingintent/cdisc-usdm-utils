#!/usr/bin/env bash
set -euo pipefail
# Smoke: generate all domains from pilot protocol and assert expected files exist
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

USDM="files/pilot_LLZT_protocol.json"
OUTDIR="output/smoke"

# Determine which domains to verify (skip TS if spec missing)
DOMAINS=(TA TE TV TI)
if [[ -f spec/TSPARM_spec.csv ]]; then
  DOMAINS+=(TS)
else
  echo "[SMOKE INFO] spec/TSPARM_spec.csv not found; TS will be skipped" >&2
fi

# Ensure venv active or rely on PATH
if command -v usdm-utils >/dev/null 2>&1; then
  CMD=(usdm-utils)
else
  CMD=(python -m cdisc_usdm_utils.cli)
fi

"${CMD[@]}" sdtm all --usdm-file "$USDM" --out-dir "$OUTDIR"

fail() { echo "[SMOKE FAIL] $*" >&2; exit 1; }

for dom in "${DOMAINS[@]}"; do
  test -f "$OUTDIR/$dom.csv" || fail "$dom.csv not found"
  test -f "$OUTDIR/$dom.dataset.json" || fail "$dom.dataset.json not found"
  # Report if schema/struct errors exist but do not fail hard; this is informational
  if test -f "$OUTDIR/$dom.dataset.schema.errors.txt"; then
    echo "[SMOKE WARN] Schema issues for $dom (see $OUTDIR/$dom.dataset.schema.errors.txt)" >&2
  fi
  if test -f "$OUTDIR/$dom.dataset.errors.txt"; then
    echo "[SMOKE WARN] Structural issues for $dom (see $OUTDIR/$dom.dataset.errors.txt)" >&2
  fi
done

echo "[SMOKE PASS] SDTM generation completed for all domains into $OUTDIR"
