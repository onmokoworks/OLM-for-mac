# OLM Mac port release completion matrix — 2026-08-06

This is the release-oriented snapshot for the ten shipped plug-ins.  It freezes
the completion target at the public major modes and the bit depths that the
original plug-in actually exposes.  `Exact` below means equality only for the
enumerated retained actual-AEX/Windows-AE fixtures.  It never means a proof for
all images, dimensions, or Cartesian parameter combinations.

The release geometry contract is:

- one or more representative small, padded fixtures per major mode and native
  bit depth, compared byte-for-byte (FLOAT32 bit-for-bit);
- one practical-resolution Software render in the current Mac AE for each
  plug-in;
- arbitrary geometry may be claimed only where the production algorithm is
  dimension-generic and the evidence includes more than one shape/rowbytes
  class.  A literal fixture guard remains a fixed-geometry implementation and
  is identified as such below.

No redundant exact-cell research is a release prerequisite.  New work is
limited to the explicit major-mode holes below; existing exact cells are frozen
regressions.  New Windows work is limited to the explicitly listed missing
host boundaries, collected as one batch.

## Frozen matrix

| Plug-in | Frozen major modes | PF8 | PF16 | PF32 | Geometry status | Remaining release work |
|---|---|---|---|---|---|---|
| OLMBlur | Legacy / NonLegacy; repeat and bias | Exact | Exact | Exact | Dimension-generic production workers; fixed fixtures prove multiple padded typed paths, not every dimension | Current installed-binary Mac AE case0001 exists; retain it as the practical host smoke and do no new Windows capture |
| ColorKeep | disabled/enabled; tolerance; 1..100 colors; duplicate/special float inputs | Exact | Exact | Exact | Dimension-generic pixel predicate and row traversal; fixed padded fixtures bound numeric behavior | Current PF8 Mac AE representative and PF16 inter-effect discriminator exist, but neither supplies a same-contract Windows AE off/on pair. Acquire one controlled Windows AE calibration at PF8/PF16/PF32; this is a host-boundary calibration, not new worker research |
| OLMColorKey | core key; Edge Thin; Edge Blur; replace/color-space surface | Exact, bounded | Exact, bounded | Exact, bounded | Core is dimension-generic, but Edge Blur exact evidence is deliberately limited to 4x3 corner/center single-key shapes and enumerated directions/amounts | Current installed Mac AE PF16 case0001 closes the practical host smoke. Release-note the bounded Edge Blur shape/amount set rather than expanding it |
| OLMToonDilate | radius copy/dilate; fractional radius; frontier/tie/corner/eligibility | Exact | Exact | Exact | Dimension-generic guarded implementation; evidence spans several shapes, padded/partial and empty worlds, radii -1..4 | Real current Mac AE load and practical representative render (one host run may cover the three project depths); no Windows capture |
| OLMDistanceGradation | Inside / Outside / Both; RGB / Layer; Constant / Linear / Sphere / Power; invert/background/blur | Exact, bounded | Exact, bounded | Exact classic, bounded | Dimension-generic field/compose code; exact axes and selected Cartesian families, not their full cross-product | Current PF32 Mac AE case0001 supplies the practical host smoke. PF32 SmartRender is not an AEX feature and is out of scope; no Windows capture unless the final selected host case lacks its retained control/reference pair |
| OLMDirectionalBlur | base directional render; Noise Type1/2/3 | Exact | **Missing Type3 representative** | Exact, bounded | Dimension-generic production traversal; retained fixtures bind only enumerated parameter families | Real major-mode hole: PF16 Noise Type3 Layer. Close one representative. Fade/tail, broader front/back strengths, size variation, seeds and Layer dimensions are release-note parameter boundaries, not additional major modes. PF8 current Mac AE case0001 already closes the practical host smoke |
| OLMRadialBlur | Zoom / Rotation / Inner | **Missing Inner representative** | Exact, guarded | Exact, guarded | **Fixed-geometry/parameter guarded production routes remain** (principally 9x7, plus retained 1920x1080 lane); do not claim arbitrary geometry | Real production holes: add PF8 Inner and widen literal geometry/parameter guards so Zoom/Rotation/Inner operate at arbitrary valid geometry. Offsets, edge/repeat, size/noise variation, strengths and quality values beyond retained tuples are release-note parameter boundaries and remain fail-closed |
| OLMSmoother2 | v1/v2 classifier; key/invert; gamma None/All/Colors; smoothing/range/extra; palette 1..5 | Prior exact slices | Exact | Exact | Dimension-generic classifier/worker code; evidence includes nonuniform geometry but bounded parameter axes | PF32 case07 current Mac AE raw FLOAT32 is exact and PF8 12/12 is retained AE-exact. Add current installed PF16 practical host representative; no new Windows work unless another host case is selected |
| OLMKiraKira | Mode1 / Mode2 / Mode3 / Mode4; ramp, compose, warp/blur | Typed exact, bounded | Typed exact, bounded | Typed exact, bounded | Mostly dimension-generic, but Mode3/4 production admission is fixture-bounded; do not generalize beyond recorded shapes/lengths | Real production/host hole: close one admitted Mode4 representative if the existing cropped fixture is not a natural full route, then run the natural current Mac AE owner-to-writer representative. The older pinned Mode4 effect output is not a same-contract off/on process-attested calibration; acquire the controlled PF8/PF16/PF32 Windows AE rows |
| OLMSmoother v1 | no-key / Color Key; smoothing range | Exact PF8 bounded full frames | Native PF16 implementation exists but host parity is not release-proven | N/A: original AEX exposes classic PF8/PF16 only; 32bpc projects use AE host conversion | Dimension-generic generated/portable worker, with canonical 960x540 full-frame and retained key fixture evidence | Finish the already-localized PF8 case01 owner boundary if not merged, obtain/verify the single Windows PF16 batch and current Mac PF16 practical render, then current-binary AE load/render. Document 32bpc as host-converted, not native PF32 |

