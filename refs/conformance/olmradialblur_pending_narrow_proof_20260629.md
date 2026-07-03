# OLMRadialBlur Pending Narrow Proof

## Decision Boundary

Keep OLMRadialBlur on narrow binary-proof lanes only. Zoom is no longer the first Windows ask; it is a context lane whose sampled/pre-writeback floats already truncate to the exact stored Windows byte. The only active Windows runtime package now is tiny Rotation case_0010, which still needs the anchored pointer/watchpoint witness for typed upstream RGB / substitute-path / neighboring-contribution proof before final inverse sampling.

## Active Request

- Request: `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
- Acceptance note: `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`
- Stop condition: Return enough typed pointer/watchpoint evidence to decide which anchored upstream branch actually promotes the missing bright lobe at `case_0010 (1614,6)`. If the watchpoint path still cannot be held, return the exact failed address/condition plus the dumped `rsi/rbp/rsp` qword windows and pointer context used to reconstruct the sampled-cell address.

## Why Global Tuning Is Still Forbidden

- Zoom already has sampled/pre-writeback floats that truncate to the exact stored Windows byte, so final byte packing is not the live issue there.
- tiny Rotation already rejects final-byte tuning, propagated-validity substitutes, same-row source support, and the current row-coupled surrogates.
- The missing bright lobe remains upstream of final inverse sampling: either neighboring-row/source-population ownership or an AEX substitute/fallback branch.

## Lanes

### zoom_context

- Status: `guarded-context-not-first-windows-ask`
- Case: `case_0009`
- Witness: `{'mac_candidate_rgba': [20, 3, 3, 255], 'reference_rgba': [20, 3, 3, 254], 'signed_delta_candidate_minus_reference': [0, 0, 0, 1], 'x': 6, 'y': 0}`
- Windows pre-writeback RGBA float: `[0.08224078267812729, 0.014130095019936562, 0.014130095019936562, 0.9999999403953552]`
- Windows final RGBA u8: `[20, 3, 3, 254]`
- Required next proof if reopened: Caller-collapse alpha/sample accumulation between preserved validity `+0xf252`, accumulated `+0xf250` RGBA, normalized final polar `+0xe`, and the final stored alpha.

### tiny_rotation_active

- Status: `tiny-rotation-pending-upstream-rgb-or-substitute-proof`
- Case: `case_0010`
- Witness: `{'mac_candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [255, 255, 255, 255], 'signed_delta_candidate_minus_reference': [-255, -255, -255, 0], 'x': 1614, 'y': 6}`
- Windows final RGBA u8: `[255, 255, 255, 255]`
- Closest traced sampler RGBA float: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- Lane audit: `{'same_row_direct_source_cells_all_black': True, 'dominant_local_positive_cluster': [{'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}], 'reference_bright_count': 17, 'all_variants_keep_bright_count_zero': True}`
- Required next proof: Exact source-population / neighboring-row ownership or substitute/fallback branch for case_0010 witness `(1614,6)`, reached from the stable `+0x4eb9/+0x4ec8` anchor and including stack/pointer or watchpoint context plus typed RGBA before and after that branch, preserved validity `+0xf252`, accumulated `+0xf250`, normalized final polar `+0xe`, pre-writeback RGBA float, and final stored RGBA8.

### inner_context

- Status: `parked-typed-per-cell-witness-still-separate`
- Required next proof if reopened: A typed FUN_180001c90 helper-to-output witness that survives beyond effective span into real accumulation / denominator / writeback for one low-span and one quality-strong family.

## Actionable Return Criteria

- The return stays on case_0010 `(1614,6)` and isolates either the substitute/fallback branch or the exact neighboring/source-population chain that creates the missing bright lobe.
- It includes typed values, not only screenshots or a re-confirmed final white byte.
- It maps the decisive value back to a Mac-side ownership boundary before final inverse sampling.

## Not Actionable

- It only repeats the final white byte or the already-known near-black closest inverse-sampler return.
- It only says 'suspected substitute path' without the actual branch/value.
- It suggests global validity-alpha, span/wrap, or final-byte tuning without witness values that survive to writeback.

## Recommended Next Windows Probe

- Send only `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702` while it remains pending.
- If the Windows helper cannot hold the exact watchpoint path, return the exact failed pointer/watchpoint condition plus the closest typed values that still land on the target witness chain.
- Do not reopen Zoom first unless a later Mac code move specifically needs the denominator-side context.
