# OLMSmoother2 AEXCompat Host-I/O Exact Evidence (2026-07-25)

## Scope

This is an AEXCompat intermediate proof, not a Mac AE `AE exact` result.

The unchanged Windows `OLMSmoother2.aex` was executed on macOS through
AEXCompat. All 12 current-AEX legacy 8bpc cases matched the Windows AE
Software PNG references after reproducing the proven AE host boundary.

## Host-I/O Contract

- AEX input: original straight-RGBA source PNG selected by
  `case.input_id` and `manifest.source_inputs`.
- Source SHA-256:
  `9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265`.
- The source was accepted only because applying the export transform to it
  reproduced every case's `before_effects_frame` exactly.
- AEX raw output was preserved separately.
- Comparison output RGB used `(raw_rgb * raw_alpha + 127) // 255`; alpha was
  preserved.
- No 8bpc `before_effects_frame` was unpremultiplied or treated as a
  reversible source.

The round-to-nearest rule is independently pinned by the Windows writer
witness `[200, 200, 200, 135]` and exported pixel
`[106, 106, 106, 135]`. Floor, ceil, and `+128` alternatives leave
measurable residuals.

## Result

| Case | max_diff | nonzero_pixels |
| --- | ---: | ---: |
| legacy_case_0001_current_aex | 0 | 0 |
| legacy_case_0002_current_aex | 0 | 0 |
| legacy_case_0003_current_aex | 0 | 0 |
| legacy_case_0004_current_aex | 0 | 0 |
| legacy_case_0005_current_aex | 0 | 0 |
| legacy_case_0006_current_aex | 0 | 0 |
| legacy_case_0007_current_aex | 0 | 0 |
| legacy_case_0008_current_aex | 0 | 0 |
| legacy_case_0009_v1mode_current_aex | 0 | 0 |
| legacy_case_0010_gamma3_current_aex | 0 | 0 |
| legacy_case_0011_gamma5_blue_current_aex | 0 | 0 |
| legacy_case_0012_gamma5_red_blue_current_aex | 0 | 0 |

Summary: `pixel_exact=12/12`, `render_success=12/12`, `errors=0`.

## Binary Identity

- Windows AEX SHA-256:
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- AEXCompat worker SHA-256:
  `2e8c58081c7db6ef7ac847b955e239f48c3469bc573b5501ac0d280b4b997fe7`
- Full local result SHA-256:
  `2ac06815fa12f587c8295eeef8e80af60fb9b5b6200cbd7760afb11d417318ce`

## Command

```sh
python3 scripts/run_aexcompat_reference.py \
  --request refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2 \
  --aex plugins_2025/OLMSmoother2.aex \
  --worker <AEXCOMPAT_WORKTREE>/guest/target/release/aex-guest-worker \
  --output-dir /tmp/olmsmoother2_aexcompat_hostio_fixed_20260725_b \
  --timeout 1200
```

## Consequence

The previously reported direct/raw residual
`max_diff=255, nonzero_pixels=18,326` for case 0008 was a comparison-harness
host-I/O error. It is superseded by this evidence and must not be used as an
algorithm residual.

The Windows algorithm and its AEXCompat execution are now a byte-exact local
oracle for these 12 cases. The next lane is to compare the Mac native
implementation against that oracle, followed by Mac AE host validation.
