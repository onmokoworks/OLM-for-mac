status: done

summary:
- Closed three Smart admission clusters: off-frame Center, finite signed/HDR Zoom input, and defined negative Noise Offset at integer depths.
- Seed 1 n300: 198 exact / 0 mismatch / 102 refusal -> 241 / 0 / 59; seed 5: 197 / 0 / 103 -> 233 / 0 / 67.
- All 395 baseline-exact campaign hashes and all 35 corpus Smart hashes are retained; 79 newly admitted campaign rows are exact.
- Each milestone passes 600 sanitized campaign replays and eight existing tests; independent boundary matrices and paired AEX traces pass.
- PF32 Gaussian import and Rotation residuals remain unpromoted and documented; this is bounded CPU-emulator evidence, not full AE compatibility.

facts:

FACT: Resumed on `fa33a5f8` with uncommitted prior C11 work. The retained baseline
campaigns bind HEAD source SHA256 `e65fd8add8bc886365a3e8aebd24fe9d0c1cd710159aabbcc6f5a20b3f11d0a1`.
Read AGENT_GUIDE, the RadialBlur ledger row, compatibility plan, GOTCHAS, and
T01/T03/T05/F08/F13/C06 plus F10/F12 methodology. Reused only verified inherited
changes. No permission rejection, MAIN/cache/emulator modification, worker rebuild,
release-gate/ledger edit, installation, push, history rewrite, stash or `/tmp` scratch.
`core/dblur_noise.h` changes only the RadialBlur generator, not its DirectionalBlur function.
Eight abandoned build directories were removed; remaining scratch is 294 MiB.

