# Binary-Grounded IR: OLMColorKey Edge Thin / Edge Blur

## Feature

- Plug-in: OLM Color Key
- Feature/path: 8bpc Edge Thin erode/dilate and Edge Blur after core keying
- Bit depth: 8bpc normalized Software is documented here; 16bpc has one active
  Mac AE residual after the Force Lower Precision fix; 32bpc still needs
  references
- Current status: packaged 8bpc AE-host return is exact for core RGB,
  Edge Thin, and Edge Blur against the 20260618 normalized Software reference
  generation. The apparent Edge Blur stress `case_0009` residual is now a
  reference-generation split against the older 20260604 PNG, not a clean
  algorithm witness. AE-free CLI residuals remain useful diagnostics, but they
  are not current proof that the Mac AE path is wrong.
  For 16bpc, ColorKey is 8/9 exact after the binary-grounded `Force Lower
  Precision` epsilon fix. The remaining case is not an Edge Blur blend path:
  it is `case_0009` with Lab76, `Force Lower Precision=3`, `Edge Thin Amount=25`,
  `Edge Thin Distance Type=2`, and `Edge Blur Amount=0`.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Core RGB/color-space/Replace is separate from the current residual. | `notes/OLMColorKey_ASM_FACTS.md`; core and Replace/color-space smokes exact or guarded independently. | reference-backed |
| Edge Blur distance type dispatch is read from `ctx+0x44`. | `FUN_1800094b0` dispatch to `FUN_180006e20`, `FUN_180005d60`, `FUN_180007ec0`. | binary-grounded |
| Edge Blur seed world is produced by `FUN_180008c90`, which marks keep-side inner boundary seeds. | Static Ghidra facts in `notes/OLMColorKey_ASM_FACTS.md`. | binary-grounded |
| Edge Blur Distance Type 1 must not be forced to Euclidean. | Only `FUN_180007ec0` squares and square-roots; current implementations route by distance type. | binary-grounded |
| Positive Edge Thin copies when `dist <= amount`. | 8bpc positive loop compiles to `COMISS amount, dist; JC skip`. | binary-grounded |
| PNG-fit probes that use drop-side seed, direct Direction=3 formula, or `< amount` are rejected without runtime proof. | `notes/OLMColorKey_ASM_FACTS.md`, 2026-06-19 rejected probes. | negative evidence |

## Current Residuals

- AE-host exact validation returned on 2026-06-18 should be read separately
  from the AE-free CLI residuals:
  - `case_0001..0008` were exact in the returned Windows Software AE-host
    render set.
  - `case_0009` remained non-exact (`max=47 mean=0.069921`).
  This does not prove the Mac plug-in is final, but it does show the current
  final-risk slice is primarily Edge Blur `case_0009`.
- 2026-06-21 provenance audit splits the `case_0009` AE-host residual into a
  reference-generation issue:
  - the returned AE-host candidate is an exact pixel match against
    `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey/case_0009.png`
    and the C++ CLI `reference/case_0009.png`;
  - the same candidate reproduces the reported `max=47 mean=0.069921` only
    against the older `refs/win_references/20260604_olm/OLMColorKey/case_0009.png`;
  - the old-reference residual is mostly alpha (`channel max RGBA =
    [7, 7, 33, 47]`, max witness `(1678,722)` old ref alpha `136`, candidate
    alpha `89`).
  Therefore `case_0009` is no longer a clean algorithm witness until the
  canonical Software reference generation is chosen. Use
  `scripts/analyze_colorkey_edge_reference_provenance.py` before treating this
  case as a porting failure.
- 2026-06-22 rerun of the provenance audit writes
  `refs/reports/olmcolorkey_edge_reference_provenance_20260622_005112/`.
  It confirms the exact split with repo-relative paths: the 2026-06-19
  candidate is exact against both the 20260618 normalized ref and the C++ CLI
  reference, while the older 20260604 PNG alone reproduces
  `max=47 mean=0.069921031`. Treat the normalized 20260618 generation as the
  active 8bpc Software reference for this slice unless a future Windows
  recapture contradicts it.
- 2026-06-22 follow-up audit
  `refs/reports/olmcolorkey_edge_reference_provenance_20260622_024907/audit.md`
  promotes that conclusion into a machine-readable classification:
  `reference-generation-split`. The generated JSON now records the reason and
  recommended action: prefer normalized 20260618 refs and do not tune Edge Blur
  from the older 20260604 residual.
