# OLMDirectionalBlur ASM Facts

Status: address-level facts for the Windows AEX port. Treat `disasm` /
objdump evidence as primary and Ghidra decomp as navigation only.

## Render Scale / Strength Scale

Current CLI diagnostics often use `--strength-scale auto`, implemented as
`1 / comp.frame_rate` because it is a better current PNG fit than raw UI
Strength. That is a measurement hypothesis, not an asm-confirmed field.

Address facts from `FUN_180003c90`:

- `180003d39..180003d58`: computes a float ratio from two render-context
  integers:

```c
scale = (float)*(int *)(ctx + 0x11c) / (float)*(int *)(ctx + 0x120);
params[0x34] = scale;
```

- `180003d5d..180003dac`: multiplies the four distance/fade integer fields by
  that scale and truncates to int:

```c
front_blur_strength = (int)(front_blur_strength * scale); // +0x48
front_alpha_fade    = (int)(front_alpha_fade    * scale); // +0x4c
back_blur_strength  = (int)(back_blur_strength  * scale); // +0x50
back_alpha_fade     = (int)(back_alpha_fade     * scale); // +0x54
```

- The ratio is read from the AE/render context (`ctx + 0x11c` and
  `ctx + 0x120`), not from the manifest frame rate. It is likely a render
  scale/downsample ratio or similar host field. Do not treat the current
  `1/24` CLI setting as the AEX implementation without mapping these context
  fields.

Current implication:

- Existing references do not record the `ctx + 0x11c / ctx + 0x120` values.
- If the remaining DirectionalBlur residual starts depending mainly on this
  scale, request a targeted Windows reference/manifest addition for the render
  scale/downsample fields instead of overfitting the PNGs.

## Row Driver / Component Coefficients

`FUN_1800038d0` is the row driver. It loops rows from `param_1` to `param_2`
and pixels across `param_5` width.

Address facts:

- `1800039a0..180003a06`: before scatter, each pixel calls `FUN_180001000`
  with a component coefficient:

```c
component_coeff = powf(map[p].area / max_area, size_variation);
FUN_180001000(..., front_alpha_fade, ..., back_alpha_fade, width,
              component_coeff);
```

  The component map pointer is `params + 0x8118`; `max_area` is
  `params + 0x38`; `size_variation` is `params + 0x30`.

- `180003a32..180003a3f`: scatter is skipped when source alpha at
  `src_rgba[p].a` is exactly zero.
- `180003a45..180003ac5`: recomputes the same area/size-variation coefficient
  and optionally multiplies it by a noise/variation factor depending on
  `*(int *)(params + 0x20)`:
  - mode `2`: reads a per-pixel float map at `params + 0x80b0`
  - mode `3`: calls `FUN_180003370(params + 0x80c0, x, y, flag)`
- `180003ad5..180003b5b`: computes front sharp-tail attenuation using:

```c
tail = max(0, 1 - abs(row - map[p].center_y) * front_sharp_tail / map[p].half_height);
front_coeff = tail * component_coeff;
FUN_1800013e0(..., front_table=params+0x58,
              front_strength=params+0x48, front_coeff);
```

- `180003b60..180003bde`: computes the same shape for the back pass using
  `back_sharp_tail`, table `params+0x4068`, and strength `params+0x50`.

Current implication:

- The CLI's `rotated-map` family correctly treats the component coefficient as
  scatter distance / table-index modulation rather than direct alpha
  attenuation.
- The current `direct` path is numerically useful but not structurally faithful
  to this row driver. Use it as a measurement baseline only.

## Scatter Helper

`FUN_1800013e0` is the one-sided row scatter helper.

Address/decomp facts:

- It reads source RGB from `param_4` and source alpha/validity from `param_7`.
- It multiplies the effective span by `param_11`:

```c
span = (int)(span * param_11);
```

- If `param_11 > 0`, the weight table index is scaled by `1 / param_11`:

```c
table_index = (int)(offset / param_11);
```

- RGB accumulates into `param_5.rgb`, denominator/weight into `param_6`, and
  output alpha is the max contribution in `param_5.a`.

Current implication:

- A simple alpha-sum final output is not the AEX shape; final alpha should stay
  max-like unless a later asm pass proves otherwise.
- Remaining error is more likely in the exact rotate/validity/input-buffer
  setup and render-scale mapping than in replacing max alpha with sum alpha.

## Rowdriver Prepass Probe

2026-06-05 diagnostic:

- Added CLI algorithm `--algorithm rotated-rowdriver-prepass` in
  `cli/OLMDirectionalBlur/main.cpp`.
- It keeps the current rotated scaffold but feeds the scatter source through a
  `FUN_180001000`-shaped prepass:
  - zero alpha clears source alpha/source RGB;
  - component coefficient comes from
    `pow(component_area / max_area, size_variation)`;
  - Front/Back Alpha Fade spans are multiplied by that coefficient;
  - weight table index uses `int(distance / coefficient)`;
  - source RGB is premultiplied by the derived prepass alpha.
- Current reference results:
  - `case_0001`: `max=255 mean=4.7505 nz=82877/518400`
  - `case_0005`: `max=254 mean=1.3802 nz=48065/518400`
- This matches the already-negative `rotated-alpha` / `rotated-aex` pattern
  rather than improving `rotated` or `rotated-front-strength-preserve-alpha`.

Interpretation:

- AEX-shaped `FUN_180001000` prepass alone is not the missing DirectionalBlur
  piece for the current opaque front-only refs.
- Keep this as negative diagnostic evidence. The next useful target is the
  exact caller buffer choreography around `memcpy(_Dst,_Src)`,
  `param_6[0x1010]` denominator initialization, and the final
  `FUN_180001ec0` rotate-back source/destination pairing.
