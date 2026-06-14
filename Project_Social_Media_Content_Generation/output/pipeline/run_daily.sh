#!/usr/bin/env bash
#
# run_daily.sh — Entry point for the LinkedIn automation pipeline.
# Called by cron, systemd timer, or Activepieces.
#
# Usage:
#   ./run_daily.sh                    # Run now, default config
#   ./run_daily.sh --config prod.yaml # Alternate config
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.yaml"

for arg in "$@"; do
    if [[ "$arg" == --config=* ]]; then
        CONFIG="${arg#*=}"
    fi
done

cd "$SCRIPT_DIR"

LOG_DIR="$(yq '.output.log_dir' "$CONFIG")"
mkdir -p "$LOG_DIR"

python3 "${SCRIPT_DIR}/content_pipeline.py" 2>&1 | tee "$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

exit ${PIPESTATUS[0]}
