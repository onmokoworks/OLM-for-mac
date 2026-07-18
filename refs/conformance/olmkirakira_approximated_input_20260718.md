# OLMKiraKira Approximated Input contract audit (2026-07-18)

Status: **binary_grounded_runtime_boundary_before_resize**
AE exact: **false**

## Determined contract

| Item | Contract | Evidence class |
| --- | --- | --- |
| Enable gate | strict `render_scale_ratio > 0.5`; otherwise the checkbox state is cleared | binary-grounded |
| Ratio | `render_width / render_info_width` and the corresponding height ratio are represented by the render-info fields; enabled path applies `ratio * 0.5` | binary-grounded |
| Working size | `int_truncate(src_width * 0.5)`, `int_truncate(src_height * 0.5)` | binary-grounded |
| Ray lengths | each length is `int_truncate(length * effective_scale)` | binary-grounded |
| Pre-resize | source Mat to working Mat with explicit working `dsize` | binary-grounded |
| Post-resize | working Mat to original-size Mat with explicit original `dsize` | binary-grounded |
| Interpolation | OpenCV `INTER_NEAREST` (`0`) | binary-grounded from both typed-owner callsites |
| Border | no border mode is passed; no plugin border branch | binary-grounded |
| Alpha | no premultiply/unpremultiply or alpha-specific branch; resize operates on Mat channels | binary-grounded wrapper audit |
| Rounding | typed owners truncate working dimensions/lengths; resize wrapper receives explicit dsize, so its `cvRound` fallback is not selected | binary-grounded |

## Runtime boundary

The existing bounded actual-AEX common-owner harness was run with
`Approximated Input=1` injected only in memory. It entered the common owner but
stopped at an existing `cv::FilterEngine::init` assertion before reaching
`FUN_1812639f0`. This is recorded as a fail-closed runtime boundary, not as
evidence that the resize branch is absent.

## Re-run

`python3 tools/emulation/audit_olmkirakira_approximated_input_20260718.py`

No production plugin source was edited. The next implementation step, if taken,
should be an isolated resize primitive using OpenCV 4.5.5 `INTER_NEAREST` and
explicit dsize, followed by a real Windows/Mac AE differential. This report does
not authorize changing the production plugin by itself.
