# OLMRadialBlur tiny Rotation Lane Audit

- Case: `case_0010`
- Witness: `(1614, 6)`
- Current candidate RGBA: `[0, 0, 0, 255]`
- Windows reference RGBA: `[255, 255, 255, 255]`
- Decision: `tiny-rotation-pending-upstream-rgb-or-substitute-proof`
- Reason: The current Mac branch already rejects final-byte tuning and validity-only explanations. At the max witness `(1614,6)`, all four direct same-row source cells are black, the surviving cell_rgb values are small or negative, the dominant local positive source-polar family sits one row above at row 843 / angles 1601..1602, and the tested row-coupled surrogates still leave the reference bright-lobe count at 17 versus 0 locally. So the remaining lane stays upstream in neighboring-row contribution ownership or an AEX substitute/fallback branch before final inverse sampling.
- Forbidden action: Do not promote global validity-alpha policy, final byte conversion, broad row-coupling tweaks, or a plain same-row support rewrite from the current local evidence alone.
- Next Windows requirement: Use the stable `+0x4eb9/+0x4ec8` anchor only as the entry point; the required witness is now the first retained promotion branch with stack/pointer or watchpoint context around the sampled cell and neighboring rows.

## Same-Row Boundary

- row_length: `3`
- row_weights: `[1.0, 0.6065306823076752, 0.13533530340315494]`
- direct same-row source cells all black: `True`

| Cell | cell_rgb | src_cell_rgba |
| --- | --- | --- |
| `x0y0` | `[-0.0147110438, -0.0147110438, -0.0147110438]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x1y0` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x0y1` | `[-0.0485489555, -0.0485489555, -0.0485489555]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x1y1` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |

## Source-Polar Boundary

- witness sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- witness sample U8: `[0, 0, 0, 255]`
- dominant local positive cluster: `[{'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}]`
- strongest negative source-polar cells: `[{'xy': [1601, 845], 'rgba': [-0.624861, -0.624861, -0.624861, 1], 'luma': -0.624861}, {'xy': [1601, 844], 'rgba': [-0.189342, -0.189342, -0.189342, 1], 'luma': -0.189342}]`

## Row-Coupling Rejection

- reference bright count in 25x25 window: `17`
- all tested variants keep local bright count at zero: `True`

| Variant | mean_diff | bright_count | witness_rgba |
| --- | ---: | ---: | --- |
| `baseline` | `0.010320337` | `0` | `[0, 0, 0, 255]` |
| `prev2-k2-positive scale=0.0025` | `0.010719039` | `0` | `[0, 0, 0, 255]` |
| `prev2-row-tail-positive scale=0.005` | `0.012562572` | `0` | `[0, 0, 0, 255]` |

## Propagated-Validity Rejection

- The propagated-validity probe leaves tiny Rotation effectively unchanged (`max=255 mean=0.0103`). This supports the existing conclusion that the remaining blocker is RGB/substitute-path population, not a simple validity-plane collapse.

## Pending Windows Follow-up

- Request: `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
- Acceptance: `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`
- Stop condition: Return enough typed pointer/watchpoint evidence to decide which anchored upstream branch actually promotes the missing bright lobe at `case_0010 (1614,6)`. If the watchpoint path still cannot be held, return the exact failed address/condition plus the dumped `rsi/rbp/rsp` qword windows and pointer context used to reconstruct the sampled-cell address.

## Reading

- The witness is no longer well described as an alpha problem or a final-sample byte problem.
- A plain same-row support model cannot generate the missing white lobe from the four direct source cells now visible in the local dump.
- The surviving local clue is the positive source-polar family one row above the witness rows, but the current row-coupled surrogates are still too weak to promote into the port.
- The next acceptable move still requires the pending Windows typed upstream RGB/substitute-path witness.

