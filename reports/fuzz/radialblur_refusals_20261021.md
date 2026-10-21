# RadialBlur Mac refusal census (2026-10-21)

Campaign report: `reports/fuzz/radialblur_20261021.json` (seed 1, 500 legal cases,
4 jobs). Production source SHA-256
`14f1b2a94b8a20eec9742f97ec62e9d168a6c942c05c731a23929ea1d5f97520`; candidate
SHA-256 `8b7308839c53a123bf4be677a080edf969314c5e2607e24a18dd3022bb7fb3b0`.

Coverage:

- Total Mac refusals: 803 (Classic 413, Smart 390).
- Attributed to a named guard: **784/803 (97.63%)**.
- Error 516 (`PF_Err_BAD_CALLBACK_PARAM`) attribution: **783/783 (100.00%)**.
- Unattributed: 19 Smart refusals with error 710. These come from the adapter's
  noise-layer checkout, before any production admission guard runs (see below).
- One non-516 return (error 4, `PF_Err_OUT_OF_MEMORY`) is attributed to
  `SmartRender:smartrender-generic-budget`; it is a work-budget return, not a
  516 admission guard.

Counts are refusals per route, not unique cases. A case that refuses on both
routes contributes to both the Classic and Smart column; a dash means zero.
Guard ids are recorded as `function:tag@line`; the line is the line of the
guarded return in the run-time source.

| rank | guard id | file:line | Classic | Smart | top triggers (non-default params, depth, profile) | intent |
|---:|---|---|---:|---:|---|---|
| 1 | `RenderZoomTyped:unadmitted-zoom-profile` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:2827` | 204 | 204 | params slot 12 (68), slot 4 (67), slot 6 (66); depth 32 (74)/16 (73)/8 (57); profile sdr (177), hdr (15), signed (7) | Rejects any Zoom control tuple that misses every exact-fixture predicate. |
| 2 | `RenderWorld:generic-world-not-admitted` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:5272` | 120 | 96 | params slot 10 (49), slot 4 (49), slot 2 (34); depth 16 (61)/32 (50)/8 (9); profile sdr (105), hdr (7), signed (6) | "must either pass that family's complete world/layout contract or stop here." |
| 3 | `RenderRotationTyped:unadmitted-rotation-profile` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:4106` | 30 | 30 | params slot 1 (30), slot 10 (25), slot 7 (24); depth 16 (13)/8 (12)/32 (5); profile sdr (29), hdr (1) | Rejects any Rotation control tuple that misses every exact-fixture predicate. |
| 4 | `RenderWorld:type3-zero-noise` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:5241` | 21 | 21 | params slot 25 (21), slot 10 (10), slot 4 (9); depth 8 (8)/16 (7)/32 (6); profile sdr (18), hdr (3) | "A zero/negative Type-3 amount does not belong to the sole admitted NV25 layer tuple." |
| 5 | `RenderZoomTyped:unadmitted-zoom-noise-inner-profile` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:2995` | 12 | 12 | params slot 10 (10), slot 11 (5), slot 5 (4); depth 8 (10)/32 (1)/16 (1); profile sdr (12) | "These branches are not yet backed by an actual-AEX worker/output contract." |
| 6 | `ValidateNoiseLayerWorld:noise-world-invalid` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:5096` | 19 | — | params slot 24 (19), slot 25 (19), slot 12 (17); depth 32 (7)/16 (6)/8 (6); profile sdr (16), signed (1), hdr (1) | Type-3 Noise Layer was requested but the host provided no usable world. |
| 7 | `RenderRotationTyped:unadmitted-two-stage-profile` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:4322` | 7 | 7 | params slot 1 (7), slot 4 (4), slot 28 (3); depth 16 (4)/32 (3); profile sdr (6), signed (1) | Admits Rotation only through the generic families or a proven exact tuple. |
| 8 | `SmartRender:smartrender-generic-budget` | `mac/OLMRadialBlur/OLMRadialBlur.cpp:6077` | — | 1 | params slot 2 (1), slot 10 (1), slot 29 (1); depth 8 (1); profile sdr (1) | tag-derived: smartrender generic budget |

## How attribution works

`OLM_REFUSAL_TRACE` names a file. When set, each guarded return appends one line,
`function:tag@line`, to that file and then returns exactly the same error code as
before. The adapter gives each route its own trace file under the disposable case
directory, clears it before the run, and reads it after the route returns. The
fuzzer stores the resulting guard list in `refusal_guards`, outside the compared
`result`, so tracing cannot change replay equality.

A refusal with error 516 and no trace line means the process returned 516 without
passing a tagged production guard (for example, a test seam or an untagged
diagnostic site). A refusal with a non-516 error is classified separately.

## Unattributed refusals

All 19 are Smart error 710. The adapter's `pre()` checkout samples the Layer popup
(slot 25) but does not construct an independent noise-layer world. When the popup
is non-zero, the harness refuses with 710 before production code runs. All 19
cases have `noise_type=3` and `noise_variation>0`; the equivalent Classic route
reaches `ValidateNoiseLayerWorld` and refuses with 516. This is a harness
limitation, not an unnamed production guard.

The single error-4 case is seed 1 index 104 (134x253, depth 8, inner strength
1169). It is the generic-budget return in `SmartRender`, so it is not a 516
admission guard and is not counted in the 516 coverage figure.

## Reading the trigger column

The parameter counts are the most frequent non-default control slots among the
cases that hit the guard (slot numbers follow the public declarations). Because
the generator often leaves most controls at their defaults, these are descriptive
features, not proof of a single triggering predicate. `depth` and `profile` are
the full distribution for the guard's cases. Several guards are deliberately
broad catch-alls over exact-fixture predicates, so no individual parameter
dominates: in particular, `unadmitted-zoom-profile` rejects 204 cases per route
with a roughly even depth split and no single non-default slot above 68/204.

Intent text in quotes is copied from a source comment. Unquoted intent text is
derived from the guard tag and its surrounding condition.

## Verification

- Replay of `tests/fuzz_corpus/radialblur`: 35/35 `matches_saved`.
- `OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py`: 8 tests, OK.
- Framework hashes in the campaign report match the committed analysis tool and
  fuzzer files.
- No admission guard was removed or relaxed; tracing only appends to the named
  file when the environment variable is set.
