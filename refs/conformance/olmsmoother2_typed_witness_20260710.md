# OLMSmoother2 Typed Witness

- Status: `local-aex-cpu-execution`
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`
- Functions: `FUN_18000e170, FUN_18000f270, FUN_18000e3a0`
- Witness: `legacy current-AEX (91,841)`
- Descriptor: `[91,841,1,91,843,5]`
- Boundary: this result is not Windows truth and not AE exact evidence; Mac source was not modified.

| Case | center_b0 | prev_b0 | left_b1 | c | f270 | e3a0 | chain append |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `legacy_current_aex` | 0 | 1 | 0 | 2 | `True` | `True` | `True` |
| `control_suppressing` | 0 | 0 | 1 | 4 | `False` | `True` | `False` |

- Shape assertions: `PASS`.
- The legacy row is the requested `c=2 / f270=1 / e3a0=1` path.
- The control row is the requested `c=4 / chain append=0` path; direct e3a0 execution is recorded separately.