Bindings:
- Original AEX SHA256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Worker: `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`.
- Worker SHA256: `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
- Final plugin source SHA256: `d569b69db194cb60734e02eb9cd25d49080021daf998b6f6415e0eb5d7940801`.
- Final Radial noise header SHA256: `b269277801195d27cb204e85069984650c0c575d6ee79ad72e6d17e4a0ea1cd9`.

FACT: The adapter's older archived calibration remains 4/6; its stale PF32 hashes
are not acceptance truth. All numerical comparisons use the pinned original-AEX
public Smart worker, raw typed ARGB and matching controls. No tolerance or PNG
visual comparison. PNG is used only as a byte-lossless transport for trace CLI
inputs, with exact reconstruction assertions and final public-Smart hash binding.
Native Windows UCRT/AE, GPU, ROI and downsample equivalence are not claimed.

| Milestone / commit | Seed 1 Smart E/M/R | Seed 5 Smart E/M/R | Newly exact rows, seeds 1/5 |
|---|---|---|---|
| Baseline | 198/0/102 | 197/0/103 | — |
| Center / `f0f6e308` | 229/0/71 | 219/0/81 | 31 / 22 |
| Finite Zoom / `dbc0e534` | 239/0/61 | 231/0/69 | 10 / 12 |
| Negative phase / this commit | 241/0/59 | 233/0/67 | 2 / 2 |

FACT: Each 300-case campaign completed, using `--plugin radialblur --n 300 --seed
{1,5} --jobs 2 --case-timeout 30 --budget-minutes 120 --shrink-attempts 0
--shrink-seconds 0 --worker <pinned-worker>` with separate scratch/corpus/report
paths under this ticket. Every long command was redirected to a matching `.log`.
The final ordinary production seed-1 campaign independently measures 241/0/59,
AEX Smart 280 ok / 20 reject / 0 budget. A final ordinary production replay of all
300 seed-5 results is identical. AEX wall-time budgets varied on refused cases;
no baseline exact or newly admitted output relies on a timed-out reference.
Because the radius operation changes generic Rotation, the 190 exact seed-3
rows from C06 were also replayed with final-source ASan/UBSan: 190 identical and
clean. This is an exact-subset check, not a new full seed-3 campaign.
Campaign Classic remains outside F18's target and still has mismatches; it is not
used to justify these Smart admissions.

FACT: Full corpus replay was performed before and after every milestone. All 35
saved result objects match, including Classic results. Complete rebaseline table:

| Corpus Smart transition | Center | Finite Zoom | Negative phase |
|---|---:|---:|---:|
| exact -> exact, identical hash | 35 | 35 | 35 |
| changed rows | 0 | 0 | 0 |

No corpus mutation was necessary. No base-exact campaign hash changed. Each
milestone's current-source ASan/UBSan replay is 600/600 identical and clean, and
each runs the eight existing generic/budget/Type3/Smart/size-noise/geometry tests
successfully. `git diff --check` passes. The first two independent matrices were
verified at their milestone source; the final negative-phase matrix uses final
production. Raw guards, input/padding preservation and callback lifecycle checks
are enforced by the common public harness.

Center cluster (largest initial generic-world refusal group):

FACT: Original-renderable baseline refusals: generic world 42, Zoom profile 26,
budget 5, Type3 zero noise 4, Rotation profile 3, host checkout 1. Removing only
the in-frame Center restriction measured seed 1 241/1/58 and seed 5 238/2/60;
that broad experiment was rejected. The all-depth independent matrix additionally
found PF16 Rotation and PF32 residuals. Production admits representable off-frame
Center only for PF8 Zoom/Rotation and PF16 Zoom.

FACT: Seed-1 case 67, 11x8 PF8 Rotation, Center
(5.5186920166015625,13.846389770507812), first diverges at radial dimensions:
original 1800x14, gate-only Mac 1800x17. Original Rotation 1BB0 and Zoom A8F0 use
FLOAT32 axis distances/squares/sqrt, integer half-extent selection, and integer
radius truncation before Ratio division (Rotation caller 481B..4849). Generic
Rotation now uses the already grounded shared radius helper. Afterward all six
paired stages are exact: polar/scalar/span/accum/max/normalized, including
100800-word RGBA planes. Final AEX/Mac raw SHA256:
`e5c33d61f49ea959c7c49bf229f5f95c98832870c83e2ed99c7335d4dabeef79`.
The resumed trace independently reproduced these results. Earlier incomplete
inherited traces omitted the inclusive endpoint; only corrected `*-full` and
resumed reports are acceptance evidence.

FACT: Independent Center matrix: 3 geometries x 3 admitted depth/family pairs x
12 Center/control variants = 108 AEX references, each with packed and two odd
padding layouts = 324 exact, clean renders. Evidence: `C11-centers.evidence.json`
and `C11-centers-trace.evidence.json`.

Finite-input cluster (remaining generic-world refusals):

FACT: Broad PF32 finite-input admission measured seed 1 240/0/60 and seed 5
231/0/69, but the independent matrix found four Rotation mismatches (12 layouts).
Three are 3x5 subnormal inputs: first word 25, AEX `0000803f`, Mac `00000000`.
The other is 11x7 HDR with Fade: first word 28, AEX `514b2846`, Mac `4f4b2846`.
That broad hypothesis was rejected with new input-boundary evidence.

FACT: The promoted rule makes RenderWorld's PF32 Zoom check match
RenderZoomTyped's existing finite-only contract. Rotation retains its SDR check;
NaN/Inf remain refused. No arithmetic, writer, sampler, dimensions or budget
changes. Independent Zoom matrix: 3 geometries x 3 signed/HDR/subnormal families
x 4 control profiles = 36 AEX references / 108 exact clean layout renders.
The baseline test now checks finite Zoom acceptance, retained Rotation refusal
and retained nonfinite refusal. Evidence: `C11-finite-zoom.evidence.json`.

Negative-phase cluster (largest remaining Zoom-profile group):

FACT: After finite Zoom, original-renderable refusals were Zoom profile 14,
generic world 13, Type3 zero noise 5, budget 4, Rotation profile 3, host 1.
The negative-phase scratch experiment adds an index-domain check before table
reads and allows the signed AD phase range. All-depth results were seed 1
242/0/58 and seed 5 233/1/66. Seed-5 case 264 (PF32 Zoom, Strength 19) newly
mismatches in six words/six bytes: first word 63, AEX `6db5ef3e`, Mac `6eb5ef3e`.
PF32 negative-phase admission was not promoted.

FACT: Original 958B..9597 subtracts only the upper table bound; 95A0 truncates
position toward zero, and 95CD/95D8 read table[index+1]/table[index] from the
101-element allocation. Negative phase is valid when every generated signed
index lies in [0,99], including a negative fractional part at index zero.
The Radial-only core check now rejects an invalid index before either read.
The existing caller reports its noise-plane failure (error 4) and Smart does not
publish the staging buffer. There is no invented lower wrap/clamp or lookup of
case/seed/output values. PF32 active negative phase retains refusal.

FACT: Final promotions: seed 1 indices 173 (PF16) and 183 (PF8); seed 5 indices
175 (PF16) and 234 (PF8), all exact. Independent NumPy MT19937 integer streams
compute valid-index boundaries, binary-search signed-fixed phase, then test the
boundary and both adjacent values, near-zero negative phase, -30 degrees and
the signed minimum, across two geometries, two seeds, PF8/PF16, Zoom/Rotation,
noise types and varied controls/layouts. Results: 64 defined references / 192
exact clean renders; 32 undefined references / 96 clean refusals. A boundary-
adjacent original noise-plane trace at raw AD -14703201, minimum index 0, is
12/12 words exact against C++; its final image matches the public Smart oracle.
The earlier broad matrix also passed 144 rows, but does not override the known
seed-5 PF32 counterexample. Evidence: `C11-negative-phase.evidence.json`.

External reference-math boundary, retained as a refusal:

FACT: The off-frame PF32 Zoom witness reduces/transports to 12x1. Weight table
length 10 first differs at word 8, AEX `a5ed653d`, Mac `a4ed653d`. Polar,
eligibility, span, preaccum and premax match; accum differs in 109 words and
normalized in 106. Final first word 38: AEX `e2e2e23e`, Mac `e1e2e23e`.

FACT: Seed-5 case 264 reduces by removing Noise Variation/Offset and simplifying
pixels; geometry remains 29x41. A byte-lossless PNG-transport witness still
mismatches. Table length 19 first differs at word 17, AEX `5c47df3c`, Mac
`5d47df3c`. The same five upstream planes match; accum differs in 1415 words,
normalized in 1143; final differs in nine words, first word 109 AEX `9190903e`,
Mac `9290903e`. This paired trace is of the reduced transported witness, not a
claim to have traced every original arbitrary FLOAT32 pixel.

FACT: Original B782 calls the expf thunk 1F574 (IAT 211B0) for those tail entries.
The pinned worker binds expf to host `f32::exp`; independent host-expf evaluation
reproduces each original-AEX table word, while double-exp-then-float reproduces
the Mac word. Neither worker imports nor the retained production Windows-exp
model were changed. This is a demonstrated external math boundary, not proof of
which implementation is correct for every native Windows UCRT input. These
witnesses also show latent PF32 mismatches outside the finite campaign set.
Evidence: `C11-exp-import.evidence.json`, committed lossless fixtures and
`check_radialblur_exp_C11.py`. No failed numerical hypothesis was repeated without
new boundary data; the two-hypothesis stop condition was not reached.

FACT: Probe-development failures were a missing hash field in the independent
noise verifier and too many final-sampler watches for the retained trace limit.
The verifier now records the raw hash explicitly; final-sampler/coordinate watches
are batched without dropping observations. Complete reruns passed. No incomplete
trace or failed verifier run is used as acceptance evidence.

inference:

INFERENCE: The Center gate hid working integer-depth behavior and one real
Rotation radius-operation error. The PF32 SDR gate was inconsistent with the
existing finite Zoom operation. A negative noise phase is not intrinsically
invalid; actual generated table addresses define its valid subset. These are
general rules, with depth restrictions retained where independent counterexamples
exist. The broad PF32 failures require separate Rotation and native-UCRT work;
quantization success at integer depths does not prove a FLOAT32 implementation.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: Center/finite Zoom/negative-phase admission and original Rotation radius operation.
- `core/dblur_noise.h`: Radial-only table-index bounds check.
- `tests/test_olmradialblur_generic_baseline_20260820.py`: new admission boundaries and retained refusals.
- `tools/fuzz/probe_radialblur_smart_C11.py`: reproducible scratch-only source/header experiments.
- `tools/fuzz/verify_radialblur_smart_C11.py`, `verify_radialblur_negative_C11.py`: independent boundary matrices and campaign acceptance.
- `tools/fuzz/verify_radialblur_smart_C06.py`: permit another ticket's scratch root.
- `tools/fuzz/trace_radialblur_rotation_C11.py`, `trace_radialblur_smart_C06.py`: paired Rotation/Zoom stages, typed lossless transport, weights and bounded watch batches.
- `tools/fuzz/transport_radialblur_C11.py`, `check_radialblur_exp_C11.py`: reproduce traceable PF32 witnesses and imported-exp boundary.
- `tools/fuzz/fixtures/radialblur_rotation_C11.json`, `radialblur_exp_C11.json`, `radialblur_exp19_C11.json`: reproducible inputs.
- `orchestra/reports/C11-*.evidence.json` and this report: hash-bound measurements and transitions.

verify:

Run in this worktree with fresh output paths. These commands reproduce final
acceptance; each source milestone's complete transitions are in its evidence.

```sh
S="$PWD/orchestra/state/C11-radial-smart-r2/recheck-final"
PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
W=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
mkdir -p "$S"
export TMPDIR="$S"
"$PY" -u tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2 --case-timeout 30 --budget-minutes 120 --shrink-attempts 0 --shrink-seconds 0 --worker "$W" --scratch "$S/seed1" --corpus "$S/corpus1" --report "$S/seed1.json" > "$S/seed1.log" 2>&1
"$PY" -u tools/fuzz/run.py --plugin radialblur --n 300 --seed 5 --jobs 2 --case-timeout 30 --budget-minutes 120 --shrink-attempts 0 --shrink-seconds 0 --worker "$W" --scratch "$S/seed5" --corpus "$S/corpus5" --report "$S/seed5.json" > "$S/seed5.log" 2>&1
"$PY" -u tools/fuzz/verify_radialblur_smart_C11.py --evidence orchestra/reports/C11-negative-phase.evidence.json --independent --smoke --output "$S/center-and-campaigns" > "$S/center-and-campaigns.log" 2>&1
"$PY" -u tools/fuzz/verify_radialblur_smart_C11.py --finite-inputs --independent --output "$S/finite" > "$S/finite.log" 2>&1
"$PY" -u tools/fuzz/verify_radialblur_negative_C11.py --output "$S/negative" > "$S/negative.log" 2>&1
"$PY" -u tools/fuzz/trace_radialblur_rotation_C11.py --fixture tools/fuzz/fixtures/radialblur_rotation_C11.json --output "$S/rotation" > "$S/rotation.log" 2>&1
"$PY" -u tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 2 --case-timeout 30 --budget-minutes 60 --worker "$W" --scratch "$S/replay" --report "$S/replay.json" > "$S/replay.log" 2>&1
git diff --check
```

Expected: seed 1 241/0/59 and seed 5 233/0/67; 790 same/clean replay rows
(600 from seeds 1/5 plus the 190 historical seed-3 exact rows);
324 exact Center renders; 108 exact finite Zoom renders; 192 exact and 96 refused
negative-phase renders, all clean; 8 smoke tests pass; six Rotation planes exact;
35/35 corpus saved expectations match. Campaign commands exit 0 on completion; pixel correctness is enforced by raw
results and the verifiers, not by campaign exit code. Classic mismatches remain visible. AEX wall-time budgets may vary on refused cases.

Diagnostic reproduction of the excluded expf boundary (expects mismatch, not a
production admission). The historical source is read without changing the checkout:

```sh
"$PY" tools/fuzz/probe_radialblur_smart_C11.py --experiment centers-radius --revision fa33a5f8 --snapshot-only --experiment-directory "$S/exp-source" > "$S/exp-source.log" 2>&1
"$PY" -u tools/fuzz/trace_radialblur_smart_C06.py --source "$S/exp-source/experiment.cpp" --cases-from tools/fuzz/fixtures/radialblur_exp_C11.json --indices 31 --no-shrink --output "$S/exp10" > "$S/exp10.log" 2>&1
"$PY" tools/fuzz/check_radialblur_exp_C11.py --trace "$S/exp10/report.json" --output "$S/exp10-boundary.json" > "$S/exp10-boundary.log" 2>&1
"$PY" -u tools/fuzz/trace_radialblur_smart_C06.py --cases-from tools/fuzz/fixtures/radialblur_exp19_C11.json --indices 264 --no-shrink --output "$S/exp19" > "$S/exp19.log" 2>&1
"$PY" tools/fuzz/check_radialblur_exp_C11.py --trace "$S/exp19/report.json" --output "$S/exp19-boundary.json" > "$S/exp19-boundary.log" 2>&1
```

Expected: table first differences 8 (`a5ed653d`/`a4ed653d`) and 17
(`5c47df3c`/`5d47df3c`), and the exact plane/word counts above. The all-depth negative
experiment is reproducible with `--experiment negative-noise --revision dbc0e534`;
its index guard is generated into a scratch header, never applied to the oracle.

next:
- The requested three-cluster loop is complete. Keep the remaining 59 seed-1
  refusals; do not infer whole-plugin exactness from this benchmark.
- Follow-up: resolve the two hash-bound native-UCRT expf tail words before PF32
  off-frame/negative-phase admission, without changing the reference worker silently.
- Follow-up: paired first-divergence work on PF16/PF32 Rotation center/HDR/subnormal
  residuals; retain their current admission limits.
- Type3 zero-noise/layer checkout, invalid negative table indices, nonfinite input
  and resource-budget refusals remain distinct unclosed boundaries.
