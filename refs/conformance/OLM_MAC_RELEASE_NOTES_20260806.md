# OLM Mac bounded release notes — 2026-08-06

## Status and contract

The Mac integration candidate passes all ten fixed-fixture lanes, all ten
installed Universal/signature/identity checks, and one current Mac AE
load/render representative per plug-in. Final same-contract cross-host
calibration remains pending for exactly seven Windows AE rows listed below.

Current-host claims assume After Effects `26.3x87`, CPU `SOFTWARE`, working
space None, linear blending off, and the depth, input interpretation, source
hash, geometry and parameters retained by each evidence record. `Exact` means
byte equality (or raw FLOAT32 word equality) for those records only. It is not
a claim over all images or the Cartesian product of controls.

## Bounded feature surface

| Plug-in | Major modes and native depths in the candidate | Important evidence boundary |
|---|---|---|
| OLMBlur | Legacy/NonLegacy, repeat and bias; PF8/PF16/PF32 | Dimension-generic workers with multiple padded typed fixtures; current PF32 host smoke is load/render evidence, not Windows-exact output |
| ColorKeep | enabled/disabled predicate, tolerance and 1..100 colors; PF8/PF16/PF32 | Exact direct worlds include duplicate/special float inputs. Current PF8 host export and PF16 inter-effect discriminator do not replace the pending same-contract Windows rows |
| OLMColorKey | core, Edge Thin, Edge Blur and replace/color-space surface; PF8/PF16/PF32 bounded | Edge Blur is limited to recorded 4x3 corner/center single-key shapes, directions and amounts |
| OLMToonDilate | copy/dilate, fractional radius, frontier/tie/corner/eligibility; PF8/PF16/PF32 | Evidence covers several padded/partial/empty shapes and radii -1..4; current installed PF32 radius-13 AE representative is a host smoke |
| OLMDistanceGradation | Inside/Outside/Both, RGB/Layer, Constant/Linear/Sphere/Power, invert/background/blur; PF8/PF16/PF32 bounded | Exact axes and selected families are not the full control cross-product; native SmartRender PF32 is not an original-AEX feature |
| OLMDirectionalBlur | base directional and Noise Type1/2/3; PF8/PF16/PF32 bounded | PF16 Type3 Layer is limited to 16x16, angle45/front8/back0, variation100, neutral size/fade/tail and independent padded rows; missing/mismatched Layer or other Type3 tuples fail closed |
| OLMRadialBlur | Zoom/Rotation/Inner; PF8/PF16/PF32 guarded | PF8 centered neutral Inner Strength 1..64 is proven at 9x7, 64x36 and 640x360. PF16/PF32 Inner remain 9x7 guarded. Unlisted offset/ratio/angle/quality/repeat/edge/noise/variation tuples fail closed |
| OLMSmoother2 | v1/v2 classifier, key/invert, Gamma None/All/Colors, range/extra and palettes; PF8/PF16/PF32 bounded | PF32 case07 is raw-artifact exact, but lacks same-run Windows process/module proof and is not called process-attested AE exact |
| OLMKiraKira | Mode1/2/3/4, ramp, compose and warp/blur; PF8/PF16/PF32 bounded | Mode3/4 remain limited to recorded shapes, lengths and tuples. Natural Mode4 and current PF32 Mode4 Mac AE output are exact to the retained artifact |
| OLMSmoother v1 | no-key/Color Key and smoothing range; native PF8/PF16 | PF8 canonical 960x540 and retained key paths are exact. PF16 cross-host host parity awaits one row. The AEX has no native PF32 callback: 32bpc projects are AE host-converted around the classic integer plug-in |

AE import, premultiplication, color management and export differences are a
separate host boundary. A final file difference alone does not establish a
plug-in arithmetic difference when the two hosts did not deliver identical
input worlds.

## Pending Windows AE boundary — exactly seven rows

Run only the hash-bound package
`refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`:

| Plug-in | Case | Depth |
|---|---|---|
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF8 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF16 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF32 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF8 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF16 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF32 |
| OLMSmoother v1 | `case_0001` | PF16 |

Each row requires disabled/effect-on uncompressed scanline FLOAT32 OpenEXR and
the process/module attestation named by `BATCH_CONTRACT.json`. Do not return
PNG previews and do not rerender the seven plug-ins whose evidence is reused.

Package SHA-256:

```text
64f58ef0901d6dc0ba1b67ceb139b63a5ab496cdb9f72868b9fcd6c9dd6db190
```

## Final verification

The checked-in full gate reports:

```text
PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=456.26s
captured-output-sha256 38a02e68c34185fbb5b4216347e161bac1487c45034b217d6638f2e763e5699d
Mac-AE representatives 10 proven / 0 pending / 0 invalid
Universal installed bundles 10 / 10
```

Reproduce and audit the bounded release state:

```sh
python3 tests/test_windows_ae_release_boundary_minimal_20260806.py
python3 tests/test_olm_release_documentation_20260806.py
python3 tests/test_olm_release_gate_20260806.py
python3 scripts/run_olm_release_gate_20260806.py
shasum -a 256 refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip
```

After the Windows archive is returned:

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```

The detailed per-plug-in evidence links and all fail-closed qualifications are
in `olm_release_completion_matrix_20260806.md`; installed binary hashes are in
`olm_release_gate_status_20260806.json`.
