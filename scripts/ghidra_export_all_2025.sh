#!/bin/zsh
# Export all current 2025 AEX files from plugins_2025/.

set -euo pipefail
HERE="${0:A:h}"
source "$HERE/ghidra_env.sh"

shopt_status=0
for aex in "$OLM_ROOT"/plugins_2025/*.aex; do
  [[ -f "$aex" ]] || continue
  "$HERE/ghidra_export_one.sh" "$aex"
done

