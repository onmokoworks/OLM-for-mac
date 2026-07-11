# OLMRadialBlur case_0010 static witness summary

## FACT

- This report reuses existing local artifacts rather than rerunning `tools/emulation/test_m4_case0010.py` or `tools/emulation/test_m5_case0010_cell_writes.py`.
- Source artifacts: `tools/emulation/M4_REPORT.md` and `tools/emulation/M5_CELL_WRITES.json`.
- Buffers from the captured run: `f250=0x268e4800`, `f252=0x28737000`, `+0xe=0x28ecba00`.
- Render facts carried forward from M5: `angular_cols=1800`, `quality_recip=0.20000000298023224`, `elapsed=114.59s`.
- Final-sampler probe for `case_0010 (1614,6)`: radius `844.317504883`, angle `5.598455906`, sample coords `(1603.839558785, 844.317504883)`, direct `+0xe` RGBA `(-0.004081939, -0.004081939, -0.004081939, 1.0)`, u8 `(0, 0, 0, 255)`.
- Local output-world bytes for `(1614,6)`: ARGB `(0, 0, 0, 0)`, RGBA `(0, 0, 0, 0)`.

## Witness Neighborhood

| Cell | Role | `+0xf250.rgba` | `+0xf252` | collapsed `+0xe.rgba` |
| --- | --- | --- | --- | --- |
| `row844_col1603` | witness southwest | `[-0.025617070496082306, -0.025617070496082306, -0.025617070496082306, 1.7418659925460815]` | `[0.0, 0.0, 0.0, 1.0]` | `[-0.014706682413816452, -0.014706682413816452, -0.014706682413816452, 1.0]` |
| `row844_col1604` | witness southeast | `[0.0, 0.0, 0.0, 1.741865993]` | `n/a` | `['00000000', '00000000', '00000000', '3f800000']` |
| `row845_col1603` | witness northwest | `[-0.0845475047826767, -0.0845475047826767, -0.0845475047826767, 1.7418659925460815]` | `[0.0, 0.0, 0.0, 1.0]` | `[-0.048538465052843094, -0.048538465052843094, -0.048538465052843094, 1.0]` |
| `row845_col1604` | witness northeast | `[0.0, 0.0, 0.0, 1.741865993]` | `n/a` | `['00000000', '00000000', '00000000', '3f800000']` |

## INFERENCE

- This bounded summary complements the planned Windows same-run final-writeback/provenance witness; it does not replace it.
- The local artifacts are already enough to restate the black direct-sampler outcome for `(1614,6)` without another multi-minute rerun.
- They are not enough to prove the missing Windows relation for `+0xf252 -> +0xe.alpha -> final output` at both col1603 and col1604, because the current local capture lacks `+0xf252` for the `1604` column and lacks a true Windows final-writeback dump.