- `scripts/analyze_soft_reference_canonicalization.py` now folds all nine
  ColorKey AE-host candidates into the cross-feature 8bpc Software audit:
  `refs/reports/software_reference_canonicalization_8bpc.md`. That report
  classifies ColorKey as `normalized-software-exact` for 9/9 cases, with only
  the old `case_0009` reference drifting.
- 2026-06-24 decision matrix
  `refs/reports/olmcolorkey_edge_decision_matrix_20260624/decision_matrix.md`
  consolidates the provenance and cross-feature canonicalization result:
  normalized 8bpc is `9/9 exact`, the legacy `case_0009` drift is
  `reference-generation-split` with max `47`, and the current runtime trace
  comparison is `not-actionable` because no concrete Windows Edge values are
  present. Preserve the normalized AE-exact behavior; do not tune Edge Blur
  from the 20260604 residual.
- Edge Thin erode, current legacy cases `case_0005` / `case_0006`:
  - C++ CLI guarded residual: `max=255 mean=0.3031`.
  - The Windows AE-host exact return had both cases exact, so the CLI residual
    is currently classified as AE-free shim/algorithm gap rather than proof that
    the Windows host reference itself is inconsistent.
  - High-diff witnesses include top-edge pixels such as `(34,0)`,
    `(421,0)`, `(993,0)`, and `(421,1)`.
  - Candidate/reference differ in alpha polarity between `case_0005` and
    `case_0006`, which points to erode-shell / boundary handling rather than
    core key comparison.
- Edge Blur current legacy cases:
  - `case_0008`: C++ residual `max=15 mean=1.1104`; Python residual
    `max=26 mean=1.1044`.
  - `case_0009`: `max=255 mean≈1.25..1.32`; high-diff witness around
    `(1116,136)` where the current candidate remains fully opaque but Windows
    reference is transparent.
- 2026-06-19 boundary/distance probes are not promotion candidates:
  `refs/reports/ae_host_validation_20260618_232926/color_key_edge_blur_boundary_probe_20260619_001018/edge_blur_boundary_probe_summary.md`
  shows drop-side matte variants lower the combined CLI mean
  (`case_0008 max=39 mean=0.149777`; `case_0009 max=255 mean=0.280201`) but
  they make `case_0008` worse than the current C++ path (`max=15`) and lack
  binary proof for the seed/apply world. Treat them as a runtime-trace
  hypothesis only, not an implementation fix.
- Mac baseline trace logs for normalized Software edge witnesses are stored at
  `refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/`.
  The sharp Edge Thin witness is `case_0005/0006` at the top edge:
  `edge_thin_dist=17` and `edge_thin_limit=17`.
- 2026-06-20 dense/live trace returns are now classified as too sparse for a
  semantic change. The dense summary mostly carries Mac-baseline placeholders
  such as `Mac baseline edge_blur_dist=...` / `not isolated`, and the live
  follow-up hit `+0x94b0` / `+0x8c90` before an OLMColorKey access violation
  but did not capture concrete edge sample values. The comparison helper now
  ignores explanatory strings for focus selection, so both existing returns
  report `trace-too-sparse`.
- 2026-06-26 Mac AE 16bpc rerun after the Force Lower Precision fix:
  - `olmcolorkey__case_0008` is exact.
  - `olmcolorkey__case_0009` remains non-exact with `max=65535`,
    `mean=100.9161`, and `0.6075%` nonzero pixels.
  - Every sampled residual pixel has `candidate == before_effects` and
    `reference alpha == 0`, which means the current Mac path is keeping pixels
    that Windows removes.
  - The case parameters are `Color Keep=0`, `Color Space=3`, `Per Color=1`,
    `Per Component=1`, key color `[1, 0, 0.470588...]`,
    component thresholds `[0.19, 0.98, 0.4]`, `Edge Thin Amount=25`,
    `Edge Thin Distance Type=2`, and `Edge Blur Amount=0`.
  - Therefore the active 16bpc gap is a positive Edge Thin dilate / seed-world
    disagreement around the Lab76 key result, not an Edge Blur weight/blend
    residual.
  - Focused report:
    `refs/conformance/olmcolorkey_16bpc_case_0009_analysis.md`.
    It records that the real Mac AE candidate differs from Windows by
    `12597px`, all in the `candidate-kept / Windows-removed` direction.
    A naive `Lab76 hit + taxicab dilate amount=25` model is much worse
    (`80592px` diff with `65535` input normalization), and forcing a
    `32768/32767` denominator makes that naive model dramatically worse
    (`189628px`). So the missing rule is narrower than a global 16bpc
    denominator switch.
  - The same focused report also sweeps obvious seed/dilate variants:
    direct hit seeds, boundary seeds, clamp-vs-outside frame handling,
    taxicab/chessboard/euclidean distance, and `<25` / `<=25` / `<26` /
    `<=26` threshold choices. None beat the naive taxicab model; the best
    family still bottoms out at `80592px`. So the remaining gap is not a
    simple choice among those common morphology variants.

