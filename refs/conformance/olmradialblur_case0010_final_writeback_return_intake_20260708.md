# OLMRadialBlur Case 0010 Final-Writeback Return Intake - 2026-07-08

## Verdict

`olmradialblur_case0010_final_writeback_20260708` returned
`answered_partial`.

This is useful provenance evidence, but it is not a full binary/runtime proof:
the return did not capture a fresh same-run Windows debugger stop tying
`+0xf250`, `+0xf252`, collapsed `+0xe`, direct `+0xe` inverse sampling,
output-buffer writeback, and exported PNG byte together.

## Facts

- Return zip:
  `/Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_radialblur_case0010_final_writeback_20260708_windows.zip`
- Runtime summary:
  `refs/reports/runtime_trace_summary.json`
- Focused comparison:
  `refs/reports/runtime_trace_comparisons/olmradialblur_case0010_final_writeback_20260708.md`
- Primary witness:
  `case_0010`, output pixel `(1614,6)`.
- Legacy 2026-06-04 Windows reference at `(1614,6)`:
  `[255,255,255,255]`.
- Current package-bundled Windows SOFTWARE recapture at `(1614,6)`:
  `[237,237,237,255]`, with `project_gpu_accel_type.current_name = SOFTWARE`.
- Local / bundled direct collapsed `+0xe` inverse-sampler result:
  `[-0.004081939, -0.004081939, -0.004081939, 1.0]`, clamping to
  `[0,0,0,255]`.
- Local output-world byte retained in the return:
  `[0,0,0,0]`.

## Classification

The current classification is:

`tiny_rotation:case0010-final-writeback-partial-missing-same-run-debugger-stop`

The return narrows the lane to a final-writeback/export/provenance split:
Windows SOFTWARE still exports a bright pixel at the witness, but the direct
collapsed `+0xe` path remains black. The old legacy `[255,255,255,255]`
reference is also not sufficient as the only target, because current Windows
SOFTWARE is bright but not byte-identical to the legacy value.

## Allowed Next Step

If this lane is pursued further, request one same-run Windows debugger stop for
`case_0010 (1614,6)` that captures:

- exact AEX path/version and module base
- four contributing polar cells around `(1603.839558785, 844.317504883)`
- each cell's `+0xf250`, `+0xf252`, and collapsed `+0xe`
- direct inverse-sampler result from collapsed `+0xe`
- output-buffer RGBA immediately after writeback
- exported PNG byte from that exact same render

## Forbidden Actions

- Do not tune Mac scatter, final byte conversion, or validity handling from
  this partial return.
- Do not treat the legacy white `[255,255,255,255]` witness as a current
  single source of truth.
- Do not mark RadialBlur tiny Rotation as binary-grounded or AE exact from this
  return.
