Smoother2 current-AEX and DirectionalBlur runtime retry queue prepared on 2026-07-02.

Target zips:
- olm_runtime_trace_smoother2_current_aex_producer_path_diff_retry_20260702.zip
- olm_runtime_trace_directionalblur_witness_logging_prep_retry_20260702.zip

Why this retry exists:
- The previous returns were not new traces. They mostly restated retained evidence.
- So this retry tightens the execution contract: a new return is only useful if it contains fresh typed witness values, or a fresh exact failed breakpoint/watchpoint or module-load condition.

Read first:
- refs/conformance/smoother2_directionalblur_runtime_retry_contract_20260702.md
- refs/conformance/olmsmoother2_producer_path_diff_20260702.md
- refs/conformance/olmdirectionalblur_witness_logging_prep_20260702.md

Hard rule:
- Repeating known writer-anchor facts or retained contract text is failure, not partial success.
