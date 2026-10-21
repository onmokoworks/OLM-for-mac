# RadialBlur admission-gate bypass experiment (2026-10-21)

Ticket: `T05-radialblur-gate-off-experiment`. Measurement only: no admission gate
was removed or relaxed in the default build.

## What was built

- `mac/OLMRadialBlur/OLMRadialBlur.cpp` gained a compile-time switch,
  `OLM_RADIAL_EXPERIMENT_BYPASS`, empty unless defined. The six top T03 guards
  test `!RadialExperimentBypass("<tag>")`, so a scratch build can let a named
  guard fall through. With no define the switch is inert; the corpus replay
  below verifies default behavior.
- `tools/fuzz/adapters/radialblur.py` gained two off-by-default measurement
  switches: `OLM_RADIAL_CANDIDATE_BYPASS="tag1,tag2"` (injects the compile-time
  define) and `OLM_RADIAL_CANDIDATE_SANITIZE=1` (uses the probe's existing
  `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` build). The
  adapter now preserves sanitizer reports in each route result and parses only
  `KEY value` harness metadata lines, so UBSan stack traces cannot masquerade as
  harness errors.

## Reproduction

Baseline default build (must be 35/35):

```sh
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur \
  --scratch orchestra/state/T05-radialblur-gate-off-experiment/final_default_scratch \
  --report orchestra/state/T05-radialblur-gate-off-experiment/final_default_replay.json \
  --budget-minutes 20 --jobs 4
```

One gate (replace the tag; each campaign uses its own `--corpus`):

```sh
OLM_RADIAL_CANDIDATE_BYPASS=unadmitted-zoom-profile \
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 \
  --budget-minutes 25 \
  --report reports/fuzz/radialblur_t05_bypass_zoom_profile_20261021.json \
  --corpus orchestra/state/T05-radialblur-gate-off-experiment/corpus_zoom_profile \
  --scratch orchestra/state/T05-radialblur-gate-off-experiment/scratch_zoom_profile
```

All six together:

```sh
OLM_RADIAL_CANDIDATE_BYPASS=unadmitted-zoom-profile,generic-world-not-admitted,unadmitted-rotation-profile,type3-zero-noise,unadmitted-zoom-noise-inner-profile,unadmitted-two-stage-profile \
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 \
  --budget-minutes 25 \
  --report reports/fuzz/radialblur_t05_bypass_all_20261021.json \
  --corpus orchestra/state/T05-radialblur-gate-off-experiment/corpus_all \
  --scratch orchestra/state/T05-radialblur-gate-off-experiment/scratch_all
```

Sanitizer all-bypass (shrinking disabled to avoid the runner's timeout-during-
shrink race; see Caveats):

```sh
OLM_RADIAL_CANDIDATE_BYPASS=<all six tags> OLM_RADIAL_CANDIDATE_SANITIZE=1 \
ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 \
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 \
  --budget-minutes 45 --shrink-attempts 0 --shrink-seconds 0 \
  --report reports/fuzz/radialblur_t05_bypass_all_sanitize_20261021.json \
  --corpus orchestra/state/T05-radialblur-gate-off-experiment/corpus_all_sanitize \
  --scratch orchestra/state/T05-radialblur-gate-off-experiment/scratch_all_sanitize
```

Summarize the committed reports:

```sh
python3 tools/fuzz/t05_bypass_summary.py
```

Expected baseline result: `replay_complete`, 35/35 `matches_saved`, exit 0.
`OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py` also passed
(8 tests, OK).

## Per-gate results (gate bypassed alone)

`route rows` are Classic+Smart rows whose T03 baseline refusal carried that guard.
`unblocked` means the candidate returned output; `exact` / `mismatch` compare
against the original AEX; `uncompared` means the candidate rendered but the AEX
oracle rejected or budgeted. `UB rows` is from the all-six sanitizer campaign,
grouped by the gate that refused the same route in the baseline (see Sanitizer).

