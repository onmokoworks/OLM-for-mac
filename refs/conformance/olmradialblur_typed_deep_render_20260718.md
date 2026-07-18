# OLMRadialBlur typed deep render (2026-07-18)

Status: `known_red_internal_pf32_frame`

The Mac production source now executes typed Zoom processing for PF16 and
PF32 instead of copying the input unchanged. PF8 keeps its existing path.

## Evidence

- Actual-AEX normalized polar plane: `31,795,200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
- Actual-AEX complete PF32 frame: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
- Compared frame bytes: `33,177,600`
- Reconstructed final sampler differing bytes: `144,584`
- Production typed PF32 differing bytes: `10,047,226`
- Universal build: `x86_64 arm64`

PF16 uses the binary-grounded `1/32768` reader and multiply-by-`32768`
truncate writer. PF32 reads and writes native floats directly.

## Limit

This is not AE exact. No Mac AE or Windows process was used. Rotation and
unsupported deep-color feature combinations are still copied. The next proof
boundary is the production normalized polar plane versus the captured
actual-AEX normalized polar plane, before any further final-sampler tuning.

Verification: `python3 tools/emulation/test_olmradialblur_typed_deep_render_20260718.py`
