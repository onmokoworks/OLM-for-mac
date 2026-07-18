# OLMKiraKira Highlight Modes 3/4 Audit (2026-07-18)

Status: **blocked_mode34_radius_semantics_color_shared_boundary**
AE exact: **false**
Production edit: **none**

## Result

The fifth layer is statically identified as Highlight. Its radius becomes an
odd square kernel, `(2r+1) x (2r+1)`, before the blur-mode dispatch.

| Mode | Recovered path | What is proven | What remains unproven |
| --- | --- | --- | --- |
| 3 | `FUN_181272ec0` | Direct helper witness reaches embedded OpenCV 4.5.5 `GaussianBlur` and returns 63 `CV_32FC1` words | full fifth-layer caller binding, kernel/border/writeback contract for all Highlight Radius values, and pre-aggregation Highlight buffer |
| 4 | inline body in `FUN_18114f4a0` | Three `FUN_181280bc0` calls and a scalar gain update are present | recurrence, pass order, edge policy, gain normalization, and writeback contract |

## Highlight Color

The recovered blur helper handles a scalar layer buffer. It does not load the
Highlight Color there. The color is applied later by the shared aggregation
operation (`AddColoredUnion` in the Mac port). No Mode 3/4-specific color
transform is proven, so this audit does not change color handling.

## Evidence

- Static sources: `decomp/OLMKiraKira.aex.c.txt`, `disasm/OLMKiraKira.aex.asm.txt`.
- Actual-AEX witness: `refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json`.
- Witness scope: direct `FUN_181150790` helper invocation; it is not a full `FUN_18114f4a0` fifth-layer end-to-end capture.
- Mode 3 call: `0x18114fa27 -> 0x181272ec0`, return capture at `0x181151105`.
- Mode 4 body: `0x181150979..0x181150f3a`, with three calls to `0x181280bc0`.

## Decision

Do not replace the current Mode 3/4 placeholder with a conventional Gaussian,
recursive blur, or PNG-tuned approximation. The production source remains
fail-closed for Highlight Radius in Modes 3/4. The next useful Windows/AEX
witness is a same-run capture of the fifth-layer buffer before color
aggregation, followed by a separate Highlight Color-only caller witness.

## Re-run

`python3 tools/emulation/audit_olmkirakira_highlight_modes34_20260718.py`

`python3 tools/emulation/test_olmkirakira_highlight_modes34_20260718.py`
