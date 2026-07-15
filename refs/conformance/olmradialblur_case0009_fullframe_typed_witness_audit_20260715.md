# OLMRadialBlur case0009 Full-Frame Typed Witness Audit - 2026-07-15

## Scope

This note owns only the Windows-side RadialBlur `case_0009` full-frame typed
witness package, classifier/validator, and smoke coverage. It does not edit
Mac RadialBlur code and does not edit `notes/CONFORMANCE_LEDGER.md`.

## FACT

- The acceptance unit is one Windows AE Software run at `1920x1080`, 8bpc,
  with the render, AEX identity, debugger trace, and exported PNG bound by the
  same `run_id`.
- The required semantic points remain `(7,0)`, `(8,0)`, and `(24,0)`.
- The validator now rejects a point unless it contains typed inverse
  coordinates and index words, four nonzero distinct cell IDs/addresses,
  four-cell accumulation/denominator/valid/final RGBA payloads, bilinear
  weights, final alpha values, and the same-run marker.
- The validator also requires `ae_result.run_id` and the Software log marker to
  equal the trace run, and records the exported RGBA8 byte tuple in the bound
  witness after validating the exact full-frame PNG.
- Queue bootstrap `run_id`, canonical work/root paths, queue SHA-256, and queue
  start/end markers are required to bind the export to the trace run; cross-run
  and wrong-queue-hash fixtures are rejected by the dedicated smoke.
- Package generation deterministically hardens the generated CDB so cell IDs
  are emitted from the live sampler pointers instead of the old textual
  `00/10/01/11` placeholders. The source template remains unchanged; the
  generated archive is the sendable artifact.
- Focused verification passed:
  `python3 refs/scripts/smoke_windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.py`
  returned `[OK] ... deterministic and fail-closed`.
- The generator completed successfully; the regenerated archive passed
  `unzip -t`; its packaged validator hash is
  `0e3b62935f2bc0dd013378cdcc3ee8e9b5d8dc13dfdeac30d6c8505cc58c9c27`.
- The old reduced `32x32` geometry and quality-step-90 probe is not used as
  semantic truth. Its existing classification says downstream indices/cells
  are non-semantic under that harness.

## INFERENCE

- The package is now suitable to send for a fresh Windows capture because a
  missing production geometry, placeholder cell identity, incomplete typed
  payload, mixed run, or missing export binding fails closed.
- This package alone does not establish Windows AE Software vs Mac AE
  compatibility. The required final criterion remains `max_diff=0` on the
  paired Windows/Mac AE outputs; CLI/emulation remains intermediate evidence
  only.
- No Mac algorithm change is authorized or implied by this witness audit.

## Artifact

`refs/runtime_trace_packages/windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.zip`
