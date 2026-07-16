#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/dg_renderbits_real_harness_20260716.XXXXXX")"
trap 'rm -rf "$OUT_DIR"' EXIT
OUT="$OUT_DIR/dg_renderbits_real_harness_20260716"
clang++ -std=c++17 -O0 -g -Wall -Wextra -pedantic \
  -I "$ROOT_DIR/tools/emulation/dg_renderbits_real_harness_20260716" \
  "$ROOT_DIR/tools/emulation/dg_renderbits_real_harness_20260716.cpp" \
  "$ROOT_DIR/core/olmdistancegradation_fieldgen.cpp" \
  -o "$OUT"
"$OUT"
