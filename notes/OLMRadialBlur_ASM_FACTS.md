# OLMRadialBlur ASM Facts

Scope: read-only sampler/writeback audit for Rotation polar buffers. Sources:
`notes/OLMRadialBlur_RE.md`, `decomp/OLMRadialBlur.aex.c.txt`,
`disasm/OLMRadialBlur.aex.asm.txt`, and current
`cli/OLMRadialBlur/main.cpp`. No implementation claims beyond the facts below.

## Sampler Helpers

- `FUN_180001270`: non-repeat RGBA polar sampler. It clears the four-float
  destination, accepts coordinates only when `-2 < int(x) < width` and
  `-2 < int(y) < height`, accumulates only in-bounds bilinear taps, weights RGB
  by tap alpha, then normalizes RGB by accumulated alpha. It returns `1` only
  when accumulated alpha is nonzero; otherwise returns `0`. It writes output
  alpha as `alpha_sum / geometric_weight_sum`.
- `FUN_180001520`: repeat-border RGBA polar sampler. It clears the destination,
  clamps the four tap coordinates to image edges, performs the same alpha
  weighted RGB normalization as `FUN_180001270`, and returns a validity byte
  based on the original un-clamped integer coordinate window
  `-2 < int(x) < width` and `-2 < int(y) < height`.
- `FUN_180001800`: non-repeat scalar sampler. It clears one float destination,
  accepts the same loose coordinate window as `FUN_180001270`, accumulates only
  in-bounds bilinear taps, and divides by the geometric weight sum when nonzero.
  It has no return value.
- `FUN_180001950`: repeat-border scalar sampler. It clears one float
  destination, clamps tap coordinates to image edges, and writes plain bilinear
  scalar output. It has no return value.

## Rotation Caller Plane Map

`FUN_180004640` selects the helper pair by Repeat Border: repeat off uses
`FUN_180001270` / `FUN_180001800`; repeat on uses `FUN_180001520` /
`FUN_180001950` (`decomp` around `2064..2072`, asm call through
`[RSI+0x58]`/`[RSI+0x60]`).

- `+0x38`: polar RGBA input. Filled by the RGBA sampler from source layer
  `param_2[0x13]` / asm `R14+0x98`; the sampler return byte is stored in a
  separate valid-byte plane at `180004b19`.
- `+0x40`: scalar span/gate plane for `FUN_1800024c0`. Filled by the scalar
  sampler from layer `param_2[0x12]` / asm `R14+0x90`.
- `+0x48`: prepass alpha plane. It is not filled during initial sampling.
  `FUN_180002780` writes it, and `FUN_1800024c0` later reads it.
- `+0x50`: prepass factor plane. If Size Variation enable flag `R14+0x44` is
  clear, the caller writes literal `1.0f`; otherwise it samples layer
  `param_2[0x11]` / asm `R14+0x88` through the scalar sampler.

Decompiler pointer-index aliases: `+0xe == +0x38`, `+0x10 == +0x40`,
`+0x12 == +0x48`, and `+0x14 == +0x50`.

## Size-Variation / Scatter-Span Source (2026-06-15, RESOLVED)

The two scalar source-space layers feeding `+0x40` and `+0x50` are built before
`FUN_180004640` runs, in the layer-allocation/fill function (decomp
`~3160..3398`):

- `param_5[0x21]` is the per-pixel **size map**. When the Size Variation gate
  `+0x44 == 0`, it is filled with constant `1.0f` (`FUN_180006500`, decomp
  3270-3273). When enabled, `FUN_180008930` builds it from a connected-component
  /run-length distance transform over the alpha mask `mask[i] = (src.alpha > 0)`
  (decomp 3284-3286), and `+0x4c` stores the map maximum for normalization.
- `param_5[0x11]` (= `param_2[0x11]`, the `+0x50` **factor** plane in source
  space) is computed (decomp 3309-3324) as
  `size_factor[i] = (sizemap[i] / sizemap_max) * SV + (1.0 - SV)`,
  where `SV = +0x40_render_param = Size Variation * 0.01`. With `SV = 0` this is
  exactly `1.0` for every pixel.
- `param_5[0x12]` (= `param_2[0x12]`, the `+0x40` **scatter span/gate** plane in
  source space) is computed by `FUN_1800065c0` (decomp 2858-2887) as
  `span_gate[i] = (NV * noise[i] + (1.0 - NV)) * size_factor[i]`, where
  `NV = +0x3c_render_param = Noise Variation * 0.01`. With `NV = 0` this is
  exactly `size_factor[i]`; with both `NV = 0` and `SV = 0` it is exactly `1.0`.

