# OLMRadialBlur tiny Rotation Lane State - 2026-07-03

- Case: `case_0010`
- Witness: `(1614,6)`
- Status: `reference-path-split-suspected`
- Candidate / Windows: `[0, 0, 0, 255]` vs `[255, 255, 255, 255]`
- Safe claim: tiny Rotation `case_0010` witness `(1614,6)` must not be tuned from the 20260604 PNG alone. Local CPU AEX emulation now reproduces the Windows typed `+0xe` neighboring cells to <=1 ULP and the AEX direct inverse sample at `(1614,6)` returns black, while the legacy PNG reference remains white.

## 2026-07-05 Local AEX Emulation Gate

- Harness: `tools/emulation/test_m4_case0010.py`
- AEX path: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- Chain executed: `FUN_180008690 -> FUN_180007520 -> FUN_180004640`
- Windows typed-cell comparison on `+0xe`:
  - exact: `2/4`
  - RGB within `<=1 ULP` with alpha exact: `4/4`
- Direct AEX inverse coordinate for `(1614,6)`:
  - radius: `844.317504883`
  - angle: `5.598455906`
  - sample coordinate: `(1603.839558785, 844.317504883)`
  - direct `FUN_180001000(+0xe)` sample: `[-0.004081939, -0.004081939, -0.004081939, 1.0]`
  - u8 after clamp/round: `[0,0,0,255]`
- Legacy PNG reference at the same witness remains `[255,255,255,255]`.
- Consequence: this witness is now a reference-provenance / render-path split candidate, not a safe local scatter-tuning target.

## Same-row boundary

- row_length: `3`
- row_weights: `[1.0, 0.6065306823076752, 0.13533530340315494]`
- direct source cells all black: `True`

## Source-polar boundary

- witness sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- witness sample U8: `[0, 0, 0, 255]`
- dominant local positive cluster: `[{'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}]`
- strongest positive: `[{'xy': [1608, 838], 'rgba': [0.452643, 0.452643, 0.452643, 1], 'luma': 0.45264299999999996}, {'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}, {'xy': [1608, 839], 'rgba': [0.0355792, 0.0355792, 0.0355792, 1], 'luma': 0.0355792}]`
- strongest negative: `[{'xy': [1601, 845], 'rgba': [-0.624861, -0.624861, -0.624861, 1], 'luma': -0.624861}, {'xy': [1601, 844], 'rgba': [-0.189342, -0.189342, -0.189342, 1], 'luma': -0.189342}]`

## Row-coupling boundary

- reference bright count in local window: `17`
- all tested local variants keep bright count zero: `True`

## Superseded Windows Follow-up

- Request: `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
- Status: `superseded-by-local-aex-emulation`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
- Acceptance: `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`
- Supersession reason: local CPU AEX emulation already matches the retained Windows typed `+0xe` cells and direct-samples the witness as black, so the old "find the branch that promotes black to white" request bakes in an unsafe assumption.
- Replacement proof: current-AEX Software/EXR recapture or CPU final writeback witness for `(1614,6)`.

Latest Windows return status:

- `partial_with_direct_postreturn_registers`
- stable anchor re-confirmed at `OLMRadialBlur+0x4eb9/+0x4ec8`
- final Windows RGBA still `[255,255,255,255]`
- source/polar sample still near-black `[-0.0040819393, -0.0040819393, -0.0040819393, 1.0]`
- retained anchor-context now additionally includes:
  - sampled-cell offsets such as `row844_col1603 = 0x1734a30`
  - typed neighboring values:
    - `row844 col1603 = bc70f44b bc70f44b bc70f44b 3f800000`
    - `row845 col1603 = bd46d045 bd46d045 bd46d045 3f800000`
    - `row843 col1601 = 3dd69702 3dd69702 3dd69702 3f800000`
    - `row843 col1602 = 3de119ce 3de119ce 3de119ce 3f800000`
  - witness-offset values:
    - `f250 = 00000000 3f800000 00000000 00000000`
    - `f252 = 00000000`
  - a retained read watchpoint hit at `OLMRadialBlur+0x111f`
  - caller stack path `+0x111f -> +0x4ec8 -> +0x7b4a -> +0x41f8 -> entry_point+0x458`
- newly retained direct post-return register snapshots:
  - `+0x7b4a`: `r9=1`, `r10=2`, `r14=0x780`, `r12=0x438`
  - `+0x41f8`: `r9=1`, `r10=2`, `r14=8`, `r15=0`
- post-capture fault happened later at `OLMRadialBlur+0xff02`, after the useful register snapshots were already written
- missing facts remain:
  - CPU final output writeback witness proving the white byte inside this same AEX path
  - or a recaptured Software/EXR reference proving the PNG white is not an older/GPU/manifest-mixed artifact

## Decision Ladder

1. If a current-AEX Software/EXR recapture or CPU writeback trace confirms black at `(1614,6)` -> mark the legacy PNG witness invalid for this lane and stop chasing the white pixel.
2. If a current-AEX CPU writeback trace proves white while direct `+0xe` sample remains black -> find the alternate final-output branch before touching Mac scatter.
3. If a current-AEX CPU trace shows upstream polar values differ from local emulation -> reopen `FUN_180002780 / FUN_1800024c0` scatter ownership with the mismatching typed cells.

## Forbidden

- Do not promote a global validity-alpha rewrite from this lane.
- Do not promote a same-row-only support tweak from the row-843 cluster evidence alone.
- Do not retune final byte conversion or scatter solely to match the legacy PNG white while CPU AEX direct sampling returns black.

## Inputs

- lane_audit_json: `refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json`
- source_candidates_json: `refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.json`
