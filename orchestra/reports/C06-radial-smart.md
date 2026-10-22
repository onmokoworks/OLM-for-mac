status: done

summary:
- Closed three Smart clusters: typed-input alignment, full signed-16.16 Angle admission, and Repeat Border scalar-field dispatch (including its discovered Zoom radius boundary).
- Seed 1 Smart exact 108→168→187→198; mismatch stays 0; refusals 192→102.
- Fresh seed 3 exact 113→166→176→190; its one pre-existing mismatch is unchanged. Every prior exact hash is preserved.
- Final acceptance: 600 clean sanitized campaign replays, 300 original inputs/900 exact layout renders, two complete paired traces, eight smoke tests.
- Corpus 35/35 stays unchanged. Three separate commits close the ticket loop; remaining plugin gaps are explicitly retained.

facts:

Base `ad206f00`, branch `orch/C06-radial-smart`. Read AGENT_GUIDE, the RadialBlur ledger row, compatibility plan, GOTCHAS, T01/T03/T05/F08/F13/F18 and F10/F12 methodology. MAIN, original AEX, SDK, emulator sources and cache were read-only. No release gate, ledger, installation, worker build, push, history rewrite, or `/tmp` writes.

Reference worker: `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`, SHA256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`. Original AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`. Starting source SHA256 `347c9fd41c3ca6fcc9146efd5b60b5985e86c0c34b31d0309ef488847f01e2db`; alignment source `1d7374fc4fc07f5b5e55517cde3b552d5186bcb957f0d5f6b8da295e7084022e`.

All campaigns used MAIN `tools/emulation/.venv/bin/python`, `tools/fuzz/run.py --plugin radialblur --n 300 --seed {1,3} --jobs 2 --case-timeout 30 --budget-minutes 120 --worker <worker>`, with separate `--scratch`, `--corpus`, and `--report` below `orchestra/state/C06-radial-smart`. The first baseline used default shrinking; later diagnostic campaigns used `--shrink-attempts 0 --shrink-seconds 0` because Classic mismatch reduction is unrelated to the target Smart route. Every subprocess log was redirected there.

| Campaign | Smart exact | mismatch | refusal | Original Smart ok/reject/budget |
|---|---:|---:|---:|---|
| Seed 1 before | 108 | 0 | 192 | 279/20/1 |
| Seed 1 alignment | 168 | 0 | 132 | 279/20/1 |
| Seed 3 before | 113 | 1 | 186 | 279/18/3 |
| Seed 3 alignment | 166 | 1 | 133 | 280/18/2 |

The original-renderable baseline refusals were Zoom profile 86, generic world 62, Rotation profile 12, Type3 zero noise 5, two-stage 2, Smart budget 2, Zoom noise/inner 1, and host 1. A six-tag gate-off experiment completed 300 cases: Smart 132 exact / 144 mismatch / 14 refusal / 10 uncompared. No bypass is enabled in production. Of the 60 seed-1 promotions, 26 previously hit Zoom profile, 33 generic world and one Zoom noise/inner. This is one storage/dispatch cause spanning three guard labels, not three independently closed algorithms.

Smart already stages its destination but passed the original byte-strided input directly to typed admission/render code. `IsGenericBaselineWorldPair` rejected odd typed rowbytes; fallback probes also bound misaligned references before refusing. The new source byte-copies active input rows into PF16 or PF32 vectors when the base address or rowbytes needs alignment. No-op byte copies retain their original path. Original overlap/full-frame/format checks and checkins still refer to the checked-out worlds. Publication remains atomic. The generic budget includes the additional input allocation; the existing budget test now checks its exact byte increment.

An initial generic-controls-only staging experiment had 300/300 identical seed-1 outcomes, but sanitizer reported misaligned PF16 reference bindings in refused cases 123, 173 and 235 at the size-factor input probe (line 1726). Applying staging before all Smart typed probes removed these reports. Final separately compiled O2 and ASan/UBSan executables reproduce all 600 campaign outcomes/hashes; all 600 sanitizer replays are clean. The independent matrix is two geometries × PF16/PF32 × Zoom/Rotation × three active strength/offset/fade profiles, with packed, 1/5-byte, and 3/11-byte input/output padding: 24 original Smart references, 72 exact sanitized Mac renders. Input/padding preservation and checkout/checkin checks are enforced by the existing harness.

