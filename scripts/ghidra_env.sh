#!/bin/zsh
# Shared Ghidra paths for OLM reverse-engineering scripts.

export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home}"
export PATH="$JAVA_HOME/bin:$PATH"

export OLM_ROOT="${OLM_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
export OLM_GHIDRA_PROJECT_DIR="${OLM_GHIDRA_PROJECT_DIR:-$OLM_ROOT/ghidra_proj}"
export OLM_GHIDRA_PROJECT_NAME="${OLM_GHIDRA_PROJECT_NAME:-OLM2025}"
export OLM_GHIDRA_SCRIPT_DIR="${OLM_GHIDRA_SCRIPT_DIR:-$OLM_ROOT/scripts}"
export OLM_OUT_DIR="${OLM_OUT_DIR:-$OLM_ROOT}"
export OLM_HEADLESS="${OLM_HEADLESS:-/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless}"
