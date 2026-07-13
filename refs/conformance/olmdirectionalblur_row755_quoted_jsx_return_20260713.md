# OLM Runtime Trace Return Summary

- Source: runtime-trace-return
- Package: refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_chunked_capture_20260712.zip

## Required Requests

| Request | Answered | Count | Statuses |
| --- | --- | ---: | --- |
| olmdirectionalblur_alpha_fade_fullrender_row755_20260712 | no | 3 | exact_bind_failure |

## Results

### olmdirectionalblur_alpha_fade_fullrender_row755_20260712

- Status: exact_bind_failure
- Source file: RETURN_RUNTIME_TRACE.json
- Summary: -

Observations:

  - aex: {"path": "C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\OLM\\OLMDirectionalBlur.aex", "sha256": "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e", "size": 56832}
  - failure: {"details": {"attempt_trace": "artifacts/attempt_RETURN_RUNTIME_TRACE.json", "missing_artifacts": ["ae_ready.marker", "ae_render.log", "ae_render_result.json", "cdb_output.txt", "cdb_stderr.txt", "row755_destination_rgba_f32_le.bin", "row755_denominator_f32_le.bin", "row755_alpha_valid_f32_le.bin"], "run_listing": "artifacts/run_listing.json"}, "reason": "The quoted-JSX retry still never wrote `ae_ready.marker`. The AE script did not reach its pause handshake, so module lookup, CDB attach, chunk capture, and chunk combine never started.", "stage": "ae_pause"}
  - run_id: dblur-row755-294e8b9aacf24dfaaea3bcdda8441856
  - schema: 1

### olmdirectionalblur_alpha_fade_fullrender_row755_20260712

- Status: exact_bind_failure
- Source file: artifacts/attempt_RETURN_RUNTIME_TRACE.json
- Summary: -

Observations:

  - failure: {"reason": "ready marker not written", "stage": "ae_pause"}
  - run_id: dblur-row755-294e8b9aacf24dfaaea3bcdda8441856
  - schema: 1

### olmdirectionalblur_alpha_fade_fullrender_row755_20260712

- Status: exact_bind_failure
- Source file: run_summary.json
- Summary: -

Observations:

  - failure: {"reason": "quoted-jsx retry still never reached pause handshake", "stage": "ae_pause"}
  - run_id: dblur-row755-294e8b9aacf24dfaaea3bcdda8441856
  - schema: 1