| gate | route rows | unblocked | exact | mismatch | uncompared | still refused | crash | new error | budget | UB rows | unique cases | cases unblocked | cases exact | cases mismatch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| unadmitted-zoom-profile | 408 | 240 | 16 | 224 | 0 | 168 | 0 | 0 | 0 | 173 | 204 | 120 | 8 | 112 |
| generic-world-not-admitted | 216 | 11 | 4 | 7 | 0 | 205 | 0 | 0 | 0 | 160 | 120 | 7 | 2 | 5 |
| unadmitted-rotation-profile | 60 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 20 | 30 | 0 | 0 | 0 |
| type3-zero-noise | 42 | 6 | 2 | 0 | 4 | 36 | 0 | 0 | 0 | 10 | 21 | 3 | 1 | 0 |
| unadmitted-zoom-noise-inner-profile | 24 | 24 | 2 | 22 | 0 | 0 | 0 | 0 | 0 | 2 | 12 | 12 | 1 | 11 |
| unadmitted-two-stage-profile | 14 | 14 | 0 | 12 | 2 | 0 | 0 | 0 | 0 | 2 | 7 | 7 | 0 | 6 |
| ALL SIX | 764 | 763 | 69 | 654 | 40 | 1 | 0 | 0 | 0 | 367 | 394 | 393 | 35 | 338 |

Same populations with all six gates lifted (this removes the downstream guard
shadowing that makes a single-gate run unblock nothing):

| gate population | route rows | unblocked | exact | mismatch | uncompared | still refused | crash | new error | budget |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| unadmitted-zoom-profile | 408 | 408 | 24 | 382 | 2 | 0 | 0 | 0 | 0 |
| generic-world-not-admitted | 216 | 215 | 31 | 184 | 0 | 1 | 0 | 0 | 0 |
| unadmitted-rotation-profile | 60 | 60 | 8 | 44 | 8 | 0 | 0 | 0 | 0 |
| type3-zero-noise | 42 | 42 | 4 | 8 | 30 | 0 | 0 | 0 | 0 |
| unadmitted-zoom-noise-inner-profile | 24 | 24 | 2 | 22 | 0 | 0 | 0 | 0 | 0 |
| unadmitted-two-stage-profile | 14 | 14 | 0 | 14 | 0 | 0 | 0 | 0 | 0 |

Downstream guards still refusing when a gate is bypassed alone:

- `unadmitted-zoom-profile`: 168 rows still refused, all by
  `unadmitted-zoom-noise-inner-profile`.
- `generic-world-not-admitted`: 205 rows still refused: 177
  `unadmitted-zoom-profile`, 19 `unadmitted-rotation-profile`, 6
  `unadmitted-zoom-noise-inner-profile`, 2 `unadmitted-two-stage-profile`,
  1 `generic-budget` (work budget, not an admission gate).
- `unadmitted-rotation-profile`: all 60 rows still refused by
  `unadmitted-two-stage-profile`.
- `type3-zero-noise`: 36 rows still refused: 28 `unadmitted-zoom-profile`,
  8 `unadmitted-rotation-profile`.
- `unadmitted-zoom-noise-inner-profile` and
  `unadmitted-two-stage-profile`: nothing downstream; every row unblocks.
- ALL SIX: 1 row still refused by `generic-budget`.

All six guards have a real fall-through path (code follows them and execution
continues). The rotation-profile guard is fully shadowed by the two-stage guard,
not absent.

## Mismatch clusters

Signature is `[stage, non-default control slots, depth]` from the campaign's
bounded reduction. Slots: 1 Blur Type, 2 Center, 4 outer Strength, 5 outer
Offset Mode, 6 outer Offset, 7 outer Edge Fade, 10 inner Strength, 11 inner
Offset Mode, 12 inner Offset, 13 inner Edge Fade, 18 Angle, 20 Quality,
21 Brightness Gain, 22 Size Variation, 24 Noise Variation, 25 Noise Type,
27 Seed, 28 Offset, 29 Thickness.

`unadmitted-zoom-profile` (224 mismatching unique cases, 50 clusters), top:

```
24  ["raw-output",[12],16]        24  ["raw-output",[6],16]
16  ["raw-output",[12],32]        10  ["raw-output",[6],32]
 8  ["raw-output",[4,18],32]       8  ["raw-output",[12,13],8]
 8  ["raw-output",[13],8]          8  ["raw-output",[11,13],16]
```

`generic-world-not-admitted` (7 cases, 5 clusters): `[4,18]@32` (2), `[4]@32`
(2), `[1,10]@16`, `[13]@32`, `[4]@16`.

`unadmitted-rotation-profile` alone: no unblocked rows, no clusters. With all
gates lifted this population is 44 mismatch / 8 exact / 8 uncompared; the exact
rows are all 1x1 frames (cases 28, 61, 108, 438).

