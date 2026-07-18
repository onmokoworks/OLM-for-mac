# OLMRadialBlur typed deep render (2026-07-18)

Status: `known_red_production_polar_and_internal_pf32_frame`

The Mac production source now executes typed Zoom processing for PF16 and
PF32 instead of copying the input unchanged. PF8 keeps its existing path.

## Evidence

- Actual-AEX normalized polar plane: `31,795,200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
- Production normalized polar plane: `31,795,200` bytes, `64b237cd1e46d65aef300f94caf5bec1b45bfac9a2b9b945f86780f435e64cdd`
- Production polar differing bytes: `13,953,051`
- First polar difference: byte `6`, float word `1`, angle `0`, radius `0`, channel `G`
- First polar values/bits: production `2.609024107869118e-15` / `0x273c0000`; oracle `0.0` / `0x00000000`
- Actual-AEX complete PF32 frame: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
- Compared frame bytes: `33,177,600`
- Reconstructed final sampler differing bytes: `144,584`
- Production typed PF32 differing bytes: `10,047,226`
- Universal build: `x86_64 arm64`
- Production plug-in binary remains unchanged by the test-only seam: `7e794ee6c8eb8f16c0a8081eaede5cdf9973d7b7ebc16047047f75ae78d6fee5`

PF16 uses the binary-grounded `1/32768` reader and multiply-by-`32768`
truncate writer. PF32 reads and writes native floats directly.

The PF32-only `OLM_RADIALBLUR_TEST_SEAM` entrypoint copies the completed
`blurred.rgba` plane into a caller-owned buffer. It reported geometry
`1104x1800` and exactly `31,795,200` bytes. The full-byte mismatch proves the
current production residual already exists before inverse-coordinate sampling
and PF32 final writeback.

## Limit

This is not AE exact. No Mac AE or Windows process was used. Rotation and
unsupported deep-color feature combinations are still copied. The next proof
boundary is a test-only capture of pre-blur `polar.rgba`, separating
Cartesian-to-polar sampling from convolution and normalization.

Verification: `python3 tools/emulation/test_olmradialblur_typed_deep_render_20260718.py`