Seed 3 index 46 is a **pre-existing** Smart mismatch, unchanged in both builds: three words/three bytes, first word 1031 (byte 4124), original `66a7df3e`, Mac `67a7df3e`; Mac SHA256 `66f28d337094f38b0a8096208c20e10d22ae38833192b214070e0e6d1ad388f3`. This is not included among newly admitted cases or called exact.

Corpus replay before/after: 35/35 `matches_saved`, all 35 Smart exact hashes unchanged; Classic results also unchanged. Rebaseline table: 35 exact→exact, zero changed rows. Eight existing RadialBlur generic baseline, sanitizer, budget, Type3, Smart contract, size/noise and typed geometry tests pass. `git diff --check` passes. Machine evidence is `C06-alignment.evidence.json`, including input hashes, complete transitions, source/reference bindings, sanitizer outcomes and smoke results. The final typed-buffer source was independently replayed against both measured campaigns in ordinary and sanitized builds; their intermediate source identities remain explicitly recorded rather than overwritten.

Angle milestone (second commit): production now admits the signed 16.16 AD getter domain `[-32768,32768)` instead of an arbitrary ±360-degree subset. `InfoFromParams` divides the original signed fixed value by 65536; no angle normalization, trigonometric operation, rounding, or output writer changed. The existing fixed-radian transform executes for newly admitted profiles.

| Campaign | Smart before E/M/R | Smart after E/M/R | retained exact |
|---|---|---|---:|
| Seed 1 | 168/0/132 | 187/0/113 | 168 |
| Seed 3 | 166/1/133 | 176/1/123 | 166 |

All 29 admissions are original-renderable and exact. Seed-3 cases 116, 263 and 274 remain refused but now reach the generic resource-budget return (error 516→4); the audit records these diagnostic changes separately. Corpus comparisons still require exact saved results. Both campaigns completed 300 cases. The independent angle matrix covers 3×5 and 11×7, all three depths, Zoom/Rotation, Ratio 1/2.25 and ten angles: both signed fixed endpoints, the neighbor of the negative endpoint, ±720, ±360 and the adjacent fixed value outside each one-turn boundary, and zero. All 240 original Smart references and 720 sanitized Mac layout renders match. The 600 sanitized campaign replays are identical and clean. The inherited seed-3 index-46 mismatch is unchanged. The first smoke pass failed only the stale rejection of Angle 360.01; the test now accepts 360+1/65536 and rejects the unrepresentable +32768. The rerun passes 8/8. Corpus 35/35 remains unchanged. Evidence: `C06-angle.evidence.json`; final Angle source SHA256 `9e7d4d4f3455ae41a3ffb04e05f2249b75de9607e8d660193ed49629ce84c0af`.

The Angle evidence uses the same worker and campaign commands, with scratch/report prefixes `angle` and `angle3`. Final verification command was `verify_radialblur_smart_C06.py --campaign orchestra/state/C06-radial-smart/angle.json --campaign orchestra/state/C06-radial-smart/angle3.json --independent --matrix angles --smoke --output orchestra/state/C06-radial-smart/angle-final-verified`, with its output redirected to the matching log. No Angle experiment was promoted until the fresh seed and boundary matrix passed.

Repeat Border milestone (third commit, after `a4cbffd2`): a gate-only experiment completed seed-1/300 with 190 exact / 8 mismatch / 102 refusal. That candidate was **not** promoted. The selected PF8 seed-1 case 163 shrinks to 2×1, Inner Strength 4 and Repeat Border off. The instrumented Mac output is required to equal the production Smart output; the original trace output is required to equal the public Smart oracle and the saved fixture hash.

