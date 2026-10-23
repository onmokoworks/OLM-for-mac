#!/bin/bash
# All runs serial. Nonzero fuzz exit codes are retained for result inspection.
set -uo pipefail
cd "$(dirname "$0")/../../.."
s="$PWD/orchestra/state/F29-unicorn-sse-nan-propagation"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
variant="${1:?baseline, patched, or default}"
case "$variant" in
 default) w=$(python3 -c 'import sys; sys.path.insert(0,"tools/fuzz"); import run; print(run.default_worker())');;
 baseline) w=/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker;;
 patched) w=/Users/onmk/.cache/olm-emu/worker-F29-ssenan/aex-guest-worker;;
 *) exit 2;;
esac
for corpus in tests/fuzz_corpus/*; do
 [ -d "$corpus" ] || continue
 compgen -G "$corpus/*.json" >/dev/null || continue
 label="${corpus##*/}"
 plugin=$(python3 -c 'import json,sys,pathlib; print(json.loads(next(pathlib.Path(sys.argv[1]).glob("*.json")).read_text())["plugin"])' "$corpus")
 python3 tools/fuzz/run.py --plugin "$plugin" --jobs 1 --replay "$corpus" --worker "$w" --scratch "$s" --report "$s/$variant-$label-replay.json" --corpus "$s/unused-corpus" > "$s/$variant-$label-replay.log" 2>&1
 printf '%s %s replay exit=%s\n' "$variant" "$plugin" "$?"
done
python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$variant-olmblur-seed1.json" --corpus "$s/$variant-corpus" > "$s/$variant-olmblur-seed1.log" 2>&1
printf '%s olmblur seed1 exit=%s\n' "$variant" "$?"
