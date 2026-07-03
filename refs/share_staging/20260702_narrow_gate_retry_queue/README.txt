Narrow witness-gate retry queue prepared on 2026-07-02.

Target zips:
- olm_runtime_trace_smoother2_current_aex_0004_writer_gate_retry_20260702.zip
- olm_runtime_trace_directionalblur_angle0_helper_gate_retry_20260702.zip

Why:
- Fresh CDB retries proved both plugins execute, but broad breakpoints hit-storm before witness-local values are retained.
- These two packages narrow the ask to one lane each so Windows can gate before the storm expands.

Read first:
- refs/conformance/smoother2_directionalblur_runtime_retry_contract_20260702.md
- refs/conformance/olmsmoother2_current_aex_0004_writer_gate_retry_20260702.md
- refs/conformance/olmdirectionalblur_angle0_helper_gate_retry_20260702.md

Intent:
- Smoother2: only `legacy_case_0004_current_aex (1903,519)`, gated from writer frame into exact producer call.
- DirectionalBlur: only real angle-0 witness lane `(494,169)` + `(579,169)`, no surrogate load case, no broad `+0x2000` answer.
