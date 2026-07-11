# 32bpc Existing-48 AE2025 Intake - 2026-07-10

Source: `20260710_185500__RETURN__olm_32bpc_existing48_exr_20260710__answered_partial_portable.zip`.

## Accepted Windows Reference Facts

- AE version: `25.2x131`.
- Project: `32bpc`, renderer `SOFTWARE`.
- Declared request: `olm_bitdepth_32bpc_full_probe_exr_rerun_20260703`, all
  48 requested cases returned.
- All 96 EXR files (48 output plus 48 before-effects) are 1920x1080, physical
  channel order `A/B/G/R`, FLOAT sample type `2`, and compression `0`.
- All 48 output hashes and EXR scanlines pass
  `scripts/verify_32bpc_float_return.py` after import.

This accepts the Windows reference artifacts. It does not make any Mac plugin
`AE exact`.

## First Mac Comparison

The already-rendered Mac AE FLOAT candidates were compared by semantic RGBA
float bits for ColorKey cases `0001..0009` and ToonDilate `0001..0003`.

- ColorKey: `0/9` exact; parameter manifests match apart from normal float
  representation differences.
- ToonDilate: `0001` and `0002` have a 960x540 Mac candidate versus a
  1920x1080 Windows reference, so they are invalid comparisons; `0003` is not
  exact.

The next Mac action is to materialize candidates with the exact 1920x1080
32bpc request geometry, then classify the remaining float mismatches. Do not
tune from the prior PNG-only 32bpc probes.