`type3-zero-noise` alone: no mismatch. With all gates lifted: 30/42 rows are
`uncompared` because the original AEX also rejects them; of the 12 AEX-renderable
rows, 4 exact and 8 mismatch. The two exact cases (297, 312) are both 1x1.

`unadmitted-zoom-noise-inner-profile` (22 cases, 6 clusters): `[10,11]@8` (8),
`[5,10]@8` (6), `[10,11]@32` (2), `[10]@16` (2), `[6]@8` (2), `[12]@8` (2).

`unadmitted-two-stage-profile` (12 cases, 5 clusters): `[1,12]@32` (4),
`[1,4,18]@16`, `[4]@16`, `[1,6]@16`, `[1,6]@32` (2 each). The remaining
route row was `uncompared` in the individual run; the all-six run compared it
and it mismatched, so its all-population outcome is 14/14 mismatch.

ALL SIX (654 mismatching unique cases, 118 clusters), top:

```
54  ["raw-output",[10],32]        46  ["raw-output",[10],16]
32  ["raw-output",[4],16]         32  ["raw-output",[4],32]
31  ["raw-output",[13],16]        30  ["raw-output",[13],32]
26  ["raw-output",[12],16]        22  ["raw-output",[7],32]
```

## Sanitizer (all-six bypass, ASan/UBSan)

- 370 route rows produced UBSan reports (217 Classic, 153 Smart); 367 of them
  lie in the six-gate baseline population. 3 more are on already-admitted cases.
- Every report is `-fsanitize=alignment`: "reference binding to misaligned
  address ... for type PF_Pixel16/PF_PixelFloat". No AddressSanitizer, no
  LeakSanitizer, no out-of-bounds/heap error, and no aborted process.
- Sites (source line before the injected define): 1666 and 2573 (input alpha
  admission probes), 2559 (input alpha probe), 3034 (Zoom input read), 3432
  (Zoom output write), 4366 (Rotation input read), 5051 (Rotation output write),
  5017-5020 (PF16 pack writes).
- Default-build sanitizer control, same 500 cases, no bypass: 35 route rows with
  the same alignment reports: 32 refusals, 2 exact, 1 mismatch. The two exact
  rows are case 193 (16bpc) and 425 (32bpc).

Facts: the reports correlate with odd/incompatible rowbyte padding (the
generator deliberately emits padding 0/1/3/7/16 in and 0/1/5/11/32 out). The
default build already reports this UB class on 35 rows, so lifting gates is not
the origin of the UB. The bypass raises exposure from 35 to 370 rows.

Inference: the underlying defect is unaligned `PixelT` dereference in admission
probes and render loops, not admission policy. Real AE worlds may supply aligned
rows, so this is a harness-world/adversarial-padding risk; it is nevertheless
real C++ UB on an input the fuzzer can generate, and it should be fixed in
general code independently of this experiment.

## Caveats

- `uncompared` is not a port failure: the AEX oracle rejected or budgeted the
  case, so no reference exists. This is why `type3-zero-noise` is mostly
  uncomparable.
- Exact cases are single-case evidence, not proof for a tuple family. Several
  exact cases are 1x1 or one-row frames (identity-like). Non-degenerate exact
  cases do exist under gates 1 and 2 (e.g. 38, 98, 146, 475 and 49, 60, 166, 232,
  326, 352, 371, 429), but they are few and must be checked against the exact
  fixture/worker contract before any predicate is widened.
- The first ASan pass with shrinking enabled lost rows to an existing runner race: `os.killpg` raised `PermissionError` after a shrink subprocess timed out.
  The reported sanitizer run uses `--shrink-attempts 0` and completed 500/500.
- Campaigns are CPU-AEX emulation versus the fake SDK host, not native Windows
  AE/UCRT.
- The AEX oracle budget is wall-clock based, so `uncompared` can move by a few
  rows between otherwise identical runs. The six gate reports, the all-six
  report and the sanitizer report were all produced with the final committed
  adapter (identical `framework_sha256`). The table above is read from those
  final reports; all-six totals (69 exact / 654 mismatch / 40 uncompared) were
  stable across the pre-final and final all-six runs.

## Report files

- `reports/fuzz/radialblur_t05_bypass_zoom_profile_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_generic_world_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_rotation_profile_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_type3_zero_noise_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_zoom_noise_inner_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_two_stage_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_all_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_all_sanitize_20261021.json`
- `reports/fuzz/radialblur_t05_default_sanitize_control_20261021.json`