## Current Port Rules

1. Build `matched` from core key comparison.
2. Apply Edge Thin only when Replace is disabled:
   - erode: compute distance to non-matched pixels, then keep matched pixels
     when `dist > abs(amount) + L1/chessboard compatibility bias`;
   - dilate: compute distance to matched pixels, then include pixels with
     `dist <= amount`.
3. Build `keep_mask` from `Color Keep` and post-Edge-Thin `matched`.
4. Edge Blur:
   - compute `Boundary8(keep_mask)`;
   - dispatch distance transform through the same distance-type mapping as
     Edge Thin;
   - compute sine-ramp weight;
   - scale the selected source pixel by that weight.

These rules are implementation-grounded, but the residuals show at least one
caller/world semantic is still missing.

For the current 16bpc residual, the missing semantic is more specific:
Windows removes additional pixels that are still input-identical in the Mac AE
candidate, so the mismatch must occur before final writeback. The two strongest
suspects are:

1. the Lab76 matched seed world feeding positive `Edge Thin Amount=25`; or
2. the L1 distance/dilate ownership around that seed world.

## Open Questions

- Does `FUN_180008320` treat image borders as outside/inside seeds differently
  from the current clamped-neighbor `Boundary8` / distance transform path?
- For erode, is the effective threshold `abs(amount)`, `abs(amount)+1`, or a
  ctx-scaled value at runtime for the legacy `case_0005/0006` path?
- For the 16bpc `case_0009` dilate path, does Windows build a larger matched
  seed world than the current Mac port before `dist <= amount` is applied?
- For the same case, is the positive dilate world keyed from post-Lab matched
  pixels, a pre-thin temporary matte, or a runtime-quantized lower-precision
  view of the source?
- Which world does `FUN_1800049a0` and the Edge Blur apply helper consume:
  current keep mask, pre-thin matched matte, boundary seed world, or an
  inverted/drop-side matte?
- If the runtime trace confirms a drop-side seed/apply world, it must also
  explain why Windows AE-host `case_0008` is exact while current CLI drop-side
  probes worsen `case_0008` to `max=39`; otherwise the probe is likely fitting
  the wrong symptom in `case_0009`.
- Does Edge Blur blend unpremultiplied RGB/alpha or use a nonzero minimum RGB
  floor before final 8bpc writeback?

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| RGB core `case_0001..0004` | 8bpc | CLI exact / AE-host exact for current refs | exact in Python/C++/Rust and AE-host return | Preserve normalized 8bpc behavior; add 16/32bpc coverage |
| Edge Thin dilate `case_0007` | 8bpc | CLI exact / AE-host exact for current refs | exact | Preserve normalized 8bpc behavior; add 16/32bpc coverage |
| Edge Thin dilate `case_0009` | 16bpc | not exact / active Mac AE residual | 2026-06-26 Mac AE rerun: `max=65535 mean=100.9161`; residual pixels are input-identical in the candidate and transparent in the Windows ref | Isolate the 16bpc positive-dilate seed world before changing blur/blend code |
| Edge Thin erode `case_0005/0006` | 8bpc | AE-host exact return, CLI residual | Windows AE-host exact; C++ CLI `max=255 mean=0.3031`; decision matrix keeps this diagnostic-only for current refs | Preserve normalized 8bpc behavior; add 16/32bpc coverage; runtime trace only if a current Software ref residual reappears |
| Edge Blur `case_0008/0009` | 8bpc | AE-host exact against normalized current refs / AE-free CLI residual | AE-host exact for `case_0008`; `case_0009` exact against 20260618 normalized ref but `max=47` against older 20260604 ref; decision matrix says preserve normalized AE exact | Prefer normalized 20260618 reference generation; next proof is 16/32bpc coverage. Runtime trace only if a current Software ref residual reappears |

## Validation Packages

- Final-style exact-only ColorKey request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmcolorkey_exact_20260619_032431.zip`
  covers `case_0001..0009` with `max_diff=0` only.
- Runtime trace request:
  `refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip`
  includes Mac baseline trace logs for `case_0005/0006/0008/0009`.
  Existing 2026-06-20 returns did not answer the core sample questions, so a
  future request should be narrower and should emit typed numeric Windows
  values for the target witnesses rather than carrying Mac baseline text.
