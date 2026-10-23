#!/bin/bash
# Run before deleting the new worker's build tree; optional independent cache root.
set -euo pipefail
cd "$(dirname "$0")/../../.."
s="$PWD/orchestra/state/F29-unicorn-sse-nan-propagation"
cache="${1:-/Users/onmk/.cache/olm-emu}"
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
base=/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/build/unicorn-engine-sys-6b38d341175b1fb7/out/lib
new=("$cache"/worker-F29-ssenan/build/release/build/unicorn-engine-sys-*/out/lib)
[ "${#new[@]}" = 1 ] && [ -f "${new[0]}/libunicorn.2.dylib" ]
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for variant in 214 215 patched; do
 args=()
 [ "$variant" != 215 ] || args=(--library "$base")
 [ "$variant" != patched ] || args=(--library "${new[0]}")
 label="uc$variant"
 [ "$variant" != patched ] || label=patched
 "$py" tools/emulation/aexcompat_patches/probe_sse_nan_F29.py --scratch "$s/probe$variant" --output "$s/$label.jsonl" ${args[@]+"${args[@]}"} > "$s/probe$variant.log" 2>&1
done
for variant in baseline patched; do
 lib="$base"
 [ "$variant" != patched ] || lib="${new[0]}"
 "$py" tools/emulation/aexcompat_patches/probe_controls_F29.py --scratch "$s/controls-$variant" --output "$s/controls-$variant.json" --library "$lib" > "$s/controls-$variant.log" 2>&1
done
python3 tools/emulation/aexcompat_patches/verify_instruction_F29.py --scratch "$s" --output "$s/instructions.json"
