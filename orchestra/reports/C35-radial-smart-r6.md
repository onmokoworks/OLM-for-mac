status: partial

summary:
- Closed PF32 defined negative-Noise-Offset and finite Rotation admissions against F32.
- Seed 1 Smart E/M/R/U: 253/0/45/2 -> 254/0/44/2 -> 255/0/43/2; seed 5: 256/0/44/0 -> 258/0/42/0 -> 258/0/42/0.
- All baseline-exact hashes retained; both milestones pass 600 sanitized Smart executions and 35 unchanged corpus rows.
- Restored Rotation's original zero-alpha RGB accumulation; independent finite-input matrix is 216/216 exact and clean.
- Two clusters closed; residual investigation continues.

facts:

FACT: Started at `7f9c2ae0`, branch `orch/C35-radial-smart-r6`. Read shared guide,
RadialBlur ledger restrictions, compatibility plan, GOTCHAS and prior radial
reports, especially C17/C26/C33 rejected hypotheses. MAIN, emulator sources,
workers, release gates and ledger remain unchanged. No worker rebuild.

FACT: F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`;
original AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Fresh CPU-emulator output supplies expectations; archived calibration is 4/6.
This is not native AE/Windows proof.

FACT: The ordinary n300 seed-1 baseline completed with 253 exact, 0 mismatch,
45 refusal, 2 uncompared. Original Smart: 275 ok / 20 reject / 5 budget.
Uncompared indices 4 and 298 both timed out at 10 seconds. These are oracle
limits, not Mac mismatches. AEX-rendered refusal counts: work budget 7,
generic world 4, Type3/NV0 4, invalid noise plane 4, Zoom profile 2, host
checkout 1. Work budget was neither bypassed nor changed.

FACT: C11 retained the PF32 negative-phase gate because its Gaussian expf
boundary failed the previous worker. Removing that gate in scratch preserves
the existing noise generator's signed-index validation. The all-depth matrix
covers two geometries, two MT seeds, both blur modes, six negative phase
positions including both sides of the independently computed valid-index
boundary, and three byte-stride layouts. All 144 references / 432 layouts
pass: 96 defined inputs / 288 exact layouts and 48 invalid-index inputs /
144 clean refusals. No invalid table read is promoted.

FACT: First matrix execution completed all 432 numerical checks but its optional
PNG trace failed: F32 rejects `param_18@18:angle` syntax. The verifier now has
explicit worker selection and an optional matrix-only mode. The completed
matrix-only rerun passes. No claim of a fresh F32 negative-angle plane trace
is made. The C11 trace is historical evidence, not relabeled as a new run.

| Check | Before | Negative-phase candidate |
|---|---:|---:|
| Seed 1 Smart E/M/R/U | 253/0/45/2 | 254/0/44/2 |
| Seed 5 Smart E/M/R/U | 256/0/44/0 | 258/0/42/0 |
| Existing exact hashes retained | 509 | 509 |
| Sanitized candidate Smart executions | — | 600 clean |
| Corpus Smart exact / complete saved matches | 35 / 35 | 35 / 35 |

FACT: Newly admitted cases: seed 1 index 202; seed 5 indices 110 and 264.
The latter is C11's retained negative-phase counterexample and now matches.
All three hashes match freshly rendered original-AEX references. Still-refused
error changes are recorded separately. Corpus before/after complete result
hash is `a17e514cdfd8d2ad776d83eb9ad33bc2467004ccb1ab84e8cd6ac74ab81bbb36`;
no corpus expectations changed.


Second cluster — finite Rotation:

FACT: The unchanged C33 finite-admission counterexample (independent matrix
index 44, PF32 3x5) differs in 3 words / 6 bytes; first word 25 (pixel 6 red),
AEX `0000803f`, Mac `00000000`. A new lossless typed diagnostic captures the
port's normalized four taps and fractional coordinates before inverse sampling.
Original import-free RVA `0x1000` is called on exactly those bytes; a constant
RGBA fractional-coordinate ABI control passes. No worker rebuild or PNG
conversion is used.

FACT: At pixel 6, weighted alpha underflows to zero. The original inverse
operation returns RGB `0000c07f 0000c07f 0000c0ff`, alpha `00000000`; the
old port returns four zero words. The original disassembly accumulates all
four taps before testing alpha and conditionally taking its reciprocal. The
port's alpha check skipped the whole RGB accumulation. The fix moves that
operation back under the strict AEX sampler path, retaining reciprocal=1
when alpha is zero. The original writer remains unchanged. The independent
matrix with this correction and finite Rotation admission passes 72 references /
216 sanitized layouts, including all three formerly failing subnormal inputs.

FACT: This is an isolated inverse-operation boundary, NOT proof that every
upstream native plane matches. Python AexLoader's unpatched Unicorn still
returns differing NaN signs at pixels 3 and 6 after correction; these differences
are preserved in evidence (not treated as bit-exact). Full public F32 output for
index 44 is exactly equal after correction, as are all 216 independent layouts.
No imported-math cause is inferred from the NaN-sign diagnostic.

| Rotation check | Before | After |
|---|---:|---:|
| Seed 1 Smart E/M/R/U | 254/0/44/2 | 255/0/43/2 |
| Seed 5 Smart E/M/R/U | 258/0/42/0 | 258/0/42/0 |
| Prior exact hashes preserved | 512 | 512 |
| Sanitized campaign executions | — | 600 clean |
| Corpus complete saved matches | 35 | 35 unchanged |

FACT: Seed-1 index 220 (HDR Rotation) becomes exact. No other campaign result
regresses. The normalized-tap diagnostic on final production still matches
index 44's full original output. Corpus complete-result hash remains
`a17e514cdfd8d2ad776d83eb9ad33bc2467004ccb1ab84e8cd6ac74ab81bbb36`.


inference:

INFERENCE: Current F32/UCRT evidence supports removing the historical PF32-only
negative-phase restriction. This is a general depth admission change, with the
noise table domain and resource limits retained. It is bounded evidence, not
proof over every representable input.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: PF32 negative-phase admission; restore zero-alpha inverse accumulation and admit finite Rotation.
- `tools/fuzz/probe_radialblur_C35.py`: scratch admission, sanitized campaigns and replay.
- `tools/fuzz/verify_radialblur_negative_C11.py`: select worker; allow matrix-only verification.
- `tools/fuzz/summarize_radialblur_C35.py`: compact measurements and hash transitions.
- `tools/fuzz/trace_radialblur_inverse_C35.py`: lossless typed inverse-operation diagnostic for subsequent residual investigation.
- `orchestra/reports/C35-radial-smart-r6.evidence.json` and this report.

verify:

Run from this worktree. Use a fresh state directory; experiment outputs must
not already exist. All campaigns use jobs 1 internally.

```sh
S="$PWD/orchestra/state/C35-radial-smart-r6/recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
B=7f9c2ae0
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$S/base-build" --corpus "$S/corpus" --report "$S/current.json" > "$S/current.log" 2>&1
"$PY" tools/fuzz/probe_radialblur_C35.py --experiment negative-phase --source-revision "$B" --output "$S/negative-matrix-final" > "$S/matrix.log" 2>&1
python3 tools/fuzz/probe_radialblur_C35.py --experiment production --source-revision "$B" --seed 5 --output "$S/base-seed5" > "$S/base5.log" 2>&1
python3 tools/fuzz/probe_radialblur_C35.py --experiment production --admission-campaign "$S/base-seed5/campaign.json" --output "$S/negative-seed5" > "$S/after5.log" 2>&1
python3 tools/fuzz/probe_radialblur_C35.py --experiment production --replay tests/fuzz_corpus/radialblur --output "$S/corpus-negative" > "$S/corpus.log" 2>&1
git diff --check
```

Expected matrix: 144 references, 432 clean passing layouts, zero failures.
Seed 5: 258/0/42/0; corpus: 35/35 complete saved matches. Seed-1 counts depend
on original wall timeouts; never count an unrendered original as exact. The
original seed-1 baseline command above was run at starting source with
`--report .../base.json`; both candidate campaigns reused its input/hash-bound
references with `--experiment negative-phase --admission-campaign ...`.

next:
- Negative-phase cluster commit: `c9d863c1`; second cluster is the finite Rotation correction.
- Type3 missing-layer allocation/prepass, nonfinite Zoom, and host checkout
  remain separate boundaries. Work-budget and invalid-index refusals remain.

Second-cluster reproduction, from the negative-phase commit:

```sh
python3 tools/fuzz/probe_radialblur_C35.py --experiment rotation-zero-alpha --source-revision c9d863c1 --output "$S/rotation-matrix" > "$S/rotation-matrix.log" 2>&1
python3 tools/fuzz/probe_radialblur_C35.py --experiment production --admission-campaign "$S/negative-seed5/campaign.json" --output "$S/rotation-seed5" > "$S/rotation5.log" 2>&1
"$PY" tools/fuzz/trace_radialblur_inverse_C35.py --output "$S/inverse-production" > "$S/inverse.log" 2>&1
python3 tools/fuzz/probe_radialblur_C35.py --experiment production --replay tests/fuzz_corpus/radialblur --output "$S/corpus-rotation" > "$S/corpus2.log" 2>&1
```

Expected: 216 exact/clean independent layouts, zero campaign failures, index-44
public diff 0 words, 35 unchanged corpus results. The isolated Python leaf
replay deliberately reports two NaN-sign differences; it does not override the
full F32 oracle. Original candidate campaigns used each retained negative-phase
campaign as `--admission-campaign` and `--experiment rotation-zero-alpha`.
