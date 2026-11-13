# OLM Smoother2 — integrated 2026-11-12 release

## Cropped output compatibility ? F-smoother2-roi (2026-11-13)

The historical cropped-output restriction below is removed. Unequal input/output
sizes now preserve the original's host-copy result; shifted origins no longer
cause a blanket 516 rejection. The performance pipeline from PR #12 is unchanged.

**Root cause and original behavior.** The Rust boundary rejected unequal world
width/height/origin, and the pure adapter repeated that restriction. In the 2025
original (`add776af61499d425f3978f4e5e4c2c8b4062db6d7276db66a22928749227137`),
SmartRender calls `PF_COPY(input, output, NULL, NULL)` first, at RVAs 0x2000,
0x2139 and 0x2272 for 8/16/32 bpc. Its intermediate planes use the output size
(constructor 0x5c60, allocation arguments 0x5d25?0x5d55). The pipeline compares
all plane dimensions at 0x464d/0x4dad/0x49fd and throws for unequal dimensions;
the successful rendered result is the initial host copy. Static disassembly
plus exact original/candidate renders establish this behavior. Applying smoothing
before or after resizing would change it. World descriptor constructors copy
data, width, height and rowbytes, without applying world origin offsets.

**Fix.** For unequal dimensions, invoke the same host callback with null source
and destination rectangles, into staged output. This preserves the host's depth
and resampling semantics. Equal dimensions retain the existing pipeline. Keep
validated row spans, matching depth, non-overlap, host-world format queries,
active-row publication, and one input checkin. Callback failure or late checkin
failure cannot publish partial output. The mock host regression covers both
branches, shifted origins, callback failure, checkin failure, input immutability,
and bytes beyond active output.

Evidence and reproduction are recorded in [roi-validation.json](roi-validation.json)
and [validate_roi.py](validate_roi.py). The latter runs ten extent campaigns and
the two-seed normal gate with at most two jobs, retaining summary records before
deleting successful render directories. Empty host results are separately
classified, never counted as exact rendered pixels.

### Measured evidence

| Campaign | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| Ten extent campaigns, fresh processes | 116 exact | 116 exact | 116 exact |
| Outside-image empty controls (not rendered pixels) | 4 matched | 4 matched | 4 matched |
| Normal seed 20261125, resident | 103 exact | 103 exact | 103 exact |
| Normal seed 20261126, resident | 103 exact | 103 exact | 102 exact, **1 mismatch** |

The ROI campaign uses 11x9, 31x19 and 17x13 inputs, all depths, downsample
1 / 1/2 / 1/4, defaults/minima/maxima/random parameters and ten demand rectangles:
`1,1,7,5`; `0,0,1,1`; `5,4,11,9`; `0,0,11,9`; `2,1,13,10`;
`-3,-2,8,7`; `0,0,31,19`; `11,9,15,13`; `1,0,10,9`; `0,1,11,8`.
All 348 pairs that produced output are byte-exact. The 12 empty controls have
successful, matching empty-result reports and no SmartRender dispatch; the
oracle reports absent output artifacts, not a plug-in error. No ROI case has a
candidate-only failure, timeout or pixel mismatch. The initial 9/9 smoke check
is additional evidence and is not included in these totals.

**Normal-gate exception, not a pass:** 617/618 comparisons are exact. Both seeds
contain 100 random parameter tuples per depth plus default/min/max, at the three
preview scales and sizes 1x1, 3x7, 97x61, 256x144. Seed 20261126 case 23 Smart32
has one blue-channel word at (187,120): original `0x3f1f523e`, Rust `0x3f1f523f`.
The automatic fresh-process replay still mismatches. A fresh unchanged
`origin/main` build at `1b4df7f3` reproduces exactly the same discrepancy, and
baseline-versus-fixed is byte-exact on that saved input/request. The retained
JSON includes the full deterministic case, binary/output hashes and both
comparisons. No exclusion, tolerance, changed seed or passing-case substitution
is used. The full normal all-exact gate remains unmet because of this pre-existing
full-frame discrepancy; it is outside the ROI boundary fix.


**Bounded classification: pre-existing port defect.** Three fresh-process
original-versus-original pairs and three pairs each for fixed Rust and unchanged
main all pass (9 self-comparisons / 18 renders, run serially). Each binary has
one stable native-output hash across its six renders. Main and fixed Rust hashes
are identical and differ from the stable original hash; they also match the
prior resident and fresh-process discrepancy. No original or Rust nondeterminism
was observed in this bounded check. The user approved this documented gate
exception for the focused ROI PR; the failing comparison remains recorded.
Reproduce with [classify_roi_control.py](classify_roi_control.py), supplying the
original, fixed Rust and unchanged-main AEX paths plus a new output directory.

Exact case: campaign seed **20261126**, case **23**, input PCG64 seed
**15135544866034798561**, **256x144**, **Smart32**, downsample **1/4** on both
axes (full-resolution dimensions 1024x576), full-frame/no cropped extent.
Parameter assignments below are exact oracle request values; colors are ARGB8:

