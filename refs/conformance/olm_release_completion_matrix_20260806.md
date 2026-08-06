# OLM Mac port release completion matrix — 2026-08-06

Release-facing status: the bounded Mac integration gate is green; the final
same-contract Windows AE calibration is still pending for exactly seven rows.
Those are different claims.  A green Mac gate proves the retained actual-AEX
fixtures, installed Universal identities, and current Mac AE representatives;
it does not manufacture the missing Windows process-bound host attestations.

Unless a row says otherwise, the current-host assumption is After Effects
`26.3x87`, CPU `SOFTWARE` rendering, working space None, linear blending off,
and the bit depth, input interpretation, source hash, and parameters named by
its evidence record.

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
| OLMToonDilate | radius copy/dilate; fractional radius; frontier/tie/corner/eligibility | Exact | Exact | Exact | Dimension-generic guarded implementation; evidence spans several shapes, padded/partial and empty worlds, radii -1..4 | Current installed PF32 radius-13 Mac AE load/render is proven. No Windows capture |
| OLMDistanceGradation | Inside / Outside / Both; RGB / Layer; Constant / Linear / Sphere / Power; invert/background/blur | Exact, bounded | Exact, bounded | Exact classic, bounded | Dimension-generic field/compose code; exact axes and selected Cartesian families, not their full cross-product | Current PF32 Mac AE case0001 supplies the practical host smoke. PF32 SmartRender is not an AEX feature and is out of scope; no Windows capture unless the final selected host case lacks its retained control/reference pair |
| OLMDirectionalBlur | base directional render; Noise Type1/2/3 | Exact | Exact, bounded | Exact, bounded | Dimension-generic production traversal; retained fixtures bind only enumerated parameter families | PF16 Type3 Layer is exact only for 16x16, independent padded rows, angle45/front8/back0, variation100 and neutral size/fade/tail. Missing/mismatched Layer and other Type3 tuples fail closed. PF8 current Mac AE case0001 closes the host representative |
| OLMRadialBlur | Zoom / Rotation / Inner | Exact, guarded | Exact, guarded | Exact, guarded | PF8 Inner is geometry-generic only inside its admitted centered neutral tuple, proven at 9x7, 64x36 and 640x360. PF16/PF32 Inner remain 9x7 guarded; do not claim arbitrary geometry for them | No new release hole. Off-center, non-unit ratio, nonzero angle, other quality, repeat-off, offsets, edge fade, noise and variation remain outside the Inner boundary and fail closed |
| OLMSmoother2 | v1/v2 classifier; key/invert; gamma None/All/Colors; smoothing/range/extra; palette 1..5 | Exact, bounded | Exact, bounded | Exact, bounded | Dimension-generic classifier/worker code; evidence includes nonuniform geometry but bounded parameter axes | PF8 retained 12/12 and PF32 current case07 raw FLOAT32 artifacts are exact. The case07 Windows same-run process/module proof is absent, so it is not promoted to process-attested AE exactness; no extra Windows row is required by the frozen seven-row package |
| OLMKiraKira | Mode1 / Mode2 / Mode3 / Mode4; ramp, compose, warp/blur | Typed exact, bounded | Typed exact, bounded | Typed exact, bounded | Mostly dimension-generic, but Mode3/4 admission remains bounded to recorded shapes, lengths and tuples | Natural Mode4 route and current installed PF32 Mode4 case01 Mac AE raw-FLOAT render are exact to the retained artifact. Acquire controlled PF8/PF16/PF32 Windows AE off/on rows for same-contract process-bound calibration |
| OLMSmoother v1 | no-key / Color Key; smoothing range | Exact PF8 bounded full frames | Native PF16 implementation exists; cross-host host parity is pending | N/A native: original AEX exposes classic PF8/PF16 only; 32bpc projects use AE host conversion | Dimension-generic generated/portable worker, with canonical 960x540 full-frame and retained key fixture evidence | PF8 canonical owner boundary and current Mac AE representative are closed. Acquire/verify the one PF16 Windows row. Never describe the 32bpc project result as native PF32 |

## Authoritative evidence