`FUN_180001c90` reads `+0x40` as `param_10` and sets the effective scatter
length `effective_len = int(base_len * param_10)` (decomp 599). So the
size-variation map scales the per-cell inner/outer scatter length, and the
size factor / noise factor are NOT a final alpha multiply — they retune the
Gaussian span before the table is reindexed by `30000 / effective_len`.

Empirical confirmation from the 2026-06-15 sizevar references: for the fully
opaque `current_olm_cells` input, `sv000_edge000`, `sv050_edge000`, and
`sv100_edge000` outputs are **byte-identical**. This is consistent with the
formula: a fully opaque mask is a single region, so the normalized distance map
is (near-)uniform and `size_factor` is constant; a constant span scale that is
applied per cell and then re-normalized by the accumulated alpha-weight sum
cancels out, leaving the image unchanged. Size Variation therefore only has a
visible effect on inputs with non-trivial alpha structure (the `alpha_*`
references), where the distance transform is non-uniform.

## Prepass And Scatter Wiring

- `FUN_180002780` call site (`180004c31..180004c6a`) receives
  `param_2=+0x38`, `param_3=+0x48`, `param_4=+0x50`,
  `param_9=+0x3c940`, and `param_10=+0x3c948`.
- `FUN_1800024c0` call site (`180004cb1..180004cef`) receives
  `param_2=+0x38`, `param_3=+0x48`, `param_4=+0x40`, valid-byte plane,
  `param_10=+0x3c940`, and `param_11=+0x3c948`.
- Therefore the AEX sequence is:
  `prepass(+0x38, +0x48 out, +0x50 factor)`, then
  `scatter(+0x38, +0x48 prepass alpha, +0x40 span/gate)`.

## FUN_180002780 Edge Fade / Seed Facts

- Rotation setup scales Outer Edge Fade `+0x6c` into `param_1+0x3c930` and
  builds table `param_1+0x3a9f0`; it scales Inner Edge Fade `+0x70` into
  `param_1+0x3c934` and builds table `param_1+0x3b990`.
- For each cell, `FUN_180002780` reads polar RGBA from `+0x38`, factor from
  `+0x50`, and starts the gathered alpha from source alpha (`fVar32 =
  polar.a`) and weight sum `1.0`. That is the self seed.
- If source alpha is zero or factor is zero, it clears the prepass/scatter RGB
  accumulation output at `+0x3c940` for that cell to `0,0,0,0`.
- Otherwise it gathers neighboring alpha in the outer/backward angular
  direction using table `+0x3a9f0` for span `int(edge_fade_outer * factor)`,
  and in the inner/forward angular direction using table `+0x3b990` for span
  `int(edge_fade_inner * factor)`.
- After either branch, it writes the computed alpha to both the `+0x48`
  prepass alpha plane and the `+0x3c948` final/max-alpha plane. The nonzero
  branch also writes prepass output RGB as `computed_alpha * polar.rgb` and
  output alpha as `computed_alpha` into `+0x3c940`.

## FUN_1800024c0 Scatter Facts

- The scatter gate is `(valid byte != 0) && (+0x48 prepass alpha != 0) &&
  (+0x40 span/gate != 0)`.
- For each gated cell it calls `FUN_180001c90` outer first with direction
  `0`, then inner with direction `1`.
- Dynamic offset is radius-row dependent:
  `int((radius_count / 2 * offset_value) / current_row_index)` in decomp shape.
  Outer offset value comes from `param_1+0x28`; inner from `param_1+0x30`.
- The values passed into `FUN_180001c90` are prepass alpha (`+0x48`) plus
  source RGB from `+0x38` and scalar span/gate from `+0x40`.

## CLI Mirror Status

- The current C++ CLI has diagnostic mirrors for the AEX sampler
  (`sample_rgba_aex_alpha`), polar valid mode, prepass factor modes, seed modes,
  scatter span/param10 planes, and final alpha/RGB denominator modes.
- The CLI still contains diagnostic alternatives; do not treat those switches
  as settled AEX behavior. The settled asm facts are the caller plane ownership,
  helper selection, prepass writeback to `+0x48/+0x3c948`, and scatter gating
  through valid byte, `+0x48`, and `+0x40`.