| Slot | Parameter | Value |
| --- | --- | --- |
| 1 | Enable Color Key | 1 |
| 2 | Color Key | [178,132,59,226] |
| 3 | Invert Color Key | 0 (untouched default) |
| 4 | Smoothness | 100 (untouched default) |
| 5 | Extra Smooth | 100 |
| 6 | Smooth Range | 59.12997589555684 |
| 7 | Smoother Version | 2 (untouched default) |
| 8 | Gamma Correction | 1 / None (untouched default) |
| 9 | Gamma Value | 1.0 |
| 10 | Number of Gamma Colors | 1 (untouched default) |
| 11 | Gamma Color 1 | [174,173,112,135] |
| 12 | Gamma Color 2 | [66,199,119,65] |
| 13 | Gamma Color 3 | [238,19,171,77] |
| 14 | Gamma Color 4 | [88,218,191,91] |
| 15 | Gamma Color 5 | [144,173,233,94] |

Unchanged main is commit `1b4df7f3` (PR #12 merged). Native RGBA32f output hashes:

- Original: `53c4492b78ca8207c49667f75e99462cc8e3a2ac5b581c901a5598a304f801d7`.
- Main and fixed Rust: `5ab2c48c4557f48451506cc7d4791e53a41c52e92005fa69e128281a61aef906`.

Release tests: **21 passed** (expanded boundary regression); **54/54 goldens**;
crate formatting and all-target release Clippy pass. Workspace-wide formatting
also checked, but reports pre-existing differences outside this owned crate.
Shared dependency and native reference warnings remain unchanged.

### 960x540 performance check

Both builds were tested serially, normal priority, one warmup plus five measured
frames per cell. Each sweep has six exact cells / 36 exact frame pairs; both
offline audits pass. Rendered frames were deleted after hashing.

| Depth / preset | PR #12 baseline ms | Fixed ms | Fixed / original |
| --- | ---: | ---: | ---: |
| 8 default | 34.149 | 37.169 | 0.391 |
| 8 heavy | 43.087 | 44.712 | 0.239 |
| 16 default | 34.744 | 34.291 | 0.364 |
| 16 heavy | 45.713 | 44.328 | 0.242 |
| 32 default | 30.243 | 32.175 | 0.351 |
| 32 heavy | 41.120 | 41.124 | 0.223 |

The sum of cell medians is 1.0207x baseline; individual ratios span 0.970?1.088.
The original-relative speed advantage remains, and no algorithm/performance
implementation changed. A single shared-machine sweep does not prove zero
slowdown or distinguish this small aggregate difference from timing variation.

This is Windows AEXCompat CPU evidence. Native AE and macOS are not qualified by
these runs; arbitrary custom world padding/origins beyond host support are covered
only by boundary tests and static analysis. Historical ROI failures below refer
to earlier artifacts and are retained for provenance, not current restrictions.


## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 | 30 exact | 30 exact | 30 exact |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

Zero pixel mismatches, reference/candidate failures or timeouts remain in these
campaigns. Inventory matches the 2025 original. The unchanged cbrtf implementation and
native bit-exact tests now live in olm-math; 1,033,289 native UCRT probes pass.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

# 2026-11-12 upstream update — measured 2026-11-13

**Current result:** effect 2.2.0 matches the new Windows AE 2025 original in
**681/681** final comparisons (**227 per depth**), with **36/36** additional
comparisons against the AE 2026 original (**12 per depth**). No pixel mismatch,
reference/candidate render failure or timeout remains in these final runs.
All **21 release tests pass**. These are headless Windows AEXCompat CPU results,
not native AE, macOS, GPU, saved-project or UI interaction qualification.

[upstream-validation.json](upstream-validation.json) binds the final candidate,
originals, UCRT provider, source hashes, campaigns and cleanup. Full diagnostic
artifacts are local-only under `upstream-work/`; the older evidence below is
historical 2.1.0 qualification and is not the current release's authority.

## Final measured coverage

| Original / corpus | Isolation | Smart8 | Smart16 | Smart32 |
| --- | --- | ---: | ---: | ---: |
| 2025, seed 20261114, 100 random + default/min/max | Resident fresh sequence | 103 | 103 | 103 |
| 2025, seed 20261115, 100 random + default/min/max | Resident fresh sequence | 103 | 103 | 103 |
| 2025, seed 20261116, independent control | Fresh process | 12 | 12 | 12 |
| 2025, three fractional ranges × three gamma modes, Oklab | Fresh process | 9 | 9 | 9 |
| **2025 final total** | | **227** | **227** | **227** |
| **2026, seed 20261116** | Fresh process | **12** | **12** | **12** |

The primary two-seed campaign covers downsample 1 / 1/2 / 1/4 with
70 / 68 / 68 cases per depth, including 68 / 66 / 66 random cases.
Among its 200 random parameter tuples, versions 1 / 2 / 3 occur 73 / 68 / 59
times, and 53 tuples use a fractional range. Dimensions cycle through 1×1,
3×7, 97×61 and 256×144. All runs use `--jobs 2`, with equal 120-second process
and host frame bounds. Classic rendering is outside the advertised SmartFX
dispatch contract and is not counted.

Resident cases share module globals but use fresh sequences. No mismatch/failure
required an automatic per-process replay. Independent fresh-process controls
and the focused Oklab cases are separately counted above. An earlier candidate
also passed 618 fresh-process 2025 comparisons, 36 fresh-process 2026 comparisons
and 36 smoke comparisons; these are excluded from the final artifact totals.

## Upstream facts and implementation

- Effect version 2.1.0 → 2.2.0. Version choices are exactly
  `v1 (sRGB)|v2 (Linear)|v2 (Oklab)`, default 2, flags 64 (supervised).
- Slot 6 / disk ID 5 changes from integer to float slider, default 2, valid/UI
  range 0–100, one decimal. Parameter construction at new RVA `0x5c60` converts
  the float UI value using **float multiplication by 0.01**; classifier `0xc110`
  then adds 0.001. The old `0xae10` divided an integer by 100.
- The new classifier includes the penultimate column's top-right neighbor.
  Old `x+1 < width-1` becomes `x < width-1`. The class-plane update is shared by
  all versions and explains the observed old/default edge changes.
- New conversion leaves `0x5520` / `0x5840` implement linear RGB ↔ Oklab.
  Setup `0x5bc0` decodes sRGB before Oklab; output `0x5990` performs inverse
  Oklab then sRGB encoding. Matrix arithmetic order and binary32 constants are
  retained. Distance `0xc4e0` uses L directly for the Oklab luminance term.
- Gamma is bypassed for Oklab in parameter construction and `0xd0f0` / `0xc400`.
  New `0xc400` leaves intermediate channels unclamped; output conversion and
  final clamping happen in the output driver (`0x3ca0` for PF32). Rust follows
  that order and avoids reading inactive gamma colors through the host suite.
- UI `0x23b0` disables Gamma Correction, Gamma Value and Number of Gamma Colors
  in Oklab, and hides all gamma color controls. Other modes retain the existing
  gamma-dependent rules. This is statically grounded implementation; native UI
  interaction has not been exercised.
- Raw declaration capture exposed a pre-existing Rust omission: checkbox
  captions for Enable Color Key / Invert Color Key were empty. Both captions
  now match the original.

Final inventory is identical in all exposed fields. Supplementary raw captures
also match **every field**, including disk IDs, actual AE types, popup labels,
flags, float precision and checkbox captions. All **294 PiPL bytes** match the
2025 build (resource 16000, language 1033, hash
`530e5aec57fb1ad83f202245a700d1f1ae029c263fda4b0ac17faa8f10d96015`).
The supplied 2026 build has SDK minor 29 rather than 28; the candidate targets
the primary 2025 declaration. 2026 sample render equality does not mean its PiPL
is byte-identical to the 2025 candidate.

## Cube root and function-level evidence

The AEX imports **`cbrtf`**, through `api-ms-win-crt-math-l1-1-0.dll`.
Live render recording resolved it to **System32 ucrtbase.dll 10.0.26100.9711**,
SHA-256 `dedb7611e1abc1ff3852dcac3d4c93a048d729e25b061973b9969f22698f14ca`,
RVA **0x54ed0**. This is not `cbrt`, `powf`, or an AEX-local cube-root routine.

Read-only disassembly shows scalar binary32 normalization, a rational estimate,
one refinement and exponent reconstruction, with no FMA dispatch. Functional
constants at provider RVAs `0x1029e0..0x1029f4` are retained as exact float words
in `src/oklab.rs`; basic operations use `olm_math::x86`. No system libm or
expected-output table is called by production Rust. Special values preserve
the observed input bits, including signaling NaNs. The implementation is
**OLM-internal**, and `oklab::cbrtf` is an **olm-math hoisting candidate**.

| Evidence | Observed result |
| --- | --- |
| UCRT direct test, 1,000,000 xorshift words + 33,280 exponent-boundary probes + 9 special words | **1,033,289 raw-word matches** |
| Native witness / diverge, each matrix on 128 RGBA vectors, including signed/HDR leaf inputs | **256/256 exact** |
| Native `0xc110` versus actual Rust whole-plane builder, every 7×5 pixel, versions 1/2/3, ranges 0/.1/1.7/2/2.9/49.9/100 | **735/735 exact** |
| Real Smart8 recording, four forward matrices, four inverse matrices, twelve cbrtf calls | **20 captured calls; all 40 original/Rust replays exact** |
| Oklab full renders at .1/1.7/2.9, gamma modes None/Colors/All, each depth | **27/27 exact; gamma mode does not alter any output word** |

The cube-root test is sampled, not exhaustive over all 2³² words. Return bits
under nearest rounding/gradual underflow are the contract; errno, FP exception
flags and alternate rounding modes are excluded. Signed/HDR matrix probes do
not establish arbitrary HDR/NaN whole-frame behavior.

## Old-to-new triage, localization and compatibility

The existing U-triage report supplies the old/new behavior and full matched
parameter sensitivity sweeps. Its omitted retyped range is covered here by an
explicit same-slot integer-domain sweep: versions 1/2 × ranges 0/1/2/3/50/100
at all depths, giving **30 changed and 6 exact** renders, with no failures.
These are intended upstream deltas, not failures of the updated port. A default
v2/range-2 Smart32 pair was classified by ubdetect with three independent
renders per side: **stable_mismatch**, no observed instability. Final updated
candidate comparisons have no residual mismatch to exclude or classify as UB.

Independent old/new native classifier calls localized the first changed output
to the top-right classification byte at pixel (5,2) of a 7×5 plane. A bounded
minimization reduced 87 nonzero input words to **one alpha word**, with a fresh
replay and complete single-word-zeroing minimality check. This proves the
isolated boundary change; it is not a claim of global image/parameter minimality.

This job's funcdb run classified the 574 new functions as **516 exact, 19 fuzzy,
39 unknown**. The prior triage's 17 referenced-data change candidates map to
existing geometry routines; normalized matches abstract callees/global state
and do not independently qualify those functions. Updated setup, converters,
classification, gamma/output and UI code were inspected in this job's isolated
hub. Existing geometry/scanners were retained and exercised by the tests and
full oracle corpus; no output tuning or broad geometry rewrite was made.

All 15 control slots and disk IDs, match name and defaults are preserved except
the original's explicit declaration changes. **Migration risk:** same disk ID
5 now carries a float instead of an integer. Native AE's old-project/keyframe
conversion remains untested; no conversion absent from the original is added.
Versions 1/2 follow the new edge behavior. The pure integer `Params` API remains
compatible; `render_with_range` supplies fractional UI values to the same pipeline.

The existing C++ reference remains unchanged outside this crate. Its extracted
test-only class loop receives the two explicitly documented new-release deltas
(right boundary and range multiplication) in `build.rs`. Consequently the
full-frame C++ tests are regression checks with a documented adapter, **not an
independent new-original oracle**. Native leaf and whole-AEX comparisons above
provide that authority.

## Reproduction, identity and remaining shared work

See [README.md](README.md) for build/test commands. The final candidate is
`upstream-work/OLMSmoother2-final.aex`, identical to
`D:/olm-rs-target/Up-smoother2/release/olm_smoother2.dll`, SHA-256
`a84f8850d0bc5d026f30711592c5c8715c1d2d665e8ed11d44828eed23a854b7`.
The primary original is `add776af61499d425f3978f4e5e4c2c8b4062db6d7276db66a22928749227137`;
2026 is `d56118d170b2eb8c6a4f7708486ba221c7e71271a87becce907db13a29fa9ac5`.

`run_upstream_validation.py --resident` generated the final campaigns;
`supplement_upstream.py` generated old-domain and gamma probes;
`summarize_upstream.py` binds the completed evidence. The 2025 raw declaration
comparison is `upstream-work/declarations-final-comparison.json`.

Shared changes required outside this job's ownership:

- Golden regeneration only publishes after an all-ten run. `--only` is
  diagnostic, so **54 Smoother2 golden hashes must be regenerated by the tool
  owner against the new original**, with Oklab/fractional tuples added. Shared
  golden manifests were not changed. The existing Mac packaging checker also
  uses C++ declaration baselines and must account for the upstream version change.
- Hoist the qualified local `cbrtf` implementation into olm-math.
- Give the hub an explicit per-instance data/project directory option. The local
  launcher currently overrides its fixed defaults without editing shared tools.
- Let the diverge reducer declare input dtype independently of output dtype.
  Its stock guard rejects this u8-output/f32-input classifier. A local wrapper
  changes only that guard; native comparisons, budget, input checks and final
  replay remain the shared implementation.
- Add Smoother2 adapters to the record replay dispatcher. The local replay bridge
  uses the unchanged witness and verifies exact recorded inputs/outputs/provider
  hashes for all 20 calls.

Ghidra hub PID **4744**, port **8783**, was stopped gracefully. Its shutdown
record reports `exited=true`, `forced=[]`, `remaining=[]`; subsequent status was
`running=false`. Native witness/record/ubdetect jobs verify child cleanup; oracle
processes use the shared Windows Job lifecycle and all campaign parents were
awaited to exit 0. Only this crate was edited. No AE/GUI, installation, commits,
pushes, subagents or shared tool/source edits occurred.

---

# Historical 2.1.0 module split and staged validation

1. `types.rs`, `frame.rs`, `lut.rs`: RGBA scratch types, PF8/PF16 loading and packing,
   key filtering, sRGB transfers and the captured 10,000-entry LUTs. Compare each
   kernel with the unchanged C++ frame-setup include before proceeding.
2. `scan.rs`: classifier and eight axial/six diagonal scanners; test every
   location of deterministic class planes, including boundaries and padded rows.
3. `gamma.rs`: palette membership, gamma/premultiply, scalar composite and
   post-unpremultiply; compare raw float words with C++ across polygon sizes.
4. `polygon.rs`, `weights.rs`, `geometry.rs`, `geometry_generated.rs`:
   bounded 12-vertex storage, corner samples, coverage weights, all cardinal
   families and the 222-case switch. Verify each family before full-frame tests.
5. `algorithm.rs`: class-plane construction and full staged render, checked
   allocations, deterministic row parallelism and C++ full-frame comparisons.
6. `ae.rs` and PiPL in `build.rs`: only after the pure pipeline passes; preserve
   original parameter slots/disk IDs, dynamic controls, SmartFX ownership and
   admission/refusal rules. Follow the pilots' binary PiPL embedding and aliases.
7. Original-AEX inventory and Smart8/16/32 oracle campaigns: at least 200 random
   cases per depth across two seeds, downsample 1, 1/2, 1/4, `--jobs 3` and equal
   host deadlines on both sides. Record failures separately from exact renders.

## Status

The pure render pipeline and AE adapter are implemented. **20 release tests pass,
zero failures.** All 222 polygon dispatch labels are translated mechanically.
Original-AEX inventory is identical; the complete 294-byte Windows PiPL is identical.
The final original-AEX campaign passed **618/618 comparisons**: **206 per depth**,
including **200 randomized cases per depth across two seeds**, with zero pixel
mismatches, reference failures, candidate failures or timeouts. Downsample 1,
1/2 and 1/4 are all covered. No requested port stage remains unfinished.

| Seed | Smart8 exact | Smart16 exact | Smart32 exact | Random cases per depth |
| --- | ---: | ---: | ---: | ---: |
| 20261116 | 103 | 103 | 103 | 100 |
| 20261117 | 103 | 103 | 103 | 100 |
| Total | **206** | **206** | **206** | **200** |

Each depth has 70 exact cases at downsample 1, 68 at 1/2 and 68 at 1/4.
Of those, 68/66/66 are randomized; six are default/min/max checks across the
seeds. `campaign-summary.json` binds the totals and per-seed details to the
frozen binary. `inventory-verified/summary.json` confirms the delivered
candidate's inventory; `pipl-comparison.json` confirms all 294 resource bytes.
Earlier smoke/regression renders are additional evidence and excluded from
these final campaign counts.

The delivered test candidate is `OLMSmoother2-verified.aex`. Earlier DLL copies
and interrupted campaign directories are diagnostic history, not final evidence.

## Measured C++ comparisons

The reference TU includes the actual unchanged C++ files. For gamma and class
plane code, `build.rs` extracts unchanged bodies using explicit source markers;
it fails if those markers disappear. A wrapper supplies arguments and returns
results; expected algorithms are not separately reimplemented in the tests.
Production Rust code has no calls to `sm2_ref_*`. As in the pilot, Cargo builds
the reference archive, but only `#[cfg(test)]` code references its functions.
C++ uses clang-cl, C++17, contraction off, fast math off, release optimization.
Both sides use the same already-qualified `olm-math` UCRT implementation: these
are translation tests, not new independent qualification of UCRT.

| Stage | Actual comparison coverage | Result |
| --- | --- | --- |
| PF8/PF16 load and pack | All 256/65,536 integer codes, each loaded and packed; additionally 20,000 random raw-float PF16 packs and finite random PF8 packs | Raw exact |
| Transfers | 50,008 inputs each for literal decode, decode LUT, encode LUT: every one of 10,000 knots and adjacent words, special endpoints, 20,000 random normalized floats | 150,024 raw exact calls |
| Frame leaves | 512 × 37 pixels × four operations (unpremultiply, palette, scalar key, runtime decode); empty/full palettes, hits, threshold boundary, hidden RGB, NaN channel | 75,776 pixel comparisons exact |
| Classifier and attenuation | All 32 boolean classifier combinations; 20,000 trapezoid cases | Exact |
| 14 scanners | Seeds `0x5162`, `0x20261112`, each 486,528 outputs; 48 plane patterns, sizes 1×1, 1×7, 7×1, 3×7, 11×9, 31×19; every coordinate; row padding 0–4 bytes | 973,056 exact outputs |
| Gamma stages | Polygon counts 0–12, 512 cases/count, four stage calls/case; gamma 0/0.1/0.5/1/2.2/5/10, negative/zero/one alpha, weights outside [0,1] | 26,624 exact stage calls |
| Gamma palette membership | Versions 1/2, modes None/Colors/All, palette counts 0–5, center/sample hits and misses | 4,608 exact cases |
| Exceptional scalar arithmetic | Signed zero, infinity, signed/payload NaNs and sNaN pairs; gamma disabled; premultiply/composite/post-unpremultiply | 192 exact stage calls |
| Curves and literal encode | 20,000 inputs, eight curve indices; 20,000 binary64 literal encode calls | 180,000 exact calls |
| Coverage weights | All 16 endpoint keys, spans 4–256, offsets −2 through span+2, both C++ scalar-rounding flags | 1,092,960 exact pair calls |
| Coverage lines | 20,000 random segments, both C++ flags | 40,000 exact line calls |
| Corners and normalization | Five sizes, every coordinate, all 16 corner masks, normalization on/off, pixel-strided padding | 4,320 exact polygons |
| Class plane | Six sizes, 48 patterns, six Smooth Range values (0/1/2/3/50/100), including transparent and nonfinite pixels | 1,728 frames exact at each of 1/3/7 threads |

| Directional leaves | Two seeds, 512 descriptor/class patterns per seed, all 32 leaves | 32,768 exact results/counts/vertices/weights |
| Complete polygons | Two seeds, four dimensions, 256 patterns, five positions; all 256 switch indices forced at interior pixels | 10,240 exact polygons |
| Full float render | Two seeds, four sizes, 144 parameter/pixel patterns each; setup through final RGB transfer/premultiply | 1,152 frames exact at each of 1/3/7 threads (3,456 comparisons) |
| Source identity SHA-256 | Actual C++ core header; lengths 0?256, 1024, 8192, 65536 | 260 exact digests |

## Reproduction and identity

From the repository root:

```powershell
python rust/plugins/olm-smoother2/generate_geometry.py --stage all
python rust/plugins/olm-smoother2/validate.py
python rust/plugins/olm-smoother2/run_campaign.py
python rust/plugins/olm-smoother2/summarize_campaign.py
```

`validate.py` sets `CARGO_TARGET_DIR=D:\olm-rs-target\P-smoother2` and runs only
`cargo build/test --release -p olm-smoother2 -j 2 --offline`. It binds source,
reference, LUT, binary, harness and worker hashes in `validation-report.json`.
`run_campaign.py` runs seeds sequentially, each with `--jobs 3`, `--cases 103`,
`--routes smart8,smart16,smart32`, `--downsample 1,1/2,1/4`, `--timeout 120`.
Both sides receive `AEXCOMPAT_FRAME_DEADLINE_MS=120000`. Output directories must
be new; archive names in the runner must be changed before intentionally rerunning.

| Artifact | SHA-256 |
| --- | --- |
| Original OLMSmoother2.aex | `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7` |
| Delivered candidate | `a5196bd1bfab23fbfc82c30c6eaf168b64d9fc9139ea513d37bbe80bae551609` |
| Built DLL | `c901503de5f3e360745970d7a30bcf1bb530e66fea7513c5a05ef43005f12771` |
| Harness | `81676eae08b30ee60ad95c29dcf227324755bc0dec7a436ac77f4686e72b3d27` |
| Worker | `0481df5fa425af28f0e8a39ea9386185de13656c3c9d488042bed2244bdf8302` |

The later test-only addition produces a new linker timestamp/PDB GUID. The frozen
campaign AEX and rebuilt DLL are byte-identical after excluding only PE/debug
timestamps and the 16-byte PDB GUID (`rebuild-equivalence.json`); all executable,
data, unwind, relocation and resource sections match. The full candidate SHA
above is the identity used for final oracle counts.

## Translation and adapter details

- `generate_geometry.py` is retained in the crate. It recognizes only the C++
  subset present here, rejects unknown statements, preserves expression order,
  all 222 labels and explicit switch fallthroughs, and omits diagnostic-only
  trace/histogram branches. `geometry-generation.json` binds each translated
  function to its C++ source hash. Normal diagnostic selector values remain zero.
- `geometry.rs` bridges the generated code to verified scanners, coverage weights
  and checked 12-vertex storage. Synthetic arbitrary class bytes at boundaries
  can send the unchanged C++ append outside its allocation. Boundary comparisons
  therefore use real class planes; interior tests explicitly force all 256 indices.
  Rust rejects out-of-bounds appends rather than reproducing undefined memory reads.
- `algorithm.rs` preserves setup, class generation, polygon, adaptive gamma,
  premultiply, separate scalar composite, post-unpremultiply and final LUT order.
  Count-zero polygons bypass gamma/compositing. All depths use captured runtime
  decode/encode LUTs and separate scalar composite, exactly as current C++ does.
  PF8/PF16 loads and packs are separately compared; PF32 writes raw words.
- `ae.rs`, `ae_setup.rs`, `ae_boundary.rs` and `dynamic.rs` retain original slots,
  disk IDs, defaults (including white key), flags, dynamic controls, SmartFX RGB
  preservation and the `entry_point` alias. The shared pilot boundary is copied
  locally only where this plug-in needs additional behavior: active-color-only
  suite fetches, source-bound admission, release error propagation, and publishing
  staged output after successful checkin. No shared source was changed.
- Public classic rendering is refused. Generic Smart admission preserves the
  C++ 1?8192 dimensions, ranges, versions, finite gamma, matching depth (the historical origin restriction is removed by F-smoother2-roi),
  nonoverlap and signed row-span limits. `admission.rs` retains the stronger
  source/parameter fixture union and its world flags/origin/downsample contract.
  `sha256.rs` translates `core/olm_sha256_rows.h` for that source identity check.
- Windows PiPL follows the pilots' binary-resource embedding, including the
  two-byte eINF declaration. macOS entry/resource declarations are present but
  have not been built here.

## Investigation history

The first adapter smoke campaign (`oracle-smoke`) passed 36/36 renders. The
transactional-output revision then failed before rendering because it asked the
host for the format of a copied temporary world. The host recognizes its own
world pointers. Format validation now runs on the original checked-out worlds
before staging. `oracle-adapter-fix` confirms the corrected path at every depth
and downsample. A focused mock-host regression also verifies original-world format queries,
immutable input, one checkin, balanced suite releases and unchanged output on
a late checkin failure. No numerical constants were tuned; no pixel mismatch was fixed
by approximation.

Three interrupted campaigns are excluded from final counts:
`oracle-seed20261116`, `oracle-final-seed20261116`, and
`oracle-final-v2-seed20261116`. A shell interrupt did not stop their Python
children. Exact task-owned parent PIDs and descendants were identified, stopped,
and verified absent; `cancelled-processes.json` records ownership. Both final runs exited 0 and were awaited normally. The oracle itself uses per-invocation Windows Jobs,
waits for child exit, terminates remaining descendants and verifies zero active
processes before closing the job.

## Remaining limits and validation outside this job

- No native AE, macOS build or GPU validation is claimed. No GUI was opened
  and AE was never launched or touched. The requested Windows CPU port,
  staged reference tests, inventory/PiPL and two-seed oracle campaign are complete.
- AEXCompat reports `source_newer_than_worker`; evidence is tied to the supplied
  binary worker hash, not unbuilt host source. This is host-emulator evidence.
- The C++ polygon/cardinal reconstruction remains public-beta scope; matching
  this corpus does not prove every image, scan length or parameter combination.
  The source-bound retained fixtures are preserved in code, but their large
  native-host fixture corpus was not rerun in this job.
- Full-render tests exercise public modes only. The unreachable internal
  luma-adaptive mode is not exposed; its six curve leaves remain tested.
- PF8 NaN-to-integer packing has no portable C++ contract. Nonfinite scalar
  kernel tests do not establish arbitrary nonfinite full-frame behavior.
- Coverage weight comparisons cover spans 4?256 and the listed random segments;
  this is not an exhaustive geometry proof. Invalid nonfinite integer casts
  are refused by the Rust coverage primitives.
- Potential shared-crate candidates: source-identity SHA-256, nonblack color
  defaults and transactional SmartFX output. No new third-party package beyond
  the existing pilots' `olm-ae`, `pipl`, `winres` and `cc` dependencies was added.

## Scope

Only `rust/plugins/olm-smoother2/**` is owned/edited. Build artifacts use the
assigned target directory. No commits, installs, subagents or GUI actions were
performed. C++ reference functions are used by tests, never by the Rust render
path. UCRT combined artifacts remain OLM-internal and must not be published
standalone.

## Integration evidence policy

All `validation/` paths, absolute machine paths, build outputs, `.aex`/`.dll`
files, process logs, raw pixels and `candidate-path.txt` references above or in
linked JSON reports are **local-only evidence**. They remain on disk and are
ignored by Git. Compact root-level JSON reports, source/test vectors and rerun
scripts are retained for version control. Historical source/binary hashes bind
the original job's snapshot, not the later integrated build; see
[workspace integration](../../INTEGRATION.md) for the fresh staged cross-check.

The `campaign-*`, `inventory-*`, `original-inventory-run`, `oracle-*` and
`standalone/` directories are also **local-only evidence/build workspaces**.
Root-level campaign-summary, geometry-generation, rebuild-equivalence,
rebuild-sections, process records and validation-report JSON are retained.

## Performance implementation (S-smoother, 2026-11-13)

The AE adapter now requests available CPU parallelism instead of hardcoding one
worker. Setup (copy, color key, transfer LUT and Oklab), classification and
smoothing operate on independent row chunks. The crate-local row scheduler caps
workers at available_parallelism and uses at least 16K pixels per worker; small
frames and explicit one-worker calls execute inline. Every scope joins before
returning, with no global mutable state or persistent worker pool. Floating-point
operations and per-pixel sample accumulation order are unchanged. `olm-math`
and its scalar cbrtf are unchanged; no local or vector cube root is substituted.

`examples/profile.rs` provides reproducible 1080p phase timings. In the bounded
24-logical-CPU diagnostic, serial v2 setup took 22-31 ms and Oklab setup 106-121
ms. Three scalar cbrtf calls per pixel took 71-82 ms; serial class planes took
15-26 ms. Complete pure pipelines took 435-583 ms with one worker and 68-95 ms
with the available workers. These are diagnostic samples on a shared machine,
not the host benchmark medians or a claim of exclusive CPU attribution.

The added 257x193 full-frame test crosses the parallel threshold with uneven
chunks and compares exact float words for requested workers 1/2/3/usize::MAX,
all three versions, all gamma modes, fractional range, color key/inversion,
extra smoothing and premultiplied output. The existing C++ and adapter tests
remain active. No parameter or host-contract changes are introduced.

### Historical performance result and ROI gate (superseded by F-smoother2-roi)

1080p Rust/original wall-time ratios (lower is better), baseline -> optimized:

| Depth | Default | Heavy |
|---|---|---|
| 8 | 1.153 -> 0.302 | 1.339 -> 0.187 |
| 16 | 1.191 -> 0.355 | 1.152 -> 0.196 |
| 32 | 1.357 -> 0.276 | 1.199 -> 0.181 |

Separate baseline/final sweeps on a shared machine; no exclusive CPU claim.
The final sweep had no overlapping build from this task. All six cells were
exact. Scalar UCRT cbrtf remains a major setup cost; parallel rows avoid any
unproven replacement. Output packing/copying is another remaining cost.

Release tests: 21 passed; fmt check passed; release clippy completed successfully
with warnings. Golden: 54 exact. Two seeds (20261121/20261122), 103 cases per
depth per seed, including 100 randomized cases and all three downsample factors:
618 exact, zero errors within the existing full-world boundary contract.

The extra per-process cropped-output campaign is NOT passing. Extent 1,1,7,5
with 11x9/31x19 inputs produces 6x4 output worlds. All 27 optimized cases failed
with smart_render_error 516; all 9 baseline repro cases also failed with 516.
The adapter already requires equal input/output dimensions and origin. This is
a preexisting compatibility gap, not evidence that ROI support is complete.

Bounded investigation rejected full-pipeline cropping, host resizing after the
pipeline, and host resizing before the pipeline. The original visibly resizes
the whole image; the exact processing/resampling order and float/color domain
remain unresolved. All experimental boundary changes were reverted. Self-review
(no agents authorized) separated this existing host-contract issue from the
validated speed changes after three rejected principal hypotheses. Further work
needs an original-side call/order trace or a small discriminating resampling
fixture, rather than another guessed boundary implementation. The job's required
ROI gate is unmet, so no PR is opened; the pushed branch is a review checkpoint.

Local-only evidence under D:\olm-rs-target\smoother: accepted-tests.log,
accepted-fmt.log, accepted-clippy.log, accepted-golden-v2.log, oracle/,
oracle-roi/, roi-baseline/, roi-fixed/, roi-host-check/, roi-resize2-check/,
bench-before/evidence.json and bench-serial/evidence.json. serial-audit.json
passed all 10 combined benchmark cells, 60 frame pairs, 120 PNGs and 72 deep
files. Tested accepted/OLMSmoother2.aex SHA256:
a209bff96fe6c8d66d3d06a0fbefc79788e9934ff46c18cab8bfc245a6fc97a5.
Rebuild DLL hashes can differ; the benchmark binds the staged binary above.

### Historical Round 2 ROI classification (resolved by F-smoother2-roi)

The bounded recheck on 2026-11-13 establishes a candidate boundary defect in
AEXCompat, not an incorrect expected image or an observed original defect.
On identical generated requests, the original succeeds; original-vs-original
is exact in all 9 cases (3 per Smart8/16/32). Both perf commit 5e73f15d and a
fresh origin/main 201885611eb89e3ea6b2f69fc3354d95fffc36bf build fail all 9
cases with smart_render_error 516. The pre-perf baseline previously failed the
same 9 cases. Source boundary ae_boundary.rs explicitly rejects unequal input
and output width, height or origin before the pipeline. No performance change
modifies that check. Main binary SHA256:
67a1df1aecae5fe9ea1d49175b81fd8c68e9ab74d07fbde9ee52436e08516f95.

Minimal reproduction from repository root (substitute absolute binary paths):

```powershell
python -X utf8 rust/tools/oracle/olm_oracle.py render --reference ORIGINAL.aex --candidate RUST.aex --routes smart8 --cases 1 --seed 20261123 --jobs 1 --downsample 1 --sizes 11x9 --extent 1,1,7,5 --out NEW_DIRECTORY
```

For the recorded 9-case check use --routes smart8,smart16,smart32 --cases 3
--downsample 1,1/2,1/4 --jobs 2. Repeat with ORIGINAL.aex as candidate to
check original determinism. Case zero has untouched defaults, 11x9 input and
6x4 output; input PNG SHA256 is
5573ff307a3908a7c90ccd9647c0ce911e7c650bbe98527df19136ff35de8018;
successful original PNG SHA256 is
fa9595f0a715e16a712f670987ab70c78c044ed8f9d07f310755efce8db1c010
in each campaign. Full requests, deep outputs, errors and binary identities:
D:\olm-rs-target\smoother\round2-roi-{main,perf,original}/summary.json
and case-* subdirectories. No reference render failed in these campaigns.

This is deferred to a separate compatibility job: prior crop/resize hypotheses
did not reproduce the original processing order, so a small verified fix is
not available. Per the Round 2 instruction, this unchanged documented defect
does not block the performance PR. The previous no-PR decision is superseded.

### Round 2 final evidence and lint cleanup

Fresh final 1080p benchmark (Rust/original):

| Depth | Default | Heavy |
|---|---:|---:|
| 8 | 0.342 | 0.179 |
| 16 | 0.329 | 0.186 |
| 32 | 0.265 | 0.153 |

All six cells remain below 1 and exact. This is a separate shared-machine sweep;
the changes since Round 1 are lint cleanup, not further math/parallel algorithm
optimization. Scalar cbrtf and shared olm-math remain untouched. Clippy fixes
make unordered float comparisons explicit with partial_cmp, retain exact
binary64 literal rounding, remove redundant casts, and name a fixture tuple.
Generated geometry has narrow documented style allowances; source clamps retain
branch order for NaN payloads and signed zero. Test/example lints are also fixed.

Final release tests: 21 passed; 54 goldens exact; 618 two-seed full-world oracle
comparisons exact with no errors/mismatches (103 per depth per seed, all three
downsamples). Formatting passes; all-target release Clippy reports zero owned
Rust warnings. Shared dependency and native C++ reference warnings remain.
The combined benchmark audit verifies all 10 cells / 60 frame pairs exactly.

The final candidate repeats the same ROI failure: round2-roi-final has 9/9
candidate failures with error 516 and no original failures. All nine reference
PNGs were also identical across the main/perf/original classification campaigns.
The defect remains classified (b), unchanged and deferred; no failing case is
counted as an exact comparison.

Local evidence under D:\olm-rs-target\smoother: round2-byte-bench/evidence.json,
round2-final-{report,audit}.json, round2-clean2-tests.log,
round2-clean2-clippy.jsonl, round2-final-golden-olm-smoother2.log,
round2-oracle/ and round2-roi-final/. Final benchmark/oracle AEX SHA256:
dad3a101117257fa0ded1cec3f19011264359ab7d6c1fc9328b6131173dc49d2.
