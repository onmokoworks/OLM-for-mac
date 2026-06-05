#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC="$ROOT_DIR/cli/OLMSmoother/main.cpp"
SHIM="$ROOT_DIR/cli/OLMSmoother/shim"
PORT="$ROOT_DIR/mac/OLMSmoother/Mac"
OUT="${1:-$ROOT_DIR/cli/OLMSmoother/olmsmoother_cli}"
CXX="${CXX:-clang++}"

# -I order matters: the shim dir must resolve "OLMSmoother.h" /
# "AEFX_SuiteHandlerTemplate.h" ahead of the real AE SDK header. The port .cpp
# dir is added so its #include "OLMSmoother_port.cpp" relative path works.
CXXFLAGS=(-std=c++17 -O2 -Wall -Wextra -I"$SHIM" -I"$PORT")
LDFLAGS=()

if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists libpng; then
  read -r -a PNG_CFLAGS <<<"$(pkg-config --cflags libpng)"
  read -r -a PNG_LIBS <<<"$(pkg-config --libs libpng)"
  CXXFLAGS+=("${PNG_CFLAGS[@]}")
  LDFLAGS+=("${PNG_LIBS[@]}")
elif [[ -f /opt/homebrew/include/png.h ]]; then
  CXXFLAGS+=(-I/opt/homebrew/include)
  LDFLAGS+=(-L/opt/homebrew/lib -lpng)
elif [[ -f /usr/local/include/png.h ]]; then
  CXXFLAGS+=(-I/usr/local/include)
  LDFLAGS+=(-L/usr/local/lib -lpng)
else
  LDFLAGS+=(-lpng)
fi

mkdir -p "$(dirname "$OUT")"
"$CXX" "${CXXFLAGS[@]}" "$SRC" "${LDFLAGS[@]}" -o "$OUT"
echo "$OUT"
