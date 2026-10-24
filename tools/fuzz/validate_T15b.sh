#!/bin/sh
# Serial default-regression and standard replay; run after sweep_T15b.py.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$root"
export TMPDIR="$root/orchestra/state/T15b-odd-even-random-comp-sweep"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
for plugin in "$@"; do
 python3 tools/fuzz/verify_sizes_T15b.py "$plugin" > "$TMPDIR/$plugin-default-regression.log" 2>&1
 maximum=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["maximum"])' "orchestra/reports/T15b-evidence/$plugin-summary.json")
 python3 tools/fuzz/run.py --plugin "$plugin" --geometry realistic --size-sampler odd-even-v1 --max-size "$maximum" --jobs 1 \
  --replay "tests/fuzz_corpus/$plugin/T15b-odd-even-realistic" \
  --scratch "$TMPDIR/replay-$plugin" --report "orchestra/reports/T15b-evidence/$plugin-replay.json" \
  > "$TMPDIR/$plugin-replay.log" 2>&1
 printf '%s default regression and both-route replay passed\n' "$plugin"
done
