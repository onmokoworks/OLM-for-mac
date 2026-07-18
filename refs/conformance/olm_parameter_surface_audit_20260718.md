# OLM parameter surface audit (2026-07-18)

Scope: Mac source/PiPL plus the Windows AE cold-start defaults/ranges manifests.
`OLMSmoother2` and `OLMRadialBlur` are intentionally excluded from source edits
for this audit.

## Evidence

- Windows defaults: `refs/win_references/olm_fresh_instance_defaults_20260629/OLMmulti-effectdefaultcapture/reference_manifest.json`
- Windows ranges: `refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json`
- Previous parity summary: `refs/conformance/windows_fresh_param_parity_20260703.md`
- Mac parameter definitions: each plug-in's `ParamsSetup` and header enum
- PiPL/code version check: `AE_Effect_Version` equals the corresponding
  `MAJOR_VERSION/MINOR_VERSION/BUG_VERSION/STAGE_VERSION/BUILD_VERSION` for
  every checked plug-in, including the excluded plug-ins.

## Implemented corrections

### OLMColorKey

The fresh-instance manifests place the topic row at property index 3, while
its leaf rows appear after the premultiply/color-space/precision controls. The
Mac source's leaf registration order and render enum remain coupled; the topic
wrapper is not treated as a linear `params[]` slot. An attempted topic/enum
move was rejected by this independent audit and is not part of the accepted
source state. Disk IDs and indexed color formulas remain unchanged.

### OLMKiraKira

Windows mapped scalar order begins `Channel`, `Blur Mode`, `Merge mode`,
`Approximated Input`, `Brightness Gain`, `Strength multiplier`, `Fade Out`,
`Glow Opacity`, `Source Opacity`, then the vertical/horizontal/diagonal groups,
`Highlight Radius`, and ends with `Glow Rotation`. The Mac source previously
started with `Glow Rotation` and placed the channel/merge controls later.
The header enum and `ParamsSetup` registration order now follow the Windows
scalar order. Disk IDs are unchanged.

The Windows property tree also contains additional NO_VALUE ramp/group entries
between color controls. They were not invented on Mac because this repository
has no source-backed registration contract for those entries. They remain an
explicit follow-up rather than being silently treated as matched.

## Reviewed without source edits

- `OLMBlur`: defaults and exposed ranges match the Windows manifest.
- `OLMDistanceGradation`: defaults and exposed ranges match the Windows
  manifest. Its existing 16bpc algorithm residuals are outside this UI audit.
- `OLMToonDilate`: defaults and exposed ranges match the Windows manifest.
- `OLMDirectionalBlur`: defaults match. Windows does not expose bounds for
  `Angle`, `Noise Layer`, or `Offset`; the Mac source currently supplies bounds
  for some of these. Removing bounds requires a source/API contract beyond the
  manifest, so it is recorded as unresolved rather than guessed.
- `OLMSmoother2` and `OLMRadialBlur`: reviewed only for version consistency;
  no source changes by policy.
- `ColorKeep`: PiPL/code version consistent; support-only and outside the main
  release population.

## Version result

No PiPL/code version mismatch was found. All checked PiPL values are consistent
with the matching header version macros. `ADBE Force CPU GPU` remains metadata
only and is not used as an execution-path claim.

## Limits

This is a parameter-surface correction, not an AE exact output claim. The
Windows manifests are from AE 26.2x49. A fresh Mac AE instance should be used
to verify the resulting property order after rebuilding each changed plug-in.

The regression test is
`refs/scripts/smoke_validate_olm_parameter_order_20260718.py`. It checks the
default/range manifest order, leaf match-name order, Mac enum values, disk ID
constants, ParamsSetup registration order, and `params[]` render references.
It also records the current KiraKira registered-but-unconsumed parameters:
`Approximated Input`, `Fade Out`, and `Highlight Radius`.
