# OLMKiraKira Mode4 Highlight gradient PF32 seam（2026-08-12）

Status: **historical fail-closed snapshot; superseded by raw-exact closure**

This file describes the immutable historical seam captured before the recovered
2-D box-filter rounding order was implemented. In that snapshot, the 5×3 gradient's
same-run Highlight ray first differed at words 3 and 11 by one ULP each; downstream
aggregation and typed writers were exact for the supplied actual ray.

The bounded 5×3 / Highlight Radius 3 / kernel 7 public Mode 4 tuple is now raw-exact
at PF8, PF16, and PF32. The current evidence and claim boundary are recorded in
`olmkirakira_mode4_highlight_gradient_closure_20260812.json`; compatibility metadata
and both artifact hashes are recorded in
`olmkirakira_mode4_highlight_gradient_pf32_seam_supersession_20260812.json`.
