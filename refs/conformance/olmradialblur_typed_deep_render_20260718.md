# OLMRadialBlur typed deep render (2026-07-18)

Status: `known_red_preblur_postblur_and_internal_pf32_frame`

The Mac production source now executes typed Zoom processing for PF16 and
PF32 instead of copying the input unchanged. PF8 keeps its existing path.

## Evidence

- Actual-AEX checkpoint: `480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909`
- Pinned AEX: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- Checkpoint RIP: `0x180005c9f`, immediately before in-place normalization
- Actual-AEX pre-blur plane: `31,795,200` bytes, `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`
- Production pre-blur plane: `31,795,200` bytes, `8e245bccbda1a856df3e079d4b49d81af256c844acee6557a1375ebebad11530`
- Production pre-blur differing bytes: `327,417`
- First pre-blur difference: byte `4,192`, float word `1,048`, angle `0`, radius `262`, channel `R`
- First pre-blur values/bits: production `0.24313725531101227` / `0x3e78f8f9`; oracle `0.24313727021217346` / `0x3e78f8fa`
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
- Production plug-in binary remains unchanged from the committed typed-deep build: `7e794ee6c8eb8f16c0a8081eaede5cdf9973d7b7ebc16047047f75ae78d6fee5`

PF16 uses the binary-grounded `1/32768` reader and multiply-by-`32768`
truncate writer. PF32 reads and writes native floats directly.

The PF32-only `OLM_RADIALBLUR_TEST_SEAM` entrypoint copies both pre-blur
`polar.rgba` and post-blur `blurred.rgba` from one `RenderZoomTyped` run into
caller-owned buffers. Both report geometry `1104x1800` and exactly
`31,795,200` bytes.

The actual-AEX pre-blur oracle is not the normalized oracle. It is extracted
from `work+0x38` in the identity-validated merged checkpoint at RIP
`0x180005c9f`, before normalization overwrites that buffer in place. The test
re-extracts the checkpoint bytes and requires byte equality with the oracle
file before comparing production output.

The relatively narrow pre-blur residual becomes `13,953,051` differing bytes
after blur. The post-blur hash and difference count exactly reproduce the
earlier single-plane run. This proves that a residual exists before the worker,
but does not by itself prove the worker is wrong because its inputs already
differ.

## Limit

This is not AE exact. No Mac AE or Windows process was used. Rotation and
unsupported deep-color feature combinations are still copied. The next proof
boundary is to feed the actual-AEX pre-blur oracle into the Mac worker and
compare that result with the actual-AEX normalized plane. This separates the
sampling residual from worker/convolution behavior.

Verification: `python3 tools/emulation/test_olmradialblur_typed_deep_render_20260718.py`
