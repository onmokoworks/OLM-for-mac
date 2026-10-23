#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
s="$PWD/orchestra/state/F32-smoother-oracle-deep-pixels"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
worker="$HOME/.cache/olm-emu/worker-F32-deep/aex-guest-worker"
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
python3 tools/emulation/aexcompat_patches/validate_F32.py > "$s/verify-corpora.log" 2>&1
"$py" tools/emulation/aexcompat_patches/probe_F32_hosts.py > "$s/verify-hosts.log" 2>&1
"$py" tools/emulation/aexcompat_patches/probe_F32_deep.py > "$s/verify-deep.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --worker "$worker" --scratch "$s/verify" --budget-minutes 30 --report "$s/verify-seed1.json" --corpus "$s/verify-corpus" > "$s/verify-seed1.log" 2>&1
python3 tools/fuzz/replay_olmsmoother_sanitized.py --plugin olmsmoother --replay tests/fuzz_corpus/olmsmoother --jobs 1 --worker "$worker" --scratch "$s/verify-sanitized" --budget-minutes 30 --report "$s/verify-sanitized.json" > "$s/verify-sanitized.log" 2>&1
"$py" tools/fuzz/compare_olmsmoother_classifier8.py --jobs 1 --worker "$worker" --scratch "$s/verify-classifier" --corpus tests/fuzz_corpus/olmsmoother/seed1_case000006_92552f06afe6.json --corpus tests/fuzz_corpus/olmsmoother/seed1_case000000_eaba52d5eacc.json --owner-corpus tests/fuzz_corpus/olmsmoother --report "$s/verify-classifier.json" > "$s/verify-classifier.log" 2>&1
python3 - <<'PY'
import json
from pathlib import Path
s=Path('orchestra/state/F32-smoother-oracle-deep-pixels')
def read(n):return json.loads((s/n).read_text())
d=read('verify-seed1.json');assert d['completed']==300
for route in ('classic','smart'):
 assert d['summary'][route+'_exact']==205 and d['summary'][route+'_refusal']==95
 assert not d['summary'].get(route+'_mismatch',0) and not d['summary'].get(route+'_uncompared',0)
d=read('verify-sanitized.json');assert d['completed']==29
assert all(all(r['status']=='exact' for r in x['result']['routes'].values()) for x in d['replays'])
d=read('corpus-differential.json');assert d['total']==679 and d['changed']==0
print('PASS: seed1 E/M/R/U 205/0/95/0; sanitized 29 exact; non-Smoother 679 unchanged')
PY
git diff --check