First divergence: polar RGBA and eligibility agree, but the span plane differs in 5,209/7,200 words. At word 1, original `00000000`, Mac `0000803f`; preaccum/premax still agree, then accum differs in 2,396 words and normalized in 1,339. The final reduced output differs at byte 2: original `44`, Mac `43`. Direct disassembly of the hash-bound original AEX shows `5984..59B6` selecting scalar sampler A550 when Repeat Border is zero, versus A6A0 for repeat. Calls at 5B04 and 5B34 use that same selected sampler for the span and enabled size/fade field. Rotation's `49CC..49FF` similarly selects 1800 versus 1950. The generic Zoom/Rotation path now makes that scalar sampler choice along with its existing color-sampler choice. No final sampling/writer bias is added. All eight paired planes and final output then match; reduced output SHA256 `38c6c77ae3ede82b7bef3424cd2f55527ed8894826a53f92836b4669b078bfc6`.

The first independent matrix found one further input boundary, rather than declaring seed success sufficient: 1×1 PF8 input `ff239014`, center (0.25,0.75), outer Strength 4, fades 25/50, Size 25, Noise 100/Type2/Seed89. Original alpha is `ff`, intermediate candidate `ae`, with all three padding layouts clean but mismatching. The original polar dimensions are 3×1800, Mac 4×1800. Original A8F0 at A94B..A965/A975..A989 chooses the far axis by comparing the center to **integer extent/2**; A98C..A9C2 uses FLOAT32 squares/add/sqrt and integer truncation. The port used a double-precision mathematical maximum. `ZoomRadiusBoundsAEX` restores the actual operation for generic Zoom, including the caller's truncation before Ratio division. It applies to all generic dimensions/centers, with no coordinate/case lookup. The corrected dimensions, all eight paired planes and final output match. The follow-up matrix adds the exact integer-half pivot, its adjacent fixed-point values independently on each axis, and quarter-pixel offsets.

| Campaign | Smart before E/M/R | Smart final E/M/R | retained exact |
|---|---|---|---:|
| Seed 1 | 187/0/113 | 198/0/102 | 187 |
| Seed 3 | 176/1/123 | 190/1/109 | 176 |

All 25 new admissions are exact, with zero newly admitted mismatch. Seed-1 cases 48/235 and seed-3 case 33 remain refused but reach resource budget error 4 instead of profile error 516. The final source was independently compiled and replayed against all 600 saved public-oracle campaign outcomes with ASan/UBSan: 600 unchanged/clean. The final independent matrix is five geometries (1×1, 1×7, 7×1, 3×5, 11×7) × three depths × Zoom/Rotation × ten control/center profiles, each with packed and two odd padding layouts: **300 AEX references, 900 exact sanitized Mac renders**. It includes inner/outer strengths and offsets, fades, Size/Noise, both procedural Noise types, off-center positions, Ratio, multi-turn Angle and Quality. Eight existing tests pass. The final ordinary seed-1 campaign again measures 198/0/102; AEX Smart 279 ok / 20 reject / 1 budget. Fresh-seed campaign references are 281 ok / 18 reject / 1 budget; final-source hash replay preserves its 190/1/109 outcomes.

Corpus before/after: 35/35 `matches_saved`, 35 exact→exact Smart rows, unchanged Classic results, zero rebaseline changes. Final source SHA256 `e65fd8add8bc886365a3e8aebd24fe9d0c1cd710159aabbcc6f5a20b3f11d0a1`. Evidence: `C06-border.evidence.json`, `C06-border-trace.evidence.json` and `tools/fuzz/fixtures/radialblur_border_C06.json`. Trace evidence includes the original instruction bytes, source/binary bindings, reference hashes and all stage comparisons. Both rejected source experiments are reproducible through the committed trace tool's scratch-only `--experiment` options. No retained worker was rebuilt or math-import policy changed.

Final `git diff --check` passes. Final scratch measures 104,116,779 bytes, below 5 GiB; 6 remaining regenerable build directories were removed before handoff (the runners already removed their other builds). This ticket stops after three closed clusters, not at full RadialBlur compatibility.

