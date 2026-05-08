#!/bin/zsh
set -e
export JAVA_HOME="/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
ROOT="/Users/onmk/Documents/Projects/Personal/OLM as"
PROJ_DIR="$ROOT/ghidra_proj"
PROJ_NAME="OLM2025"
SCRIPT_DIR="$ROOT/scripts"
HEADLESS="/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless"

export OLM_OUT_DIR="$ROOT"

for aex in "$ROOT/aex"/*/Plugins/64/2025/*.aex; do
  name=$(basename "$aex")
  echo "==== $name ===="
  "$HEADLESS" "$PROJ_DIR" "$PROJ_NAME" \
    -import "$aex" \
    -overwrite \
    -scriptPath "$SCRIPT_DIR" \
    -postScript ExportAll.py \
    -loader PeLoader
done
