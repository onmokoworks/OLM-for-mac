# OLMRadialBlur Tiny Rotation Intake Audit - 2026-07-03

Status: `reference-path-split-suspected-after-local-aex-emulation`

This is a no-edit audit of the active `tiny Rotation` Windows return boundary.

Checked against:

- [anchor-context follow-up contract](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_followup_contract_20260702.md)
- [anchor-context return acceptance](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md)
- [scripts/compare_radialblur_trace.py](/Users/onmk/Documents/Projects/Personal/OLM%20as/scripts/compare_radialblur_trace.py)
- [latest backstep comparison](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.md)

## 2026-07-05 Update

The previous intake path was aligned for the Windows CDB follow-up contract,
but local AEX emulation has now changed the decision boundary:

- `tools/emulation/test_m4_case0010.py` runs the Windows CPU `.aex` locally
  through `FUN_180008690 -> FUN_180007520 -> FUN_180004640`.
- The normalized polar `+0xe` typed cells from the local run match the retained
  Windows typed cells to `<=1 ULP` RGB with exact alpha.
- Calling the AEX inverse coordinate transform and AEX bilinear sampler
  directly for `(1614,6)` samples `+0xe` at
  `(1603.839558785, 844.317504883)` and returns near-black
  `[-0.004081939, -0.004081939, -0.004081939, 1.0]`.
- The legacy 20260604 PNG reference remains white at that witness.

Therefore the active intake state is no longer "wait for upstream promotion
branch" as the only path. The lane must first distinguish:

- legacy PNG / render-path / AEX-version provenance split, versus
- an alternate final-output CPU branch not represented by the direct
  `+0xe -> FUN_180001000` path.

Do not use this witness to justify Mac-side scatter tuning until that split is
resolved.

## Prior Result

The current intake path had been aligned:

- the contract asks for the first retained upstream promotion branch from the
  stable `+0x4eb9/+0x4ec8` anchor
- the return acceptance explicitly rejects anchor-only confirmation as
  `answered`
- `scripts/compare_radialblur_trace.py` now promotes the newest focused return to
  `tiny_rotation:direct-postreturn-captured-upstream-branch-still-missing`
  once `+0x7b4a/+0x41f8` are retained but the decisive promotion branch is still
  missing
- the latest imported Windows result is still correctly read as
  not-yet-final binary proof, even though it is materially stronger than the
  earlier anchor-only retries

Latest return now concretely says:

- stable inverse-sampler anchor is still present
- final Windows RGBA is still `[255,255,255,255]`
- sampled inverse-sampler return is still near-black
- and the retained artifact now does include:
  - anchor-context pointer windows and sampled-cell reconstruction notes in the retained CDB log
  - concrete sampled-cell offsets for row844/845 and the positive row843 neighbors
  - typed row844/845 negative cells and row843 positive cells
  - witness-offset `f250` / `f252` values
  - a retained read watchpoint hit at `OLMRadialBlur+0x111f`
  - caller stack path through `+0x4ec8 -> +0x7b4a -> +0x41f8`
  - direct post-return register dumps at `+0x7b4a` and `+0x41f8`
- but the decisive promotion branch still does not include:
  - `+0x7404` direct post-return / normalized-final bridge
  - the first retained upstream promotion branch from near-black to white
  - typed normalized final `+0xe` promotion values at that branch

## Durable intake rule

The next Windows return for:

- `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`

should be promoted to `answered` only if it includes:

- stable anchor preservation
- concrete sampled-cell / adjacent-row address reconstruction
- the first retained upstream promotion branch
- typed values for substitute/source-population ownership or equivalent
  `+0xf252`, `+0xf250`, `+0xe` path evidence

It should remain `failed_partial` if it only reconfirms:

- the same near-black inverse-sampler sample
- the same final white byte
- the same anchor without the decisive upstream branch/value
- or only repeats the retained anchor facts without the missing pointer windows /
  sampled-cell reconstruction

For the current `2026-07-05` direct-postreturn retry, treat the state as
`partial_with_direct_postreturn_registers`: the retained artifact now includes
direct post-return register snapshots at `+0x7b4a` and `+0x41f8`, but it still
does not cross the stop line into the first decisive promotion branch or the
normalized-final `+0xe` bridge.

## Practical consequence

No additional local RadialBlur source tuning is justified from the current
Windows lane alone. After the local AEX emulation gate, the specific
`case_0010 (1614,6)` white pixel should be treated as a reference-provenance
question unless a same-AEX CPU writeback witness proves otherwise.

The next meaningful proof is either a current-AEX Software/EXR recapture for
this exact case or a CPU writeback trace that captures the actual final output
store at `(1614,6)` from the same `.aex`.

Latest return archive:

- `/Volumes/onmk/olm_pr/old/20260703_202500__olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702_return_windows.zip`
- `/Volumes/onmk/olm_pr/old/20260704_0028__olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260704_return_windows.zip`
- `/Volumes/onmk/olm_pr/old/20260705_124819__olm_runtime_trace_radialblur_tiny_rotation_direct_postreturn_20260705_return_windows.zip`
