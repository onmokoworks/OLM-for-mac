# OLMRadialBlur tiny Rotation Source-Candidates Audit

- Case: `case_0010`
- Witness: `(1614, 6)`
- Source: `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- Lane decision: `tiny-rotation-pending-upstream-rgb-or-substitute-proof`
- Current candidate RGBA: `[0, 0, 0, 255]`
- Windows reference RGBA: `[255, 255, 255, 255]`

## Lane Facts

- direct source cells all black: `True`
- witness directly sees row-843 cluster in current branch: `False`
- reference bright count in local 25x25 window: `17`
- tested local variants keep bright count zero: `True`

## Source Candidates

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `rotation_polar_population_and_validity_capture` | `RenderRotation8` | `934` | The active witness is already black before final inverse sampling, and the local audits show the surviving bright family lives upstream in source-polar / preserved-validity ownership. | typed source-polar population or preserved-validity capture only |
| 2 | `rotation_scatter_and_neighboring_row_ownership` | `scatter_row_small / RenderRotation8` | `952` | The row-843 cluster is locally real, but the witness cannot directly see it in the current branch, so neighboring-row ownership or a substitute/fallback promotion before inverse sampling remains live. | upstream scatter/substitute-path ownership only; no broad same-row tweak |
| 3 | `rotation_final_inverse_sample_and_u8_writeback` | `RenderRotation8` | `1074` | This is second-order only. Reopen it only if a Windows typed witness proves upstream population already matches and the decisive split still appears at final sampling. | only with explicit Windows contradiction to the current upstream reading |

## Decision Ladder

1. If Windows typed witness shows the decisive bright contribution is missing before scatter/normalization -> Constrain changes to polar population / preserved-validity capture in RenderRotation8
2. If Windows proves the bright family exists upstream but is lost in ownership, substitute, or neighboring-row promotion -> Constrain changes to scatter/substitute-path ownership before final inverse sampling
3. If Windows shows upstream population already matches but the split still appears at final sampling -> Only then reopen final inverse-sample / writeback logic

## Forbidden Actions

- Do not promote a global validity-alpha rewrite from this lane.
- Do not promote a same-row-only support tweak from the row-843 cluster evidence alone.
- Do not retune final byte conversion while the witness remains black before the proven upstream boundary.

## Pending Windows Follow-up

- Request: `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
- Acceptance: `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`
- Requirement: Use the stable `+0x4eb9/+0x4ec8` anchor only as the entry point; the required witness is now the first retained promotion branch with stack/pointer or watchpoint context around the sampled cell and neighboring rows.

