status: partial

summary:
- Closed the off-frame Center admission cluster for PF8 Zoom/Rotation and PF16 Zoom.
- Seed 1 Smart 198/0/102 -> 229/0/71 exact/mismatch/refusal; seed 5 197/0/103 -> 219/0/81.
- All 395 baseline-exact campaign hashes and all 35 exact corpus hashes are retained.
- 600 sanitized campaign replays and 324 independent padded-layout renders are clean; eight existing tests pass.
- Continuing the ticket loop; broad PF32 finite-input admission is experimental and is not promoted.

facts:

FACT: Resumed on `fa33a5f8`, with uncommitted C11 work. HEAD RadialBlur source SHA256
`e65fd8add8bc886365a3e8aebd24fe9d0c1cd710159aabbcc6f5a20b3f11d0a1` matches the retained
`before.json` and `before5.json` campaigns. Verified candidate source SHA256
`9870a5c3c9ce4ac0d59374e71db52068e716da685f24fc716a26770da2327b21` matches both the resumed
seed-1 measurement and retained seed-5 measurement, then all 600 outputs were independently
replayed with ASan/UBSan. No permission rejection, MAIN/cache/emulator write, worker rebuild,
release-gate edit, ledger edit, installation, push, history rewrite or `/tmp` scratch write.

FACT: Pinned original AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`;
worker `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`,
SHA256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
Existing adapter calibration is 4/6 against its older archived samples; public Smart outputs
from this pinned worker, rather than those stale PF32 hashes, supply campaign expectations.
These are CPU emulation / SDK fake-host results, not native AE, native Windows UCRT or GPU claims.

FACT: The original-renderable baseline refusal census was generic world 42, Zoom profile 26,
budget 5, Type3 zero noise 4, Rotation profile 3 and host checkout 1. The first selected cause
was the generic world's in-frame-only Center gate. The retained unrestricted-center experiment
measured seed 1 241 exact / 1 mismatch / 58 refusal and seed 5 238 / 2 / 60; it is not promoted.
The independent all-depth matrix additionally exposes PF16 Rotation and PF32 residuals.
The admitted rule retains those depth/family restrictions and requires representable signed
16.16 Center values. No case, coordinate, output hash or expected value enters production.

FACT: Seed-1 case 67 (11x8 PF8 Rotation, center 5.5186920166015625,13.846389770507812)
first differs at radial dimensions: original 1800x14, gate-only Mac 1800x17. Original Rotation
1BB0 and Zoom A8F0 use FLOAT32 axis distances/squares/sqrt, integer half-extent selection and
integer radius truncation before Ratio division (Rotation caller 481B..4849). Generic Rotation
now uses the already grounded shared radius helper. Afterward polar/scalar/span/accum/max/normalized
all have zero differing words, including 100800-word RGBA planes. The resumed trace independently
reproduced all six exact stages and binds both instrumented final outputs to the public Smart
oracle. Earlier incomplete traces used radius_count without the inclusive endpoint; only the
corrected `*-full` reports are acceptance evidence.

| Campaign | Before E/M/R | After E/M/R | Baseline exact hashes retained |
|---|---|---|---:|
| Seed 1, n300 | 198/0/102 | 229/0/71 | 198 |
| Seed 5, n300 | 197/0/103 | 219/0/81 | 197 |
| Saved corpus, 35 Smart rows | 35/0/0 | 35/0/0 | 35 |

FACT: Corpus replay is 35/35 `matches_saved`; Classic results also remain identical in the
corpus. Rebaseline table is 35 exact->exact and zero changed rows; no corpus mutation needed.
Campaign Classic remains outside F18's target and has many mismatches against the per-route
Classic oracle. It is not called exact or used to justify these Smart admissions.
The 53 newly admitted Smart cases are all original-renderable and exact. Sanitizer replay:
600/600 same and clean. Independent Center matrix: 3 geometries x 3 admitted depth/family
pairs x 12 Center/control variants = 108 original references, each with packed and two odd
padding layouts = 324 exact, clean renders. Existing smoke tests 8/8; `git diff --check` passes.
Machine evidence: `C11-centers.evidence.json`, `C11-centers-trace.evidence.json`.

inference:

INFERENCE: Off-frame Center is not by itself an unsupported algorithm. The old generic
predicate hid already working Zoom/PF8 Rotation behavior, while Rotation's mathematical
radius bound did not reproduce the AEX operation. Correcting that shared operation plus
limiting admission to independently exact depth/family combinations closes this cluster.
The rejected all-depth matrix is new boundary evidence, not justification to tune final bytes.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: Center admission and original Rotation radius operation.
- `tests/test_olmradialblur_generic_baseline_20260820.py`: representable Center boundary checks.
- `tools/fuzz/probe_radialblur_smart_C11.py`: scratch-only source experiments.
- `tools/fuzz/trace_radialblur_rotation_C11.py`, `tools/fuzz/fixtures/radialblur_rotation_C11.json`: paired original trace.
- `tools/fuzz/verify_radialblur_smart_C11.py`: independent matrices.
- `tools/fuzz/verify_radialblur_smart_C06.py`: allow other ticket scratch roots.
- `orchestra/reports/C11-centers*.json` and this report: evidence and audit.

verify:

Run in this worktree; output directories for trace must be fresh. These are the commands
used on resume (paths below use a fresh prefix for review):

```sh
S="$PWD/orchestra/state/C11-radial-smart-r2/recheck"
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
W=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
mkdir -p "$S"
export TMPDIR="$S"
"$PY" -u tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --case-timeout 30 --budget-minutes 120 --shrink-attempts 0 --shrink-seconds 0 --worker "$W" --scratch "$S/fuzz" --corpus "$S/corpus" --report "$S/fuzz.json" > "$S/fuzz.log" 2>&1
"$PY" -u tools/fuzz/verify_radialblur_smart_C11.py --evidence orchestra/reports/C11-centers.evidence.json --independent --smoke --output "$S/verify" > "$S/verify.log" 2>&1
"$PY" -u tools/fuzz/trace_radialblur_rotation_C11.py --fixture tools/fuzz/fixtures/radialblur_rotation_C11.json --output "$S/trace" > "$S/trace.log" 2>&1
"$PY" -u tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 2 --case-timeout 30 --budget-minutes 60 --worker "$W" --scratch "$S/replay" --report "$S/replay.json" > "$S/replay.log" 2>&1
git diff --check
```

Expected on this milestone: 229/0/71 seed-1 Smart; 600 identical clean replay results;
324 exact clean matrix renders; 8 smoke tests pass; all six paired planes exact;
35/35 corpus saved expectations match. AEX wall-time budgets may vary only on refused cases.
For seed 5 use the same campaign arguments with `--seed 5`: expected 219/0/81.

next:
- Continue the ticket loop on the remaining generic-world refusals; broad finite PF32 input
  experimentation has no campaign mismatches but the independent matrix found Rotation
  residuals, so it is not promoted.
- PF32 off-frame Zoom has an observed Gaussian table import boundary; preserve its refusal
  and document the external math dependency separately before any admission.