## Authoritative evidence

| Plug-in | Primary current evidence |
|---|---|
| OLMBlur | `olmblur_effectmain_completion_matrix_20260805.json`; `test_olmblur_*source_aex_adapter_20260805.py`; `olmblur_case0001_current_host_result_20260805.json` |
| ColorKeep | `colorkeep_effectmain_completion_matrix_20260805.md`; `colorkeep_pf8_pf16_actual_aex_20260805.json`; `colorkeep_pf16_upstream_chain_current_mac_ae_20260806.md` |
| OLMColorKey | `olmcolorkey_public_completion_matrix_20260805.{md,json}`; `olmcolorkey_edge_blur_complete_family_20260806.json`; `olmcolorkey_mac_ae_host_phase_result_20260805.json` |
| OLMToonDilate | `olmtoondilate_completion_matrix_20260805.md`; `olmtoondilate_installed_completion_route_20260805.{md,json}`; `test_olmtoondilate_installed_dynamic_all_depths_20260806.py` |
| OLMDistanceGradation | `olmdistancegradation_completion_matrix_20260805.md`; `olmdistancegradation_classic_pf16_outside_interp_family_nobg_exact_20260806.md`; `olmdistancegradation_pf32_case0001_current_mac_ae_exact_20260806.json` |
| OLMDirectionalBlur | `olmdirectionalblur_completion_matrix_20260805.json`; `olmdirectionalblur_pf16_front_back_exact_20260806.md`; `olmdirectionalblur_pf8_current_mac_ae_exact_20260806.json` |
| OLMRadialBlur | `olmradialblur_public_completion_matrix_20260805.{md,json}`; `olmradialblur_rotation_pf16_inner_strength_family_production_20260806.json`; `olmradialblur_rotation_pf32_inner_strength_family_production_20260806.json`; `olmradialblur_current_mac_ae_supported_lanes_20260806.md` |
| OLMSmoother2 | `olmsmoother2_completion_matrix_20260805.md`; `olmsmoother2_pf32_current_mac_ae_raw_exact_20260806.md`; `olmsmoother2_native_vs_actual_aex_20260726.md` |
| OLMKiraKira | `olmkirakira_completion_matrix_20260805.json`; `olmkirakira_mode3_gaussian_length9_15x6_crt_dispatch_actual_aex_20260806.json`; Mode2/Mode4 production-boundary regressions in the global suite |
| OLMSmoother v1 | `olmsmoother_v1_effectmain_completion_matrix_20260805.md`; `olmsmoother_v1_pf8_current_mac_ae_exact_20260805.md`; `olmsmoother_v1_32bpc_host_conversion_boundary_20260730.md` |

The Mac-only fixed-fixture release gate is
`python3 scripts/run_olm_mac_fixed_fixture_regression_20260805.py`.  It has ten
named lanes and consumes retained Windows-AEX evidence without contacting a
Windows host.  Its latest full run completed with
`PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=432.31s`.

## One-shot Windows boundary package

The minimum missing Windows observations for this frozen scope are:

- ColorKeep controlled calibration at PF8/PF16/PF32.  Its current Mac PF8
  report explicitly withholds an AE-exact claim, and the retained campaign gap
  matrix records that real Windows AE coverage was absent.
- OLMKiraKira controlled Mode4 calibration at PF8/PF16/PF32.  A hash-pinned
  older Windows effect output exists, but the current runner record is only
  `prepared_loaded_identity_ready_not_rendered`; it does not provide the
  same-contract no-effect/effect-on and process/module attestation required by
  the frozen host boundary.
- OLMSmoother v1 PF16, one representative canonical row.  The current host
  record explicitly says `pf16_host_exact=false`, and the bit-depth audit says
  PF16 becomes exact-eligible only after a returned Windows render passes its
  gates.  Reusing the PF8 host-exact record does not close PF16.

These seven observations belong in one batch.  Do not recapture existing exact
AEX worker fixtures or already-exact Windows AE cases.  OLMSmoother v1 32bpc is
not an additional native-depth row: the original AEX is classic PF8/PF16 and a
32bpc project exercises AE host conversion.

## Release-note evidence boundaries

- Equality is claimed for the named fixtures, AE versions, Software renderer,
  project depth, color settings, input hashes and parameter tuples only.
- Small-fixture equality supports the algorithm path but is not a mathematical
  proof over all dimensions.  OLMRadialBlur is stricter: several production
  paths are themselves guarded to named dimensions/tuples.
- OLMColorKey Edge Blur, OLMDirectionalBlur PF16/PF32, OLMRadialBlur,
  OLMKiraKira Mode3/4, and both Smoother generations retain explicit bounded
  parameter-family claims.
- OLMSmoother v1 has no native PF32 AEX lane.  A 32bpc AE project exercises
  host conversion around the classic integer plug-in and must not be described
  as native PF32 parity.
- AE import, premultiplication, color management and export differences are
  host-boundary evidence, separate from equal plug-in arithmetic on identical
  input worlds.
