# OLMRadialBlur Zoom Case 0009 Sampler Args Intake (2026-07-10)

## Accepted Return

- NAS return: `20260710_194000__RETURN__olm_runtime_trace_radialblur_zoom_case0009_sampler_args_20260710__answered_partial_portable.zip`
- Request: `olmradialblur_zoom_case0009_sampler_args_20260710`
- Status: `answered_partial`

The `answered_partial` status is only due to the post-capture AE PNG write
failure. The requested one-run CDB facts were returned for all three target
coordinates and are usable as runtime evidence.

## Facts

The coordinate gate was `(EBX, R13D) = (x, y)` at the static call site
`OLMRadialBlur+0x5e68`, with the paired return at `+0x5e6d`.

| Target | RCX pool | RDX/RDI result cell | R8 | R9 |
| --- | --- | --- | ---: | ---: |
| `(7, 0)` | `0x000001aea1e45050` | `0x000001ae9c0990c0` | 1104 | 1800 |
| `(8, 0)` | `0x000001aea1e45050` | `0x000001ae9c0990d0` | 1104 | 1800 |
| `(24, 0)` | `0x000001aea1e45050` | `0x000001ae9c0991d0` | 1104 | 1800 |

The result cells advance by 16 bytes per output pixel, consistent with a
four-float RGBA destination. Static disassembly identifies the target as
`FUN_180009d80`, the alpha-weighted bilinear sampler.

## Limits

- This return does not contain a fresh output PNG because AE reported a PNG
  write failure after capture.
- The stack coordinate values and returned RGBA cells are available in the
  bundled CDB trace, but are not yet a complete end-to-end witness for the
  remaining RadialBlur residual.

## Next Action

Map the captured call arguments and returned cells to the Mac sampler's
coordinate, border, alpha-normalization, and writeback stages. Do not perform
PNG-only tuning from this trace.
