# OLMRadialBlur Scatter Caller, 2026-07-17

- Status: `pass`
- Caller: `0x1800024c0`
- Anchor: `0x180002520`
- Tail helper: `0x180001c90`
- Source and destination planes use absolute radius rows; `start_radius` selects the first visited row.
- Actual-AEX and portable gates skip `valid=0`, `alpha=0`, `span=0`, `alpha=NaN`, and `span=NaN`.
- Negative finite alpha and span remain active; AEX tail-entry hooks record both outer and inner calls for `alpha=-0.5` and `span=-1`.
- Actual-AEX tail entry instrumentation records outer (`direction=0`) before inner (`direction=1`) for the active `start_radius=1` cell.
- Mode-1 `INT_MAX + 1` wraps to `INT32_MIN` with defined portable arithmetic; the bounded AEX helper fixture captures effective length `INT32_MIN` and unchanged buffers.
- The release and UBSan caller probes include the mode-1 overflow case; both pass.
- DAT_1800212d4 is preserved as float32 `1.0f`; no fast math is permitted.
- Intentional bounds divergences are limited to portable preflight/bailouts and are outside the AEX undersized-buffer claim.
- This is not an AE-exact, production-wiring, or broad-equivalence claim.

## Reproduce

```text
python3 tools/emulation/test_radialblur_scatter_caller_20260717.py
python3 tools/emulation/test_radialblur_scatter_tail_equivalence_20260717.py
```
