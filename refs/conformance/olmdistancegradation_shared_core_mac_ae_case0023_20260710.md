# OLMDistanceGradation Shared-Core Mac AE Validation - 2026-07-10

## Verdict

`olmdistancegradation_extended__case_0023` is `AE exact` at 16bpc for both
declared background variants after the Mac plug-in was rebuilt to use the
shared portable distance stage.

| Variant | max_diff | nonzero_px | nonzero_values |
| --- | ---: | ---: | ---: |
| Use Background Color = 1 | `0` | `0` | `0` |
| Use Background Color = 0 | `0` | `0` | `0` |

This is an exact result for the stated case/variant slice. It is not a claim
that all OLMDistanceGradation 16bpc features are complete.

## Host facts

- Mac AE: `26.3x87`
- project depth: `16bpc`
- working space: `None`
- linear blending: `false`
- effect: `OLM Distance Gradation`
- Mac source path: `dt_to_normalized` delegates to
  `core/olmdistancegradation_fieldgen.cpp`
- built binary before signing SHA-256:
  `e904ff6423aa8660893595e54a0ddcb565bed1d593861477112ea73032824401`
- installed ad-hoc-signed binary SHA-256:
  `637c9b295809b2a71c52d6660f4818eb11afac45ca194760ed52de723eb87f44`

The prior installed plug-in was moved outside MediaCore before installation,
so AE loaded one Distance Gradation plug-in copy.

## Parameters

- Invert: `0`
- In/Out: `3` (Both)
- Inside Threshold: `36`
- Outside Threshold: `0`
- Render Mode: `1` (RGB)
- Gradation Color: `[0.1098041459918, 0, 0.93333333730698, 1]`
- BG Color: `[1, 0, 0, 1]`
- Interpolation Mode: `1`
- Power: `1`
- Blur Mode: `1`
- Blur Size: `0`

## Candidate hashes

- bg_on PNG:
  `4ffcbd0015557e076067969ce364625e9aad12ffb8c96756a97d7dc6d8ad4910`
- bg_off PNG:
  `933ea782e5781556b95cfb739abcfb8f0dfa021ff63d99a784ca2497262dbf64`

## Reproduction

The request was materialized with
`scripts/prepare_distancegradation_case0023_probe.py`, then both variants were
rendered through the live AE instance using `scripts/run_ae_single_case.py`.
Comparison used `refs/scripts/verify_manifest.py` image loading and exact
integer RGBA subtraction. Temporary host artifacts were written below
`/tmp/olm_dg_shared_core_case0023`; the canonical Windows references remain in
`refs/win_references/`.

## Remaining boundary

Keep OLMDistanceGradation at release-scope incomplete. Other 16bpc feature
families, 8bpc declared coverage, and 32bpc float-preserving host comparison
remain separate gates.