inference:

The refusal reduction comes from restoring the input storage contract before existing general algorithms, not relaxing numerical comparisons or selecting output values. The retained original worker receives packed input; these experiments establish Mac odd-stride equivalence to that original packed render, not native Windows odd-stride support. This is bounded CPU-emulator evidence, not native AE/UCRT conformance or a claim about arbitrary remaining profiles.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tests/test_olmradialblur_generic_budget_20260821.py`
- `tests/test_olmradialblur_generic_baseline_20260820.py`
- `tools/fuzz/verify_radialblur_smart_C06.py`
- `tools/fuzz/summarize_radialblur_smart_C06.py`
- `tools/fuzz/trace_radialblur_smart_C06.py`
- `tools/fuzz/fixtures/radialblur_border_C06.json`
- `orchestra/reports/C06-alignment.evidence.json`
- `orchestra/reports/C06-angle.evidence.json`
- `orchestra/reports/C06-border.evidence.json`
- `orchestra/reports/C06-border-trace.evidence.json`
- `orchestra/reports/C06-radial-smart.md`

verify:

Run at this commit from the worktree root:

```sh
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
export TMPDIR="$PWD/orchestra/state/C06-radial-smart/recheck-border"
mkdir -p "$TMPDIR"
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/verify_radialblur_smart_C06.py \
  --evidence orchestra/reports/C06-border.evidence.json --independent --matrix border --smoke \
  --output "$TMPDIR/verify" > "$TMPDIR/verify.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/run.py --plugin radialblur \
  --n 300 --seed 1 --jobs 2 --case-timeout 30 --budget-minutes 120 \
  --worker /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker \
  --scratch "$TMPDIR/fuzz" --corpus "$TMPDIR/corpus" --report "$TMPDIR/fuzz.json" \
  > "$TMPDIR/fuzz.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/run.py --plugin radialblur \
  --replay tests/fuzz_corpus/radialblur --case-timeout 30 --budget-minutes 60 \
  --worker /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker \
  --scratch "$TMPDIR/replay" --report "$TMPDIR/replay.json" > "$TMPDIR/replay.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/trace_radialblur_smart_C06.py \
  --cases-from tools/fuzz/fixtures/radialblur_border_C06.json --indices 163,5005 \
  --output "$TMPDIR/traces" > "$TMPDIR/traces.log" 2>&1
git diff --check
```

Expected: verifier pass, 600 identical/clean Smart outcomes, 900 independent exact renders, 8/8 smoke tests; seed-1 Smart 198 exact / 0 mismatch / 102 refusal (oracle timeouts can vary); corpus 35/35 matching. The fuzz runner's nonzero status for diagnostic Classic mismatches is separate from Smart acceptance.

The trace command should report zero differences for all eight planes on both witnesses and bind both outputs to the saved original Smart hashes. To reproduce the rejected experiments, use the same trace command with `--indices 163 --revision a4cbffd2 --experiment border-gate-only` in a new output directory (5,209 span differences), or `--indices 5005 --experiment legacy-radius` (3×1800 original versus 4×1800 Mac). These switches write only scratch sources.

next:
- Suggested follow-up: split the 42 original-renderable `generic-world-not-admitted` cases. Twenty-nine have out-of-frame centers; the remaining 13 are PF32 profiles (5 signed, 6 HDR, 2 nonfinite) with centers in frame. Do not lift that gate wholesale.
- Other seed-1 original-renderable refusals: Zoom profile 26, generic budget 4, Type3 zero noise 5, Rotation profile 3, host 1. Original reject/budget rows are not exactness evidence.
- Preserve and investigate fresh-seed-3 case 46's three-word pre-existing mismatch in a separate first-divergence ticket. Native AE/UCRT, independent noise-layer worlds, and unmeasured parameter/input intersections remain outside these bounded closures.
- Milestones: alignment `981ef3ac`; Angle `a4cbffd2`; final Repeat Border/radius correction is the third commit containing this report. No push or MAIN mutation.
