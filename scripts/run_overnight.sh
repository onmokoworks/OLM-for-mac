#!/bin/zsh
# Overnight runner: finishes any remaining 2025 aex that lack decomp output.
# Skips files already processed (decomp/*.c.txt present and > 1KB).
# Safe to rerun; uses -overwrite so partial project state is replaced.

set -u
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
ROOT="/Users/onmk/Documents/Projects/Personal/OLM as"
export OLM_OUT_DIR="$ROOT"
HEADLESS="/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless"
LOG="$ROOT/scripts/overnight.log"

echo "=== overnight runner start $(date) ===" >> "$LOG"

for aex in "$ROOT/aex"/*/Plugins/64/2025/*.aex; do
  name=$(basename "$aex")
  out="$ROOT/decomp/${name}.c.txt"
  if [[ -s "$out" ]] && [[ $(stat -f%z "$out") -gt 1024 ]]; then
    echo "[skip] $name (already done)" >> "$LOG"
    continue
  fi
  echo "[run ] $name @ $(date)" >> "$LOG"
  "$HEADLESS" "$ROOT/ghidra_proj" OLM2025 \
    -import "$aex" -overwrite \
    -scriptPath "$ROOT/scripts" \
    -postScript ExportAll.py \
    -loader PeLoader >> "$LOG" 2>&1
  echo "[done] $name @ $(date)" >> "$LOG"
done

echo "=== overnight runner end $(date) ===" >> "$LOG"
