# DirectionalBlur source/staging witness 20260710

- Status: `ok`
- Case: `case_0001`, row `169`
- No Mac source or PNG edits.

## FACT

- source (959,169) is [0,0,0,255] in the Windows before-effects input.
- the real AEX rowdriver capture reaches source_x=959 on row 169 and observes source RGB zero after return.
- with zero-initialized staging, the observed B RGB at (494,169) and (579,169) is zero immediately after scatter and at rowdriver writeback input.
- Windows final reference is red=164 at (494,169) and red=25 at (579,169), both alpha=255.
- disassembly makes the front helper write leftward from a source position: offsets begin at 1 and continue while offset < param_9; the effective span is int(param_9 * param_11), subject to clipping.

## Witness

| target | source after rowdriver | B after scatter | writeback B | Windows final |
| --- | --- | --- | --- | --- |
| `(494, 169)` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `[164, 0, 0, 255]` |
| `(579, 169)` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `[25, 0, 0, 255]` |

## INFERENCE

- source (959,169) is expected zero before scatter under this source/staging model; it cannot itself explain Windows red=164 when A is loaded from the before-effects image.
- red=164 must arise from a different populated source/staging path, a different contributing source coordinate/group, or a later host-store path; it is not evidence for changing coefficients.
- this witness does not identify which of those Windows-side paths produced red=164 because final host pixel storage is not observed by FUN_1800038d0-only capture.

## Exact Next Boundary

Capture one real helper call that writes the target B record for (494,169) or (579,169), with the exact source coordinate, B destination address/record, pre/post B floats, and the final host-store bytes in the same run. Keep the required source coordinate fixed at (959,169) and do not tune coefficients.
