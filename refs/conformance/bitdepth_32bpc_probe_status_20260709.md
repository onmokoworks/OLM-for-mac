# 32bpc Probe Status

This note freezes the current committed 32bpc probe state so that
32bpc evidence does not live only in ignored reports or ad-hoc memory.

- Generated at: `2026-07-09T08:37:16Z`
- Compare policy: `refs/conformance/bitdepth_32bpc_compare_policy_20260703.md`

| Lane | Cases | Classification | float-preserving | Share | Next action |
| --- | ---: | --- | --- | --- | --- |
| `OLMColorKey / focused 32bpc probe` | `9` | `probe-only-png-return` | `False` | `False` | Keep this return probe-only because it is PNG-only; wait for a float-preserving EXR-first return before any 32bpc exact claim. |
| `Cross-plugin batch / broad 32bpc full probe` | `48` | `probe-only-png-return` | `False` | `False` | Keep this broad batch probe-only because it is PNG-only; request a float-preserving EXR-first rerun before any 32bpc exact claim. |
| `Cross-plugin batch / broad 32bpc EXR-first rerun` | `48` | `probe-only-png-return` | `False` | `False` | The EXR-first rerun still came back PNG-only/non-float-preserving, so it remains probe-only. Another Windows return must preserve float samples before any 32bpc exact claim. |

## Lane details

### OLMColorKey - focused 32bpc probe

- Request id: `olm_bitdepth_32bpc_colorkey_probe_20260703`
- Request JSON: `refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json`
- Package zip: `refs/runtime_trace_packages/olm_reference_request_32bpc_colorkey_probe_20260703.zip`
- Share copy: `olm_reference_request_32bpc_colorkey_probe_20260703.zip` (`present=False`)
- Cases: `9`
- Plug-ins covered: `['OLMColorKey']`
- Classification: `probe-only-png-return`
- float_preserving_present: `False`
- preferred_exr_present: `False`
- Reference quality reason: `32bpc request contract matched, but the return is PNG-only/non-float-preserving, so it remains probe-only.`
- Next action: Keep this return probe-only because it is PNG-only; wait for a float-preserving EXR-first return before any 32bpc exact claim.

- Returned dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_colorkey_probe`
- Imported dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_colorkey_probe/OLMbit-depthconformancebatch`
- Returned asset formats: `{'.png': 18}`

### Cross-plugin batch - broad 32bpc full probe

- Request id: `olm_bitdepth_32bpc_full_probe_20260703`
- Request JSON: `refs/reference_requests/olm_bitdepth_32bpc_full_probe_20260703.json`
- Package zip: `refs/runtime_trace_packages/olm_reference_request_32bpc_full_probe_20260703.zip`
- Share copy: `olm_reference_request_32bpc_full_probe_20260703.zip` (`present=False`)
- Cases: `48`
- Plug-ins covered: `['OLMBlur', 'OLMColorKey', 'OLMDistanceGradation', 'OLMToonDilate']`
- Classification: `probe-only-png-return`
- float_preserving_present: `False`
- preferred_exr_present: `False`
- Reference quality reason: `32bpc request contract matched, but the return is PNG-only/non-float-preserving, so it remains probe-only.`
- Next action: Keep this broad batch probe-only because it is PNG-only; request a float-preserving EXR-first rerun before any 32bpc exact claim.

- Returned dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe`
- Imported dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe/OLMbit-depthconformancebatch`
- Returned asset formats: `{'.png': 96}`

### Cross-plugin batch - broad 32bpc EXR-first rerun

- Request id: `olm_bitdepth_32bpc_full_probe_exr_rerun_20260703`
- Request JSON: `refs/reference_requests/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json`
- Package zip: `refs/runtime_trace_packages/olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip`
- Share copy: `olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip` (`present=False`)
- Cases: `48`
- Plug-ins covered: `['OLMBlur', 'OLMColorKey', 'OLMDistanceGradation', 'OLMToonDilate']`
- Classification: `probe-only-png-return`
- float_preserving_present: `False`
- preferred_exr_present: `False`
- Reference quality reason: `32bpc request contract matched, but the return is PNG-only/non-float-preserving, so it remains probe-only.`
- Next action: The EXR-first rerun still came back PNG-only/non-float-preserving, so it remains probe-only. Another Windows return must preserve float samples before any 32bpc exact claim.

- Returned dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun`
- Imported dir: `refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun/OLMbit-depthconformancebatch`
- Returned asset formats: `{'.png': 96}`

## Interpretation

- A PNG-only 32bpc return is useful as a probe and as request coverage proof, but not as `AE exact` evidence.
- A float-preserving return may be compared mechanically now that `verify_manifest.py` keeps EXR/TIFF/HDR companions in float compare mode.
- The broad full batch is intentionally tracked even before return so Windows/Mac handoff state stays explicit.
