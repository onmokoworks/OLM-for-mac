#!/bin/bash
# Diff all win/* PNGs against the same-named mac/* PNGs and summarize.
# Usage: diff_all.sh
set -u
cd "$(dirname "$0")/.."

WIN_DIR="win"
MAC_DIR="mac"
DIFF_DIR="diff"

shopt -s nullglob
ok=0
fail=0
missing=0
echo "=== OLMSmoother v1 byte-perfect verification ==="
for w in "$WIN_DIR"/*.png; do
    base="$(basename "$w")"
    m="$MAC_DIR/$base"
    if [ ! -f "$m" ]; then
        echo "[MISSING] $base (mac side)"
        missing=$((missing + 1))
        continue
    fi
    if python3 scripts/diff_one.py "$w" "$m" "$DIFF_DIR/${base%.png}_diff.png" >/dev/null 2>&1; then
        echo "[OK]      $base"
        ok=$((ok + 1))
    else
        echo "[DIFF]    $base"
        python3 scripts/diff_one.py "$w" "$m" "$DIFF_DIR/${base%.png}_diff.png" 2>&1 | sed 's/^/          /'
        fail=$((fail + 1))
    fi
done
echo "---"
echo "ok=$ok fail=$fail missing=$missing"
[ "$fail" -eq 0 ] && [ "$missing" -eq 0 ] && exit 0 || exit 1
