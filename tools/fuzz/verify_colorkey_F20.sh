#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/F20-colorkey-zero-color-and-byte-safe/verify"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 ASAN_OPTIONS=detect_leaks=0
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_SANITIZE OLM_COLOR_TRIAGE_NO_TRACE
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
py="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python"
base=9bdbc01e437f2367c21b3a2a9621f4585802c553
for mode in before sanitize-before after sanitize-after; do
  runner=(python3 tools/fuzz/run.py)
  if [[ "$mode" == *before ]]; then
    runner=(python3 tools/fuzz/run_colorkey_revision_F20.py --source-ref "$base")
  fi
  export OLM_COLOR_TRIAGE_SANITIZE=0 UBSAN_OPTIONS=halt_on_error=0
  [[ "$mode" != sanitize-* ]] || export OLM_COLOR_TRIAGE_SANITIZE=1
  [[ "$mode" != sanitize-after ]] || export UBSAN_OPTIONS=halt_on_error=1
  "${runner[@]}" --plugin olmcolorkey --n 300 --seed 1 --jobs 2 --shrink-attempts 0 \
    --worker "$w" --scratch "$s/$mode" --report "$s/$mode.json" --corpus "$s/$mode-corpus" > "$s/$mode.log" 2>&1
  tail -1 "$s/$mode.log"
done
unset OLM_COLOR_TRIAGE_SANITIZE
python3 tools/fuzz/run_colorkey_revision_F20.py --source-ref "$base" --plugin olmcolorkey \
  --replay tests/fuzz_corpus/olmcolorkey --jobs 2 --worker "$w" --scratch "$s/replay-before" \
  --report "$s/replay-before.json" --corpus "$s/replay-corpus" > "$s/replay-before.log" 2>&1
code=0
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --jobs 2 \
  --worker "$w" --scratch "$s/replay-after" --report "$s/replay-after.json" \
  --corpus "$s/replay-corpus" > "$s/replay-after.log" 2>&1 || code=$?
# Historical corpus results intentionally remain mismatches; exact improvements
# therefore produce replay exit 1. The summarizer checks every changed row.
[[ "$code" == 1 ]]
"$py" tools/fuzz/probe_colorkey_stages_F20.py --worker "$w" --scratch "$s/stages" \
  --output "$s/stages-after.json" --require-exact > "$s/stages.log" 2>&1
"$py" tools/fuzz/trace_colorkey_alpha_F20.py --output "$s/alpha-trace.json" > "$s/alpha-trace.log" 2>&1
python3 tools/fuzz/check_colorkey_boundaries_F20.py --worker "$w" --scratch "$s/boundaries" \
  --output "$s/boundaries.json" > "$s/boundaries.log" 2>&1
python3 tools/fuzz/test_colorkey_existing_F20.py > "$s/tests.log" 2>&1
python3 tools/fuzz/summarize_colorkey_F20.py --scratch "$s" --output "$s/evidence.json"
