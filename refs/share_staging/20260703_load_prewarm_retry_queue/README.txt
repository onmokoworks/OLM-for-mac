Load-prewarm retry queue prepared on 2026-07-03.

Target zips:
- olm_runtime_trace_smoother2_current_aex_0004_load_prewarm_retry_20260703.zip
- olm_runtime_trace_directionalblur_angle0_load_prewarm_retry_20260703.zip

Why:
- The previous exact-gated retries did not fail from noisy witness breakpoints.
- They failed earlier: AE/CDB startup reached `sxe ld:<module>`, but target module load never appeared before timeout.
- So the next useful retry is to stabilize module load on the exact case/project path before returning to witness-local gating.

Read first:
- refs/conformance/smoother2_directionalblur_startup_stall_retry_20260703.md
- refs/conformance/olmsmoother2_current_aex_0004_writer_gate_retry_20260702.md
- refs/conformance/olmdirectionalblur_angle0_helper_gate_retry_20260702.md

Intent:
- first prove exact-case module load
- only then re-bind a narrow gate in the same session if possible
