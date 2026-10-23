status: done

summary:
- Restore the original five-tap Gaussian symmetric scalar tail and admit directional Alpha Length1.
- Seed1 Smart258/0/42→260/0/40; fresh seed11 267/0/33→268/0/32.
- Previous Smart exact and all Classic records persist; saved corpus expectations and samples are unchanged.
- Independent288 conditions,600 sanitized campaign renders,70 corpus inputs and retained66 Gaussian conditions pass.

facts:

Base `3dacf4ae`. Evidence: `reports/fuzz/olmkirakira_smart_C22_length1.json`. All n300 campaigns use jobs1, no shrinking, and ticket-local corpus/scratch. Original AEX/worker identities are unchanged from the approximation report. Original Smart output/reject is287/13 for seed1 and292/8 for seed11. New exact indices: seed1 11,123; seed11 273.

The retained C04 PF32 9×7 Length1 witness has input SHA256 `c3cc70ed4a7d57f6c836e5ae6d4fe5ce872d83595b3c6ffd24b5b588f58677b9`. Before, its one final word differs at217 (`5cf1563f` original versus `5df1563f`). Extended original/Mac Gaussian tracing identifies the first differing helper operation: fourth ray, Gaussian output, word132 of a15×15 workspace (`7369c63c` versus `7269c63c`), three words total. Source, seed, forward warp and previous rays are exact. The original trace binds byte-for-byte to public Smart.

Original SSE4.1 constructor `1812e5880` selects vtable `181536f70`, whose row body is `1812f9a70`. Runtime hooks record24 kernel5/width13/channel1 calls and30 kernel5/width15/channel1 calls. The original five-tap symmetric tail forms adjacent pairs and the center product, then adds the outer pair product; the final single sample uses the same symmetric sum. The port incorrectly fell through to five independent products after its vector-width prefix. Recovering the symmetric tail fixes all12 paired helper stages, all full planes and final bytes. No coefficient, coordinate or output-value adjustment is made.

The generic `HorizontalGaussian` operation is corrected, including existing owners. Tiny scalar Alpha workspace admission extends from Length≥2 to Length≥1; source/percentage/aggregation recovery and Smart's existing Gaussian budget accept that same directional domain. Highlight, approximation and non-Alpha Gaussian owners remain excluded from this additional rule. All prior finite SDR, layout, default-ramp/color and control limits persist. Classic admission is unchanged.

Gate-off independent controls:288/288 exact under ASan/UBSan. Final production repetition:288/288 exact. Seven one-away negative cases refuse. The final public-bound retained counterexample is exact through every paired helper/full stage. Original Gaussian66-case regression retains497250/497250 exact words. Existing25 fast tests pass; compiled generic sanitizer passes54 rows includingHD in45.648s. The final campaign verifier independently rerenders600 Smart conditions under ASan/UBSan. The70-input corpus verifier and140-route sample audit pass; changed samples=0. Strict production replay8/8; no rebaseline edits.

Before-source audits explicitly include a scratch copy of the **old Gaussian header**, preventing a false before/after comparison against the new operation at both revisions. Header hashes are retained in machine evidence. No reference-worker rebuild or numerical detour. `git diff --check` passes.

inference:

The original symmetric row body and first divergent Gaussian plane establish the operation, with independent controls/retained regressions supporting the bounded admission. This is not native AE/UCRT, nonfinite/HDR, Highlight, custom-ramp, ROI/downsample or full-plugin proof.

changed_files:
- `core/kirakira_gaussian.h`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `reports/fuzz/olmkirakira_smart_C22_length1.json`
- `orchestra/reports/C22-kira-smart-r5{,-length1}.md`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C22-kira-smart-r5/recheck-length1"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 3dacf4ae:core/kirakira_gaussian.h > "$s/before.h"
git show 3dacf4ae:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
python3 - "$s" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]);p=s/'before.cpp'
p.write_text(p.read_text().replace('#include "../../core/kirakira_gaussian.h"','#include "'+str(s/'before.h')+'"'))
PY
for seed in 1 11; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus-$seed" > "$s/before-$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus-$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-one-controls --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-one-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 11 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py > "$s/retained66.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_smart_C07.py --family gaussian-length1 --trace-index 24 --require-exact --scratch "$s/trace" --report "$s/trace.json" > "$s/trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: campaign counts above;288 exact matrix;7 refusals;600 sanitized campaign routes and70 corpus inputs pass;140 routes unchanged;66 retained cases exact; public-bound all-stage exact trace;8/8 replay. The trace with `--source "$s/before.cpp" --gate-off` instead of `--require-exact` reproduces the first Gaussian and final differences.

next:
- Two clusters closed. Seed1 remaining40 =13 original rejects +27 successful-oracle refusals.
- Largest residual parameter family is approximation10, followed by Gaussian9. Continue scalar brightness/max approximation; retain other constructors, Highlight and non-SDR/nonfinite boundaries.
