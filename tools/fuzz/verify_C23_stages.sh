#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/C23-smoother2-colorkeep-toondilate-fresh"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/test_olmsmoother2_palette_C23.py --report "$s/palette-boundary.json" > "$s/palette.log" 2>&1
"$py" tools/emulation/trace_olmsmoother2_smart_C01.py --generated --seed 2 --indices 273 --label seed2-273-before --source-ref 310b543d --scratch "$s" --worker "$w" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/trace_olmsmoother2_smart_C01.py --generated --seed 2 --indices 273 --label seed2-273-after --scratch "$s" --worker "$w" --reference-trace "$s/seed2-273-before.json" > "$s/trace-after.log" 2>&1
python3 -B tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 1 --worker "$w" --scratch "$s" --report "$s/replay.json" > "$s/replay.log" 2>&1
