# OLMKiraKira Parameter Surface Contract

- Requested artifact date: `2026-07-17`
- Generated on: `2026-07-17`
- Scope: bounded Windows-manifest-to-Mac-surface validation only.
- AE exact claim: `false`

## Contract

- Identity is `match_name` only for KiraKira request application.
- Index-only request rows are rejected.
- Any request row that includes a missing Windows ramp row fails closed as `unmappable`.
- Existing mapped rows are accepted by match-name even though Windows and Mac visible ordering differs.

## Ordered Surface Drift

| Surface | Slot | Identity | Label |
| --- | ---: | --- | --- |
| Windows | 1 | `OLM OLM Kira Kira-0008` | `Channel` |
| Windows | 2 | `OLM OLM Kira Kira-0009` | `Blur Mode` |
| Windows | 3 | `OLM OLM Kira Kira-0017` | `Merge mode` |
| Windows | 4 | `OLM OLM Kira Kira-0010` | `Approximated Input` |
| Mac | 1 | `OLM OLM Kira Kira-0001` | `Glow Rotation` |
| Mac | 2 | `OLM OLM Kira Kira-0002` | `Brightness Gain` |
| Mac | 3 | `OLM OLM Kira Kira-0003` | `Vertical Length` |
| Mac | 4 | `OLM OLM Kira Kira-0004` | `Horizontal Length` |

## Mapping Summary

| Status | Count |
| --- | ---: |
| `mapped_plugin_surface` | 25 |
| `shared_builtin_passthrough` | 2 |
| `unmappable_custom_ramp_payload_row` | 5 |
| `unmappable_missing_ramp_row` | 5 |
| `unmappable_windows_group_separator` | 5 |

## Validation Examples

- Full Windows case: `unmappable` / `missing_ramp_row_present`
- Mapped rows by match-name: `accepted` / `all_rows_match_name_mapped`
- Index-only rows: `rejected` / `index_only_request_rejected`

## Table

| Win idx | Windows match-name | Windows label | Status | Mac match-name |
| ---: | --- | --- | --- | --- |
| 1 | `OLM OLM Kira Kira-0008` | `Channel` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0008` |
| 2 | `OLM OLM Kira Kira-0009` | `Blur Mode` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0009` |
| 3 | `OLM OLM Kira Kira-0017` | `Merge mode` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0017` |
| 4 | `OLM OLM Kira Kira-0010` | `Approximated Input` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0010` |
| 5 | `OLM OLM Kira Kira-0002` | `Brightness Gain` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0002` |
| 6 | `OLM OLM Kira Kira-0011` | `Strength multiplier` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0011` |
| 7 | `OLM OLM Kira Kira-0027` | `Fade Out` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0027` |
| 8 | `OLM OLM Kira Kira-0007` | `Glow Opacity` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0007` |
| 9 | `OLM OLM Kira Kira-0012` | `Source Opacity` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0012` |
| 10 | `OLM OLM Kira Kira-0003` | `Vertical Length` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0003` |
| 11 | `OLM OLM Kira Kira-0013` | `Vertical Color` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0013` |
| 12 | `OLM OLM Kira Kira-0029` | `Vertical Color Ramp` | `unmappable_missing_ramp_row` |  |
| 13 | `OLM OLM Kira Kira-0018` | `Use Ramp` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0018` |
| 14 | `OLM OLM Kira Kira-0019` | `Ramp` | `unmappable_custom_ramp_payload_row` |  |
| 15 | `OLM OLM Kira Kira-0030` | `(blank)` | `unmappable_windows_group_separator` |  |
| 16 | `OLM OLM Kira Kira-0004` | `Horizontal Length` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0004` |
| 17 | `OLM OLM Kira Kira-0014` | `Horizontal Color` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0014` |
| 18 | `OLM OLM Kira Kira-0031` | `Horizontal Color Ramp` | `unmappable_missing_ramp_row` |  |
| 19 | `OLM OLM Kira Kira-0020` | `Use Ramp` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0020` |
| 20 | `OLM OLM Kira Kira-0021` | `Ramp` | `unmappable_custom_ramp_payload_row` |  |
| 21 | `OLM OLM Kira Kira-0032` | `(blank)` | `unmappable_windows_group_separator` |  |
| 22 | `OLM OLM Kira Kira-0005` | `Diagonal Length` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0005` |
| 23 | `OLM OLM Kira Kira-0015` | `Diagonal Color` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0015` |
| 24 | `OLM OLM Kira Kira-0033` | `Diagonal Color Ramp` | `unmappable_missing_ramp_row` |  |
| 25 | `OLM OLM Kira Kira-0022` | `Use Ramp` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0022` |
| 26 | `OLM OLM Kira Kira-0023` | `Ramp` | `unmappable_custom_ramp_payload_row` |  |
| 27 | `OLM OLM Kira Kira-0034` | `(blank)` | `unmappable_windows_group_separator` |  |
| 28 | `OLM OLM Kira Kira-0026` | `Diagonal 2 length` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0026` |
| 29 | `OLM OLM Kira Kira-0028` | `Diagonal Color2` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0028` |
| 30 | `OLM OLM Kira Kira-0037` | `Diagonal 2 Color Ramp` | `unmappable_missing_ramp_row` |  |
| 31 | `OLM OLM Kira Kira-0035` | `Use Ramp` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0035` |
| 32 | `OLM OLM Kira Kira-0036` | `Ramp` | `unmappable_custom_ramp_payload_row` |  |
| 33 | `OLM OLM Kira Kira-0038` | `(blank)` | `unmappable_windows_group_separator` |  |
| 34 | `OLM OLM Kira Kira-0006` | `Highlight Radius` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0006` |
| 35 | `OLM OLM Kira Kira-0016` | `Highlight Color` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0016` |
| 36 | `OLM OLM Kira Kira-0039` | `Highlight Color Ramp` | `unmappable_missing_ramp_row` |  |
| 37 | `OLM OLM Kira Kira-0024` | `Use Ramp` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0024` |
| 38 | `OLM OLM Kira Kira-0025` | `Ramp` | `unmappable_custom_ramp_payload_row` |  |
| 39 | `OLM OLM Kira Kira-0040` | `(blank)` | `unmappable_windows_group_separator` |  |
| 40 | `OLM OLM Kira Kira-0001` | `Glow Rotation` | `mapped_plugin_surface` | `OLM OLM Kira Kira-0001` |
| 2 | `ADBE Effect Mask Opacity` | `Effect Opacity` | `shared_builtin_passthrough` | `ADBE Effect Mask Opacity` |
| 3 | `ADBE Force CPU GPU` | `GPU Rendering` | `shared_builtin_passthrough` | `ADBE Force CPU GPU` |
