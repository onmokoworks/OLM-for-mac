# OLMDistanceGradation Pending Layer/no-bg Proof

- Active request: `olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629`
- Runtime package: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/runtime_trace_packages/olm_runtime_trace_distancegradation_layer_no_bg_source_ownership_20260629.zip`
- Latest runtime summary: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/runtime_trace_summary_distancegradation_layer_no_bg_source_ownership_20260629_235638.json`
- Priority: `1`

## Decision Boundary

Determine whether Windows Layer/no-bg 16bpc compose derives RGB from straight source times output alpha, from already-premultiplied source, or from another ownership rule.

## Why PNG Alone Is Not Enough

- The direct Layer/no-bg unpremultiply hypothesis is already rejected because it widened coverage from 25421 to 285406 changed pixels.
- The current narrowed Mac fix matches the primary case_0012 witness alpha and nearly matches RGB, but the family is still not AE exact.
- The remaining ambiguity is the exact source RGB ownership inside the Windows compose branch, not a generic threshold or writeback issue.

## Witness Focus

### olmdistancegradation_extended__case_0012

- Family: `layer-no-bg-source-or-alpha-ownership`
- Changed pixels: `25421`
- Use: Primary Layer/no-bg source-ownership branch proof.
- Primary point A: `{'x': 462, 'y': 7, 'input': [16255, 16255, 16255, 32639], 'reference': [32371, 32371, 32371, 64997], 'candidate': [16121, 16121, 16121, 64997], 'delta': [-16250, -16250, -16250, 0]}`
- Primary point B: `{'x': 72, 'y': 8, 'input': [16255, 16255, 16255, 32639], 'reference': [32371, 32371, 32371, 64997], 'candidate': [16121, 16121, 16121, 64997], 'delta': [-16250, -16250, -16250, 0]}`
- Current reverted max witness: `{'x': 462, 'y': 7, 'channel': 0, 'ref': [32371, 32371, 32371, 64997], 'candidate': [16121, 16121, 16121, 64997], 'delta': [-16250, -16250, -16250, 0]}`
- Latest Windows runtime note: `{'branch_decision': {'uses_straight_source_times_output_alpha': True, 'uses_premultiplied_source_directly': False, 'uses_other_source_ownership_rule': False, 'failed_breakpoint_or_watchpoint_reason': "cdb launched AE 2026 and armed the startup trace, but the retry stalled during AE/plugin startup before DistanceGradation+0x1170480 callback hits were produced. See included cdb logs. Numeric ownership facts here are derived from the request's source/reference witness pixels."}, 'pixels': [{'x': 462, 'y': 7, 'source_input_rgba16': [16255, 16255, 16255, 32639], 'windows_reference_rgba16': [32371, 32371, 32371, 64997], 'mac_candidate_rgba16': [16121, 16121, 16121, 64997], 'derived_output_alpha_norm': 0.991790646, 'derived_source_straight_rgb16': [32633, 32633, 32633], 'derived_straight_times_output_alpha_rgb16': [32365, 32365, 32365], 'derived_premultiplied_source_times_output_alpha_rgb16': [16122, 16122, 16122], 'interpretation': 'Windows RGB is near straight_source_rgb * output_alpha. Mac candidate is near premultiplied_source_rgb * output_alpha.'}, {'x': 72, 'y': 8, 'source_input_rgba16': [16255, 16255, 16255, 32639], 'windows_reference_rgba16': [32371, 32371, 32371, 64997], 'mac_candidate_rgba16': [16121, 16121, 16121, 64997], 'derived_output_alpha_norm': 0.991790646, 'derived_source_straight_rgb16': [32633, 32633, 32633], 'derived_straight_times_output_alpha_rgb16': [32365, 32365, 32365], 'derived_premultiplied_source_times_output_alpha_rgb16': [16122, 16122, 16122], 'interpretation': 'Same ownership rule as the primary witness.'}]}`

### olmdistancegradation_extended__case_0016

- Family: `layer-no-bg-companion-ownership-separator`
- Use: Companion Layer/no-bg witness that cleanly separates straight-source-times-output-alpha from double-premultiplied ownership.
- Companion point(s): `[{'x': 106, 'y': 19, 'source_input_rgba16': [29125, 29125, 29125, 43689], 'windows_reference_rgba16': [29125, 29125, 29125, 43689], 'mac_candidate_rgba16': [19415, 19415, 19415, 43689], 'derived_output_alpha_norm': 0.666651408, 'derived_source_straight_rgb16': [43688, 43688, 43688], 'derived_straight_times_output_alpha_rgb16': [29125, 29125, 29125], 'derived_premultiplied_source_times_output_alpha_rgb16': [19415, 19415, 19415], 'interpretation': 'The companion witness exactly separates the two ownership rules: Windows equals straight source premultiplied by output alpha, while Mac equals premultiplied source multiplied by output alpha again.'}]`

### olmdistancegradation_extended__case_0020

- Family: `constant-bg-binary-sparse-full-color`
- Changed pixels: `1001`
- Use: Secondary Constant/background control family; not the current runtime-trace target.
- Control point A: `{'x': 951, 'y': 417, 'input': [65535, 0, 0, 65535], 'reference': [7195, 0, 61165, 65535], 'candidate': [65535, 0, 0, 65535], 'delta': [58340, 0, -61165, 0]}`
- Control point B: `{'x': 950, 'y': 417, 'input': [65535, 0, 0, 65535], 'reference': [7195, 0, 61165, 65535], 'candidate': [7195, 0, 61165, 65535], 'delta': [0, 0, 0, 0]}`

## Actionable Return Criteria

- It records the actual source-layer RGBA values consumed by the Windows Layer/no-bg compose path at case_0012/case_0016 witnesses.
- It records any premultiply or unpremultiply step between source-layer read and the already supported straight-source-times-output-alpha branch.
- It records the output floats before 16bpc writeback and the final RGBA16 words at the same pixels.

## Not Actionable

- It only returns final PNG or final RGBA16 values without the compose-path source ownership steps.
- It records the wrong branch family (for example only case_0020 Constant/background behavior).
- It confirms values after the point where RGB ownership has already been collapsed and cannot distinguish straight vs premultiplied source handling.