| Plug-in | Primary current evidence |
|---|---|
| OLMBlur | `olmblur_effectmain_completion_matrix_20260805.json`; `test_olmblur_*source_aex_adapter_20260805.py`; `olmblur_case0001_current_host_result_20260805.json` |
| ColorKeep | `colorkeep_effectmain_completion_matrix_20260805.md`; `colorkeep_pf8_pf16_actual_aex_20260805.json`; `colorkeep_pf16_upstream_chain_current_mac_ae_20260806.md` |
| OLMColorKey | `olmcolorkey_public_completion_matrix_20260805.{md,json}`; `olmcolorkey_edge_blur_complete_family_20260806.json`; `olmcolorkey_mac_ae_host_phase_result_20260805.json` |
| OLMToonDilate | `olmtoondilate_completion_matrix_20260805.md`; `olmtoondilate_installed_completion_route_20260805.{md,json}`; `test_olmtoondilate_installed_dynamic_all_depths_20260806.py` |
| OLMDistanceGradation | `olmdistancegradation_completion_matrix_20260805.md`; `olmdistancegradation_classic_pf16_outside_interp_family_nobg_exact_20260806.md`; `olmdistancegradation_pf32_case0001_current_mac_ae_exact_20260806.json` |
| OLMDirectionalBlur | `olmdirectionalblur_completion_matrix_20260805.json`; `olmdirectionalblur_pf16_front_back_exact_20260806.md`; `olmdirectionalblur_pf16_noise_type3_exact_20260806.md`; `olmdirectionalblur_pf8_current_mac_ae_exact_20260806.json` |
| OLMRadialBlur | `olmradialblur_public_completion_matrix_20260805.{md,json}`; `olmradialblur_rotation_pf8_inner_release_boundary_20260806.md`; `olmradialblur_rotation_pf8_inner_practical_geometry_20260806.json`; `olmradialblur_rotation_pf16_inner_strength_family_production_20260806.json`; `olmradialblur_rotation_pf32_inner_strength_family_production_20260806.json`; `olmradialblur_current_mac_ae_supported_lanes_20260806.md` |
| OLMSmoother2 | `olmsmoother2_completion_matrix_20260805.md`; `olmsmoother2_pf32_current_mac_ae_raw_exact_20260806.md`; `olmsmoother2_native_vs_actual_aex_20260726.md` |
| OLMKiraKira | `olmkirakira_completion_matrix_20260805.json`; `olmkirakira_mode3_gaussian_length9_15x6_crt_dispatch_actual_aex_20260806.json`; `olmkirakira_mode4_case01_current_mac_ae_20260806.json`; Mode2/Mode4 production-boundary regressions in the global suite |
| OLMSmoother v1 | `olmsmoother_v1_effectmain_completion_matrix_20260805.md`; `olmsmoother_v1_pf8_current_mac_ae_exact_20260805.md`; `olmsmoother_v1_32bpc_host_conversion_boundary_20260730.md` |

The final bounded integration command is
`python3 scripts/run_olm_release_gate_20260806.py`.  Its checked-in report is
`olm_release_gate_status_20260806.json`: ten Mac AE representatives, ten
Universal signed installed identities, and ten fixed-fixture lanes are proven.
The fixed-fixture sub-gate consumes retained Windows-AEX evidence without
contacting Windows; the current checked-in summary is
`PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=423.84s` with captured
output SHA-256
`bf5970bbcaf47fed933b8602841ec20ce2e0db1a3f2be7d411fefa8b363e19fd`.
The same checked-in gate also requires all ten parameter-UI registration rows:
seven are normalized exact and three are explicitly bounded rather than
silently promoted to native-AE visual or custom-UI exactness.

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

The exact pending rows are:

| Plug-in | Case | Depths |
|---|---|---|
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF8, PF16, PF32 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF8, PF16, PF32 |
| OLMSmoother v1 | `case_0001` | PF16 |

Use `refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`
only. Verify its release hash from `OLM_MAC_RELEASE_NOTES_20260806.md` before
execution (the matrix itself is embedded in the package, so it intentionally
does not self-pin the archive hash).
The return must contain process/module attestation plus disabled and enabled
uncompressed scanline FLOAT32 OpenEXR for every row; PNG previews do not close
the boundary.

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

## Final verification

```sh
python3 tests/test_windows_ae_release_boundary_minimal_20260806.py
python3 scripts/package_windows_ae_release_boundary_minimal_20260806.py
shasum -a 256 refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip
python3 tests/test_olm_release_gate_20260806.py
python3 scripts/run_olm_release_gate_20260806.py
```

After the Windows return arrives, verify it with the packaged verifier (or the
repository copy) before changing any host-exact claim:

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```
