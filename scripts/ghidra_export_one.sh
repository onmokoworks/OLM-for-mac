#!/bin/zsh
# Import one AEX into the OLM Ghidra project and export asm/decompiled C.
#
# Usage:
#   scripts/ghidra_export_one.sh plugins_2025/OLMBlur.aex
#   scripts/ghidra_export_one.sh OLMBlur

set -euo pipefail
HERE="${0:A:h}"
source "$HERE/ghidra_env.sh"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <aex path | plugin basename>" >&2
  exit 2
fi

target="$1"
if [[ -f "$target" ]]; then
  aex="${target:A}"
elif [[ -f "$OLM_ROOT/plugins_2025/${target}.aex" ]]; then
  aex="$OLM_ROOT/plugins_2025/${target}.aex"
elif [[ -f "$OLM_ROOT/aex/${target}/Plugins/64/2025/${target}.aex" ]]; then
  aex="$OLM_ROOT/aex/${target}/Plugins/64/2025/${target}.aex"
elif [[ "$target" == "ColorKeep" && -f "$OLM_ROOT/aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex" ]]; then
  aex="$OLM_ROOT/aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
elif [[ "$target" == "DistanceGradation" && -f "$OLM_ROOT/aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex" ]]; then
  aex="$OLM_ROOT/aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
elif [[ "$target" == "OLMSmoother" && -f "$OLM_ROOT/aex/OLMSmootherAE/Plugins/64/2025/OLMSmoother.aex" ]]; then
  aex="$OLM_ROOT/aex/OLMSmootherAE/Plugins/64/2025/OLMSmoother.aex"
elif [[ "$target" == "OLMSmoother2" && -f "$OLM_ROOT/aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex" ]]; then
  aex="$OLM_ROOT/aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex"
else
  echo "AEX not found for: $target" >&2
  exit 2
fi

mkdir -p "$OLM_ROOT/decomp" "$OLM_ROOT/disasm" "$OLM_GHIDRA_PROJECT_DIR"
name="$(basename "$aex")"
echo "=== Ghidra export: $name ==="
echo "aex=$aex"
"$OLM_HEADLESS" "$OLM_GHIDRA_PROJECT_DIR" "$OLM_GHIDRA_PROJECT_NAME" \
  -import "$aex" \
  -overwrite \
  -scriptPath "$OLM_GHIDRA_SCRIPT_DIR" \
  -postScript ExportAll.py \
  -loader PeLoader

echo "decomp=$OLM_ROOT/decomp/${name}.c.txt"
echo "disasm=$OLM_ROOT/disasm/${name}.asm.txt"

