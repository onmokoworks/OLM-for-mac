#!/bin/bash
# Repeat T12 without changing production admission or retained corpus files.
set -euo pipefail
cd "$(dirname "$0")/../.."
s="$PWD/orchestra/state/T12-triage-colorkeep-colorkey/verify"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
export ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=halt_on_error=0
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_HOST_FLAGS OLM_COLOR_TRIAGE_SANITIZE OLM_COLOR_TRIAGE_NO_TRACE
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
for p in colorkeep olmcolorkey; do
  for mode in before trace bypass sanitize-default sanitize-bypass; do
    export OLM_COLOR_TRIAGE_NO_TRACE=0 OLM_COLOR_TRIAGE_BYPASS=0 OLM_COLOR_TRIAGE_SANITIZE=0
    case "$mode" in
      before) export OLM_COLOR_TRIAGE_NO_TRACE=1 ;;
      bypass) export OLM_COLOR_TRIAGE_BYPASS=1 ;;
      sanitize-default) export OLM_COLOR_TRIAGE_SANITIZE=1 ;;
      sanitize-bypass) export OLM_COLOR_TRIAGE_BYPASS=1 OLM_COLOR_TRIAGE_SANITIZE=1 ;;
    esac
    python3 tools/fuzz/triage_colors_T12.py --target-only --plugin "$p" --n 300 --seed 1 --jobs 2 \
      --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/$mode-$p.json" \
      --corpus "$s/$mode-$p-corpus" > "$s/$mode-$p.log" 2>&1
    tail -1 "$s/$mode-$p.log"
  done
done
unset OLM_COLOR_TRIAGE_BYPASS OLM_COLOR_TRIAGE_SANITIZE OLM_COLOR_TRIAGE_NO_TRACE
OLM_COLOR_TRIAGE_HOST_FLAGS=1 python3 tools/fuzz/triage_colors_T12.py --target-only --plugin colorkeep \
  --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --worker "$w" --scratch "$s" \
  --report "$s/host-colorkeep.json" --corpus "$s/host-colorkeep-corpus" > "$s/host-colorkeep.log" 2>&1
python3 tools/fuzz/triage_colors_T12.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey \
  --jobs 2 --worker "$w" --scratch "$s" --report "$s/replay-olmcolorkey.json" \
  --corpus "$s/replay-corpus" > "$s/replay-olmcolorkey.log" 2>&1
# ColorKeep has no historical saved cases: make a complete seed-1 snapshot.
python3 tools/fuzz/analyze_colors_T12.py --scratch "$s" --output "$s/evidence.json" \
  --jobs 2 --worker "$w" > "$s/analyze.log" 2>&1
python3 tools/fuzz/triage_colors_T12.py --target-only --plugin colorkeep \
  --replay "$s/colorkeep-neutrality-corpus" --jobs 2 --worker "$w" --scratch "$s" \
  --report "$s/replay-colorkeep-300.json" --corpus "$s/replay-corpus" > "$s/replay-colorkeep-300.log" 2>&1
python3 - "$s" <<'PY'
import json, sys
from pathlib import Path
s = Path(sys.argv[1])
fresh = json.loads((s/'evidence.json').read_text())
saved = json.loads(Path('reports/fuzz/colors_T12.json').read_text())
for plugin in ('colorkeep','olmcolorkey'):
    a,b = fresh['plugins'][plugin], saved['plugins'][plugin]
    assert a['neutrality'] == b['neutrality'] == 300
    assert a['guards'] == b['guards']
    # Ignore source line numbers: compare the actual Smart result dictionaries.
    for x,y in zip(a['baseline'], b['baseline']):
        for key in ('index','input_sha256','oracle','candidate'):
            assert x[key] == y[key], (plugin, x['index'], key)
    for mode in b['campaigns']:
        for key in ('total','previously_refused','sanitizer_rows','refused_sanitizer_rows','candidate_errors'):
            assert a['campaigns'][mode][key] == b['campaigns'][mode][key], (plugin,mode,key)
    print(plugin, '300/300 unchanged; guards and gate-off/sanitizer counts reproduced')
assert fresh['witnesses'] == saved['witnesses']
for plugin, count in (('olmcolorkey',3),('colorkeep-300',300)):
    replay = json.loads((s/f'replay-{plugin}.json').read_text())
    assert len(replay['replays']) == count and all(r['matches_saved'] for r in replay['replays'])
    print(plugin, f'{count}/{count} matches_saved')
PY
