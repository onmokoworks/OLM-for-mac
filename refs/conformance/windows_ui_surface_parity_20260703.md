# Windows UI Surface Parity Audit - 2026-07-03

This note summarizes the new Windows Effect Controls surface capture return:

- Windows manifest:
  `refs/win_references/olm_reference_return_windows_20260703_combined/OLMmulti-effectUIsurfacecapture/reference_manifest.json`
- Mac source-backed schema:
  `refs/reports/mac_plugin_param_schema_20260629.json`
- Machine audits:
  `refs/reports/windows_ui_surface_defaults_audit_20260703.md`
  `refs/reports/windows_ui_surface_ranges_audit_20260703.md`
  `refs/reports/windows_ui_surface_param_parity_summary_20260703.md`

The purpose here is not algorithm correctness. This is only the visible AE panel
surface: labels, grouped rows, cold-start defaults, and AE-exposed range
metadata.

## Decision

Current ranking for visible Win/Mac UI-surface mismatch risk:

1. `OLMKiraKira`
2. `OLMColorKey`
3. `OLMRadialBlur`
4. `OLMSmoother2`
5. `OLMSmoother` v1

- `OLMKiraKira` no longer has a hard fresh-surface range blocker after the
  2026-07-03 label/range cleanup; what remains is mostly ordering/ramp metadata.
- `OLMColorKey` moved from broad visible mismatch into mostly-fixed territory.
- `OLMKiraKira` is mostly source/range metadata drift, not immediate evidence
  that the visible panel is unusable.
- `OLMRadialBlur` is now mostly beyond host-fix; remaining blockers are narrow
  binary-proof lanes, not a broad missing-controls problem.

## High-signal findings

### OLMColorKey

- Defaults audit status: `mostly-fixed`
- Ranges audit status: `mostly-fixed`
- The Mac source now mirrors the Windows `Threshold Parameters`, `Edge Thin`,
  and `Edge Blur` topic layout, uses visible child `Amount` labels, matches the
  Windows `Use Color / Use Replace Color / Color / Replace Color / Threshold*`
  block order, and exposes the Windows-scale `Amount` ranges.
- Remaining differences are narrow:
  source-backed symbolic defaults for `Use Color N`, the missing explicit group-end
  placeholder rows, and the fact that `Threshold Parameters` appears only as a
  source-side topic row rather than a full Windows start/end pair in the audit model.
- Evidence:
  - `refs/reports/windows_ui_surface_defaults_audit_20260703.md`
  - `refs/reports/windows_ui_surface_ranges_audit_20260703.json`

### OLMKiraKira

- Defaults audit status: `fixed`
- Ranges audit status: `mostly-fixed`
- The 2026-07-03 host/UI cleanup aligned `Brightness Gain` to the Windows
  visible `1..100` range, aligned `Highlight Radius` to Windows `0..500`, and
  renamed the visible labels to the Windows spellings `Merge mode`,
  `Strength multiplier`, `Diagonal 2 length`, and `Diagonal Color2`.
- Windows also presents the visible order very differently: `Channel`,
  `Blur Mode`, `Merge mode`, `Approximated Input` appear near the top, while
  the current Mac schema begins with `Glow Rotation` / `Brightness Gain` and
  then length controls.
- The many ramp/color entries flagged in the ranges audit are mostly `source-no-range`
  because they are color/toggle/no-value UI surface rows, not because the
  whole panel is missing.
- So this is a real host-schema follow-up lane, but not evidence to reopen the
  already parked hotspot compose lane.
- Evidence:
  - `refs/reports/windows_ui_surface_param_parity_summary_20260703.md`
  - `refs/reports/windows_ui_surface_ranges_audit_20260703.json`

### OLMRadialBlur

- Defaults audit status: `mostly-fixed`
- Ranges audit status: `mostly-fixed`
- The remaining mismatches are mostly expected grouped/no-value rows and fields
  where Windows does not report a scalar range in the UI surface manifest
  (`Center`, group headers, `Angle`, `Noise Layer`, trailing `Offset`).
- The visible grouped structure itself is close now. The most obvious remaining
  label drift is that Windows shows plain `Strength` under `Inner Blur`, while
  the current Mac schema still names that row `Inner Strength`.
- This supports the earlier conclusion that RadialBlur is no longer primarily a
  host-fix problem.
- Evidence:
  - `refs/reports/windows_ui_surface_defaults_audit_20260703.md`
  - `refs/reports/windows_ui_surface_ranges_audit_20260703.json`

### OLMSmoother2 and OLMSmoother v1

- These are not top-three blockers, but both still have visible naming drift.
- `OLMSmoother2`: Windows repeats five visible `Gamma Color` labels, while the
  current Mac schema names them `Gamma Color`, `Gamma Color 2`, `Gamma Color 3`,
  `Gamma Color 4`, `Gamma Color 5`.
- `OLMSmoother` v1: Windows still shows `Do Smooth Range`, while the current
  Mac schema label is `Smooth Length Tolerance`.

## Operational takeaway

When we spend Mac AE time by hand:

1. `OLMColorKey` host/UI parity checks are still worth doing.
2. `OLMKiraKira` should get targeted schema/range cleanup only; do not treat
   the UI-surface audit as a reason to retune the image pipeline.
3. `OLMRadialBlur` should stay on witness-led binary proof, not panel polishing.
