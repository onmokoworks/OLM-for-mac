# F52 geometry worker (qualification in progress)

F46 plus opt-in session arguments:

- `--downsample-x num/den`, `--downsample-y num/den` (positive, <=1)
- `--rowbytes-pad N` (0..256 extra bytes on input and output rows)
- `--extent-hint left,top,right,bottom` (sampled-world coordinates)
- `--request-rect left,top,right,bottom` (Smart output request)
- `--pixel-aspect num/den` (positive horizontal/vertical ratio)

CLI width/height are full-resolution layer dimensions. Input/output files are
packed ARGB at `ceil(full*num/den)` dimensions, with no host resampling or pixel
conversion. Row padding is allocated inside the worker and removed on output;
only allocation guards are immutable (row padding is not image data). Primary fixture layouts cannot be
combined with explicit padding/extent overrides. Rectangle requests remain
subject to the existing Classic route restriction. This does not implement
arbitrary output origins or expanded output allocation negotiated by PreRender.

SDK basis, in MAIN `Headers/AE_Effect.h`:

- 2923–2927: in_data width/height are full-resolution input-layer dimensions.
- 2937–2943: extent_hint is the visible input/output intersection.
- 2951–2961: layer dimensions adjust for downsampling; effects must scale scalar
  pixel distances; factors are rational and available at sequence setup.
- 3025–3027: downsample fields and pixel aspect h/v (NTSC D-1 example 0.9).
- 1541–1546: source-world extent_hint describes opaque pixels.

The ceiling rule is the requested host allocation policy; the cited comment
establishes the dimension distinction, not a particular integer rounding rule.

Build serially with `python3 tools/emulation/aexcompat_patches/build_F52.py`.
It verifies F46 source hashes, checks >=30% memory free, uses jobs=1, and removes
the build tree even on failure. `--register` adds the built worker to INDEX without
changing the default worker. Retained sources and binaries are in the cache.

The source-host `geometry.hpp` currently forwards **downsample only**. It wraps
host calls after the production source include and is inactive without the
per-invocation `OLM_F52_DOWNSAMPLE` environment variable. No plugin code changes.
`measure_F52.py` is a separate downsample qualification driver, not the requested
complete `--geometry realistic` sampler. It keeps original seed generation
unchanged, crops independently generated pixels to the sampled dimensions, and
scales point parameters. The full sampler and bundle-host geometry remain open.

## Static observations (original AEX)

Read-only disassemblies in MAIN `disasm/`:

- `OLMBlur.aex.asm.txt`, `0x1800022ee..0x180002315`: read downsample_x
  numerator at `PF_InData+0x11c`, denominator at `+0x120`; convert to float32,
  `DIVSS`, multiply radius with `MULSS`, then `CVTTSS2SI` (truncate toward zero).
  Other worker paths have matching reads at `0x18000377e`, `0x180004bf1`,
  `0x180005f67`, `0x180007347`, `0x180008717`.
- `OLMDirectionalBlur.aex.asm.txt`, `0x180003d39..0x180003dac`: the same
  float32 horizontal ratio multiplies four integer fields at offsets
  `0x48/0x4c/0x50/0x54`, each followed by `CVTTSS2SI`; the nearby float field at
  `+0x8110` is scaled without integer conversion (`0x180003db0`). Matching
  scale reads occur at `0x180004ac9` and `0x180005854`. The existing IR identifies
  the four integer fields as Front/Back strength/fade; that identification is
  inherited analysis, whereas the instructions and offsets above were checked.
- `OLMColorKey.aex.asm.txt`, `0x180013a30..0x180013ae9`: helper functions use
  double-precision **inverse** X/Y ratios to multiply pointed-to coordinates.
  Caller/radius interpretation is unconfirmed; do not infer a Blur-like radius
  rule from these helpers alone.

`validate_F52.py` compares 9-pixel Blur Amount / DirectionalBlur front strength
under 1/2, 1/3, 1/4, 1/8 against same sampled pixels at 1:1 and the corresponding
scaled control (float radius for Blur; truncated integer for DirectionalBlur).
These are bounded final-output observations, not a claim covering every radius,
route, parameter interaction or native AE.
