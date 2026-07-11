# OLMDistanceGradation case_0023 Source Model Audit - 2026-07-07

- Status: `source-model-matches-aex-helper-samples`
- Source: `scripts/materialize_distancegradation_case0023_source_model_audit.py`
- AEX helper input: `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`
- Source PNG: `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png`
- Inside threshold: `36`
- Outside threshold: `0`
- Safe claim: For the recorded case_0023 witness points, a Mac-source-shaped Constant/BOTH field model matches the Windows AEX CPU helper samples. This is not AE exact, but it makes broad field-helper retuning unsafe and keeps the live lane on reference/export/source ownership.

| XY | Mac inside | AEX inside | Mac outside | AEX outside | Mac both | AEX both | match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(1698,7)` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `True` |
| `(1699,7)` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `True` |
| `(1700,7)` | `0.0` | `0.0` | `1.0` | `1.0` | `1.0` | `1.0` | `True` |
| `(1699,6)` | `0.0` | `0.0` | `1.0` | `1.0` | `1.0` | `1.0` | `True` |
| `(1699,8)` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `True` |
| `(414,393)` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `True` |
| `(415,393)` | `1.0` | `1.0` | `0.0` | `0.0` | `1.0` | `1.0` | `True` |
| `(416,393)` | `1.0` | `1.0` | `0.0` | `0.0` | `1.0` | `1.0` | `True` |
| `(415,392)` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `0.0` | `True` |
| `(415,394)` | `1.0` | `1.0` | `0.0` | `0.0` | `1.0` | `1.0` | `True` |

## Limitations

- comparison is sampled at the recorded witness points, not a full image diff against an exported Windows field buffer
- model uses the already-grounded OpenCV-detour EDT implementation rather than re-entering the Mac plug-in binary
- this does not settle stale packaged PNG vs current Windows Software export provenance
