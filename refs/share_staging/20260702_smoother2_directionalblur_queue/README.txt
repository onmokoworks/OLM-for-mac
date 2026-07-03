Smoother2 current-AEX and DirectionalBlur witness-log queue prepared on 2026-07-02.

Target zips:
- olm_runtime_trace_smoother2_current_aex_producer_path_diff_20260702.zip
- olm_runtime_trace_directionalblur_witness_logging_prep_20260702.zip

Why:
- Smoother2 legacy current-AEX is now writer-anchored. The next useful Windows pass is not a broad rerun; it is the first unresolved producer-stage proof for 0004 / 0012.
- DirectionalBlur is now narrowed to two witness lanes. The next useful Windows pass must return typed A/B mapping, denominator, alpha_or_valid or validity, pre-writeback RGBA, and lane-specific helper or rotate facts.

Contracts:
- refs/conformance/olmsmoother2_producer_path_diff_20260702.md
- refs/conformance/olmdirectionalblur_witness_logging_prep_20260702.md
