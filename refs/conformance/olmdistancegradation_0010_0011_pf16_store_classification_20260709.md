# OLMDistanceGradation 0010/0011 PF16 Store Classification

Date: 2026-07-09

## Decision

The pointer-map return moves `case_0010/0011` out of "Windows address binding"
and into a pre-store float / field packing lane.

The remaining sparse R/A difference is not explained by changing only the final
Mac `clamp16()` rounding rule.

## Facts

Windows return:
`refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md`

Mac local probes:

- `refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md`
- `refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md`

| Pixel | Mac `field_x` | Mac `out_a` | Mac store | Windows `xmm2_alpha` | Windows store word |
| --- | ---: | ---: | ---: | ---: | ---: |
| `case_0010 (6,40)` | `0.900283873` | `0.0997161269` | `3267` | `0.0997314` | `3268` |
| `case_0010 (901,394)` | `0.69859308` | `0.30140692` | `9877` | `0.301392` | `9876` |

The Windows writer sites are:

- `DistanceGradation+0x1170814`
- `DistanceGradation+0x117081c`
- `DistanceGradation+0x1170824`
- `DistanceGradation+0x117082b`

The AEX writer path is consistent with `cvttss2si`-style float-to-int
conversion, but that alone is not a valid Mac fix:

- At `(901,394)`, truncating the Mac value `9876.501...` would match Windows
  `9876`.
- At `(6,40)`, truncating the Mac value `3267.498...` would keep `3267`, while
  Windows stores `3268`.

The Windows `xmm2_alpha` values are already very close to the stored PF16 word
grid:

- `(6,40)`: `0.0997314 * 32768 ~= 3268`.
- `(901,394)`: `0.301392 * 32768 ~= 9876`.

## Inference

The split is upstream of or inside the pre-store float generation, not merely
the final `clamp16()` conversion. The plausible live causes are:

- the field world is packed/read back on a PF16-like grid before compose;
- Windows uses a slightly different normalized field value at the half-boundary;
- the 16bpc callback reads a channel/word that has already been quantized by
  the AEX/OpenCV/PF pipeline;
- there is a channel-order or lane-handling detail around the writer, but the
  output address formula itself is now proven.

This evidence permits local Mac-side experiments that alter how the 16bpc
distance field is packed/read for the sparse family, but it forbids a global
store rounding toggle.

## Next

Inspect the Mac 16bpc field-world representation and the AEX 16bpc compose
callback around the field read. The specific question is:

Does Windows consume a quantized field value such that `out_a` is already on
the PF16 word grid before the final writer?

Only if local classification cannot prove that should the next Windows ask be a
same-run true16 TIFF/EXR export sample tied to these watchpoints.
