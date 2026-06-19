# OLMDirectionalBlur ASM Facts

Status: address-level facts for the Windows AEX port. Treat `disasm` /
objdump evidence as primary and Ghidra decomp as navigation only.

## Render Scale / Strength Scale

Current CLI diagnostics use `--strength-scale auto` to read recorded
`ctx_render_scale` / `ctx_0x11c / ctx_0x120` values when present, falling back
to `1.0`. The older `1 / comp.frame_rate` setting was a measurement hypothesis
and is now only available as an explicit frame-rate diagnostic.

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

- The ratio is read from `PF_InData.downsample_x.num` and
  `PF_InData.downsample_x.den`. Local AE SDK `offsetof` confirms
  `downsample_x.num == 0x11c` and `downsample_x.den == 0x120`, and Mac OLMBlur
  uses the same `in_data->downsample_x.num / in_data->downsample_x.den` pattern
  for pixel-distance slider scaling.

Current implication:

- Existing references do not record the `ctx + 0x11c / ctx + 0x120` values.
- If the remaining DirectionalBlur residual starts depending mainly on this
  scale, request a targeted Windows reference/manifest addition for the render
  scale/downsample fields instead of overfitting the PNGs.
- 2026-06-12 returned `directionalblur_context_scale_20260606` refs show
  byte-identical `fr24` vs `fr30` outputs for sampled cases, so the previous
  CLI `--strength-scale auto = 1 / comp.frame_rate` proxy is contradicted by
  the new evidence. `auto` now means "use recorded `ctx_render_scale` /
  `ctx_0x11c / ctx_0x120` when present, otherwise fall back to `1.0`"; the old
  frame-rate diagnostic remains available only as `--strength-scale
  frame-rate`.
- The targeted request is
  `refs/reference_requests/directionalblur_context_scale_20260606.json`; it also
  asks for non-opaque alpha cases because the current tracked references cannot
  distinguish straight-vs-premultiplied source RGB or continuous alpha side
  channels.
- A 2026-06-06 full-choreography scale sweep confirms this is not closing as
  one scalar conversion. With `rotated-aex-full-choreo` on front-only cases
  `0001..0005`, the mean averages were:
  - `auto` / `1/24`: `3.7928`
  - `0.03`: `3.7731`
  - `0.06`: `3.8490`
  - `0.08`: `3.9352`
  `case_0005` alone prefers `0.08` (`mean=1.1540`), while cases `0001..0004`
  worsen to `mean=4.6304`. Keep `auto` for registered smoke stability; do not
  promote `0.03` as a fix without the actual context fields.

## Work-Buffer Padding / Host Offsets

Work-buffer dimensions and host populate/output offsets are set from the
diagonal-derived half span. For the 16bpc path:

```asm
180003e18  MULSS XMM0,dword ptr [0x18000b390] ; diagonal * -0.5
180003e20  CVTTSS2SI EAX,XMM0
180003e24  MOV R9D,0x2
180003e2a  SUB R9D,EAX                        ; half_span
180003e39  MOV dword ptr [RBX + 0x8098],ECX   ; y offset
180003e48  MOV dword ptr [RBX + 0x80a4],R8D   ; padded height
180003e5c  MOV dword ptr [RBX + 0x809c],R9D   ; x offset
180003e6c  MOV dword ptr [RBX + 0x80a0],EDX   ; padded width
```

This matches the CLI's `aex_pad_size` formula. The combined
`rotated-aex-pad-full-choreo` probe is neutral on current refs
(`case_0001 mean=4.4483`, `case_0005 mean=1.1703`), so the exact pad/offset
formula is not the dominant residual either.

## Host Populate / Output Callbacks

Direct `llvm-objdump` over `plugins_2025/OLMDirectionalBlur.aex` confirmed the
8bpc host callbacks that Ghidra's exported disassembly does not label as
standalone functions.

Populate callbacks:

- `0x1800068e0`: 16bpc populate. Reads PF pixel words and multiplies each
  channel by the float constant at `0x18000b33c`.
- `0x180006980`: 8bpc populate. Reads bytes from the PF pixel in A/R/G/B order:
  byte 1 -> work R, byte 2 -> work G, byte 3 -> work B, byte 0 -> work A. It
  divides channels by the float constant at `0x18000b388`.
- `0x180006a20`: 32bpc populate. Reads floats at byte offsets 4/8/12/0 into
  work R/G/B/A.
- All populate callbacks write to `params + 0x8078` and index the padded work
  buffer as:

```text
work_index = ((params+0x8098 + y) * *(int *)(params+0x80a0)
              + (params+0x809c + x)) * 4
```

Output callbacks:

- `0x180006b30`: 8bpc output. Reads from `params + 0x8090`, multiplies RGB by
  `BrightnessGain` at `params + 0x28`, clamps RGB to `1.0`, leaves alpha
  ungained, multiplies by the float constant at `0x18000b388`, and uses
  `CVTTSS2SI` truncation. It writes alpha to byte 0 and RGB to bytes 1/2/3.
- `0x180006a90`: 16bpc output has the same shape, using the constant at
  `0x18000b38c` and writing 16-bit channels.
- `0x180006bd0`: 32bpc output multiplies/clamps RGB, leaves alpha as the work
  alpha, and writes floats.
- Output uses the same padded index formula with `0x8098`, `0x809c`, and
  `0x80a0`.

Current implication:

- The CLI's centered padded copy/crop and `rotated-aex-trunc-output` diagnostic
  match these host callback facts closely.
- The remaining front-only residual is less likely to come from host
  input/output channel order, centered offsets, or output rounding. Continue at
  render-context scale mapping or finer `FUN_1800013e0` source/denominator
  ownership.

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

## Component Map Builder

`FUN_1800028e0` builds the `params + 0x8118` per-pixel component map from the
rotated valid mask. A 2026-06-06 asm/decomp pass confirmed the high-level shape:

- The helper first scans each row into horizontal non-zero runs. Each run stores
  row, start x, end x, and run length.
- Adjacent rows are merged only when their x ranges overlap inclusively
  (`FUN_180002250`). This is equivalent to 4-connected components for the
  binary valid mask, not 8-connected diagonal merging.
- For each merged component, the area is the sum of run lengths.
- The vertical minimum and maximum are tracked from the run row values.
- `center_y` is integer floor midpoint for positive coordinates:
  `(min_y + max_y) / 2`.
- `half_height` is `max_y - center_y`.
- Every pixel in every run receives four floats:
  component area, min_y, center_y, and half_height. The caller stores the
  maximum component area in `params + 0x38`.

Current implication:

- `cli/OLMDirectionalBlur/main.cpp`'s 4-neighbor component-map approximation is
  consistent with the AEX run-merging connectivity and center/span arithmetic.
- The remaining front-only residual is less likely to be a simple 4-vs-8
  connectivity bug or midpoint rounding issue. Prefer the next asm-first pass
  on exact rotate/validity semantics, scatter source/denominator ownership, or
  render-context scale mapping.

2026-06-06 half-height diagnostic:

- Added C++ CLI algorithm `--algorithm rotated-aex-halfheight`.
- It keeps the current full A/B choreography but removes the CLI's safety clamp
  on component `half_height`, leaving `half_height = max_y - center_y` exactly
  as recorded above.
- Current measurement is neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- This makes the component half-height clamp another non-leading suspect for
  the tracked front-only refs.

## Scatter Helper

`FUN_1800013e0` is the one-sided row scatter helper.

Address/decomp facts:

- It reads source RGB from `param_4` and source alpha/validity from `param_7`.
- Register-level mapping from `disasm/OLMDirectionalBlur.aex.asm.txt`
  `18000142b..18000144a`:
  - `XMM4 = param_4[p].r`
  - `XMM5 = param_4[p].g`
  - `XMM6 = param_4[p].b`
  - `XMM7 = param_7[p]`
  These are loaded once for the current source pixel before the scatter loop.
- It multiplies the effective span by `param_11`:

```c
span = (int)(span * param_11);
```

- It starts at offset 1 and uses `offset < span`; offset 0 is not scattered by
  this helper, and a truncated span of 1 skips the helper body.

- If `param_11 > 0`, the weight table index is scaled by `1 / param_11`:

```c
table_index = (int)(offset / param_11);
```

- RGB accumulates into `param_5.rgb`, denominator/weight into `param_6`, and
  output alpha is the max contribution in `param_5.a`.
- The per-offset contribution is:

```text
contribution = param_7[source_p] * table[int(offset / param_11)]
param_5[dst].rgb += param_4[source_p].rgb * contribution
param_6[dst]     += contribution
param_5[dst].a    = max(param_5[dst].a, contribution)
```

  This is visible in the repeated block at `180001550..1800015cc`: `XMM2` is
  initialized from `XMM7`, multiplied by `[weight_table + index*4]`, then
  multiplied by `XMM4/XMM5/XMM6` for RGB, added directly to the denominator
  buffer, and maxed into output alpha.
- The front call from `FUN_1800038d0` passes `param_3 = 1`, which makes the
  helper step toward lower x indices inside the rotated work buffer. Do not
  translate this helper-local direction directly into the CLI `sample-sign`
  without the surrounding rotate/callback coordinate convention.

Caller mapping from `FUN_1800038d0`:

- First/front call at `180003ad5..180003b5b`:
  - `param_3 = 1`
  - `param_4 = lVar2 = *param_3` (source A buffer)
  - `param_5 = lVar1 = *param_4` (destination B buffer)
  - `param_6 = *(params+0x8080)` denominator
  - `param_7 = *(params+0x8088)` alpha_or_valid
  - `param_8 = params+0x58` front weight table
  - `param_9 = *(params+0x48)` front strength
  - `param_11 = front_tail * component/noise coeff`
- Second/back call at `180003b60..180003bde` is the same shape with
  `param_3 = 0`, `param_8 = params+0x4068`, and
  `param_9 = *(params+0x50)`.

`FUN_180001000` buffer ownership:

- `FUN_1800038d0` calls the prepass as:

```c
FUN_180001000(x, row_offset, lVar2, lVar1,
              *(params+0x8088), *(params+0x8080),
              front_fade_table, front_alpha_fade,
              back_fade_table, back_alpha_fade,
              width, component_coeff)
```

- Therefore:
  - `param_3 = lVar2` source A buffer
  - `param_4 = lVar1` destination B seed buffer
  - `param_5 = *(params+0x8088)` alpha_or_valid
  - `param_6 = *(params+0x8080)` denominator
- For zero source alpha, `180001042..18000105b` clears denominator,
  alpha_or_valid, and B RGBA for that pixel.
- For nonzero source alpha, `18000136a..1800013c5` writes:

```text
gathered_alpha = weighted neighboring source alpha / weight_sum
denom[p] = gathered_alpha
B[p].rgb = A[p].rgb * gathered_alpha
B[p].a = gathered_alpha
alpha_or_valid[p] = gathered_alpha
```

- Scatter does not read B as its source. `FUN_1800013e0` gets source RGB from
  `lVar2`/A and contribution alpha from `alpha_or_valid`.

Current implication:

- A simple alpha-sum final output is not the AEX shape; final alpha should stay
  max-like unless a later asm pass proves otherwise.
- Current CLI `source_rgb = raw_rgb * alpha; accum += source_rgb * weight` is
  algebraically equivalent to the helper's
  `A.rgb * alpha_or_valid * weight` as long as CLI `alpha` is the same
  `alpha_or_valid` produced by the prepass. It is an implementation
  representation difference, not evidence that scatter reads B as source.
  The 2026-06-06 straight-source-RGB probe only showed that current opaque refs
  cannot distinguish representations that differ by source alpha placement.
- Remaining error is more likely in exact rotate/input-buffer ownership,
  non-opaque source behavior, or render-scale/context mapping than in replacing
  max alpha with sum alpha.
- A 2026-06-06 sign check on the current AEX full-choreography probes keeps
  `--sample-sign 1` best despite the helper-local negative-x step:
  - `rotated-aex-full-choreo`: sign `1` gives
    `case_0001/0005 mean=4.4483/1.1703`; sign `-1` worsens to
    `4.4485/1.3013`.
  - `rotated-aex-truncated-span`: sign `1` gives `4.4467/1.1749`; sign `-1`
    worsens to `4.4469/1.2916`.
  - `rotated-aex-trunc-output`: sign `1` gives `4.4438/1.1736`; sign `-1`
    worsens to `4.4439/1.3048`.
  Keep the registered rotated AEX smokes on `--sample-sign 1`.

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
- Added companion `--algorithm rotated-rowdriver-prepass-init` to test the
  copied-buffer / zero-denominator style initialization already used by the
  older `rotated-aex-init` diagnostic. Results are also negative:
  - `case_0001`: `max=255 mean=4.7724 nz=82879/518400`
  - `case_0005`: `max=254 mean=1.3862 nz=47999/518400`

Interpretation:

- AEX-shaped `FUN_180001000` prepass alone is not the missing DirectionalBlur
  piece for the current opaque front-only refs.
- Pairing that prepass with the current copied-buffer initialization hypothesis
  is also negative.
- Keep this as negative diagnostic evidence. The next useful target is the
  exact caller buffer ownership around `_Dst`/`_Src`/`param_6[0x1010]` and
  the final `FUN_180001ec0` rotate-back source/destination pairing, not another
  simple prepass/init toggle.

## Rotated Buffer Ownership / Final Rotate-Back

Address facts from the main `FUN_180003c90` no-noise/front-only branch:

- `180003e79..180003f09`: allocates and locks the first rotated RGBA work
  buffer, then stores the locked pointer at `params + 0x8078`.

```asm
180003ee6  MOV RCX,RSI
180003ee9  CALL qword ptr [RAX + 0x8]
180003eec  MOV R15,RAX
180003f09  MOV qword ptr [RBX + 0x8078],R15
```

- `180003f20..180003f4b`: allocates and locks the second rotated RGBA work
  buffer, then stores it at `params + 0x8090`.

```asm
180003f37  MOV RSI,RAX
180003f3a  MOV qword ptr [RBP + -0x60],RAX
180003f4b  MOV qword ptr [RBX + 0x8090],RAX
```

- `180003f52..180003faa`: allocates the per-pixel accumulator/support buffers:
  `params + 0x8080`, `params + 0x8088`, and the component map at
  `params + 0x8118`.

```asm
180003f76  MOV qword ptr [RBX + 0x8080],RAX
180003faa  MOV qword ptr [RBX + 0x8088],RAX
180003fe1  MOV qword ptr [RBX + 0x8118],RAX
```

- `FUN_180001ec0` uses `RCX/param_1` as the source image and `RDX/param_2` as
  the destination image. In the helper body, `RDI = RCX` is read for bilinear
  samples and `RBP = RDX + 8` is advanced/written as the output pointer
  (`180001eda..180001efe`, `180002078..1800020d2`).

- `18000451c..180004529`: the first `FUN_180001ec0` call rotates the first
  RGBA work buffer into the second RGBA work buffer. The first buffer has just
  been populated by the `FUN_180006610(..., LAB_1800068e0, ...)` callback.

```asm
180004523  MOV RDX,RSI        ; destination = params+0x8090 work buffer
180004526  MOV RCX,R15        ; source = params+0x8078 work buffer
180004529  CALL 0x180001ec0
```

- `180004575..18000457b`: immediately after that first rotate, the second work
  buffer is copied back into the first work buffer. The helper uses the normal
  Windows x64 `memcpy`-style argument order (`RCX` destination, `RDX` source).

```asm
180004575  MOV RDX,RSI        ; source = params+0x8090 work buffer
180004578  MOV RCX,R15        ; destination = params+0x8078 work buffer
18000457b  CALL 0x18000a646   ; memcpy-like helper
```

  This matches the decompiler's later `memcpy(_Dst, _Src, ...)`, but note that
  register names have been reused by then. The assembly-level relationship is:
  first rotate writes into the second locked RGBA work buffer, then that
  rotated image is copied back into the first locked RGBA work buffer before
  component-map and row-driver processing.

- `1800047f0..180004850`: after `FUN_1800038d0` row scatter, RGB in the second
  RGBA work buffer is divided by the per-pixel denominator at
  `params + 0x8080`; the first RGBA work buffer is cleared pixel-by-pixel.

```asm
1800047fb  MOV RAX,qword ptr [RBX + 0x8080]
180004819  MOVSS XMM0,dword ptr [RSI + RCX*0x4]
18000481e  DIVSS XMM0,XMM2
180004847  MOV dword ptr [R15 + RCX*0x4],EDI
18000484b  MOV qword ptr [R15 + RAX*0x4 + 0x4],RDI
180004850  MOV dword ptr [R15 + RAX*0x4 + 0xc],EDI
```

- `180004880..18000489d`: the final `FUN_180001ec0` call rotates the normalized
  second RGBA work buffer back into the cleared first RGBA work buffer, using
  the negated angle. The output callback then reads from `params + 0x8090`,
  which is repointed to the first work buffer after the final rotate.

```asm
180004880  MOVSS XMM0,dword ptr [RBX + 0x24]
180004885  XORPS XMM0,xmmword ptr [0x18000b3b0]
18000488c  MOVSS dword ptr [RSP + 0x20],XMM0
180004892  MOV RDX,R15        ; destination = params+0x8078 work buffer
180004895  MOV RCX,RSI        ; source = params+0x8090 work buffer
180004898  CALL 0x180001ec0
18000489d  MOV qword ptr [RBX + 0x8090],R15
```

- Direct `objdump` of the callback gap confirms the 8bpc output callback at
  `180006b30` / 16bpc at `180006a90` / float at `180006bd0`. The 8bpc callback
  reads from `params+0x8090`, indexes with `params+0x8098`/`0x809c` offsets and
  `params+0x80a0` stride, multiplies RGB by `BrightnessGain` at `params+0x28`,
  clamps RGB to `1.0`, leaves alpha un-gained, multiplies by `255`, then uses
  `CVTTSS2SI` truncation rather than round-to-nearest.

```asm
180006b30  MOV R9,qword ptr [RCX + 0x8090]
180006b37  MOVSS XMM5,dword ptr [RCX + 0x28]   ; BrightnessGain
180006b70  MULSS XMM5,dword ptr [R9 + RCX*4]   ; R * gain
180006b84  MINSS XMM5,XMM0                     ; clamp RGB <= 1
180006b88  MOVSS XMM3,dword ptr [R9 + RCX*4 + 0xc] ; alpha, no gain
180006ba0  MULSS XMM5,XMM1                     ; *255
180006ba8  CVTTSS2SI EAX,XMM5                  ; truncate
```

Current implication:

- The final rotate-back source is the normalized second RGBA work buffer, not
  the just-cleared first buffer.
- The final rotate-back destination is the first RGBA work buffer, and
  `params + 0x8090` is repointed to that destination for the host-output pass.
- The CLI's older "copied-buffer / zero-denominator init" probes are still
  useful negative evidence, but the next faithful implementation pass should
  mirror this explicit A -> rotate into B -> copy B back to A -> row-driver
  writes/normalizes B -> clear A -> rotate B back into A -> output A order.
- Final output quantization should be truncating for faithful AEX output, but a
  `rotated-aex-trunc-output` probe is mixed/minor on current refs
  (`case_0001 mean=4.4438`, `case_0005 mean=1.1736`), so quantization is not
  the dominant residual.
- A 2026-06-06 post-output shift sweep on the `rotated-aex-full-choreo`
  candidate tested `dx/dy = -1..1`. The unshifted output was best for both
  tracked cases (`case_0001 mean=4.4483`, `case_0005 mean=1.1703`); all one-pixel
  shifts worsened. This makes a simple final crop/output offset error unlikely.

2026-06-06 rotate-math diagnostic:

- `FUN_180001ec0` receives a float angle, uses `cosf` / `sinf`, and computes
  centers from integer `width / 2` and `height / 2`.
- Inside the helper, source coordinates are converted with `CVTTSS2SI`, then
  accepted only if `0 < ix < width - 1` and `0 < iy < height - 1`
  (`180002010..180002048`). Invalid samples skip the destination write path.
- Added C++ CLI algorithm `--algorithm rotated-aex-float-math` to apply those
  details to the current full A/B choreography.
- Current measurement is neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- The remaining front-only residual is therefore not explained by double-vs-float
  trig or integer-center rounding in `FUN_180001ec0`. Keep looking at
  edge/validity semantics or row-driver scatter/source ownership.

2026-06-06 preserve-invalid-input diagnostic:

- Added `rotated-aex-preserve-invalid-input`, which initializes the first
  rotate destination from the centered source canvas and preserves that value
  when the AEX-shaped rotate helper would skip an invalid input sample.
- Measurement is exactly neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- This makes first-rotate invalid-pixel destination ownership unlikely to be
  the leading residual on the tracked front-only references.

2026-06-06 row-initialization diagnostic:

- Added `rotated-aex-row-init-straight-zero`,
  `rotated-aex-row-init-premul-zero`, and `rotated-aex-row-init-zero`.
- These keep the full A/B choreography fixed and vary only the row-driver
  output/denominator initialization.
- Current measurements:
  - straight retained `B`, zero denom: `case_0001 mean=4.4702`,
    `case_0005 mean=1.1762`
  - premultiplied retained `B`, zero denom: `case_0001 mean=4.4702`,
    `case_0005 mean=1.1762`
  - zeroed `B` and zero denom: `case_0001 mean=4.5240`,
    `case_0005 mean=1.4931`
- This is negative evidence for a simple zero-denominator/B-clear fix. The next
  asm-first pass should map the exact `FUN_1800013e0` argument roles and
  `FUN_1800038d0` source-alpha/validity handling before more init toggles.

2026-06-06 full-prepass diagnostic:

- Added `rotated-aex-prepass-full-choreo`, combining padded A/B input/output
  choreography with the `FUN_180001000`-shaped center prepass.
- Current measurements are neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- This suggests the remaining front-only residual is not exposed by simply
  combining center prepass and A/B ownership in the current scaffold. Continue
  with exact `FUN_1800013e0` scatter boundary/table-index semantics or the
  host populate/output callbacks.

2026-06-06 exact row-driver diagnostic:

- Added `rotated-aex-exact-rowdriver`, combining the full padded A/B
  choreography, `FUN_180001000` prepass, and `FUN_1800013e0`-shaped
  source-driven scatter in one probe.
- Dedicated smoke:
  `refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_cli.py`.
- Measurements exactly match `rotated-aex-exact-scatter-helper`:
  `case_0001 mean=4.4392`, `case_0005 mean=1.1761`.
- `rotated-aex-full-choreo` remains `case_0001 mean=4.4483`,
  `case_0005 mean=1.1703`.
- This is negative evidence for simple row-driver integration as the missing
  residual. The next useful pass should map caller argument roles,
  render-context scale, or nonopaque-alpha Windows references rather than
  continuing image-only toggles.

2026-06-06 asm/decomp recheck of `FUN_180001000`:

- The prepass is not just a source-alpha replacement. For each row pixel it
  writes all three row-driver support outputs:
  - `param_6` / `params+0x8080`: denominator/alpha seed
  - `param_5` / `params+0x8088`: alpha-or-valid seed used later by scatter
  - `param_4` / current `B`: prepass output RGBA seed
- If the original rotated source alpha at `param_3[p].a` is exactly zero, the
  helper immediately clears `denom[p]`, `alpha_or_valid[p]`, and `B[p].rgba`.
- Otherwise it starts with center weight `1.0` and center alpha, gathers
  forward/backward source alpha using the Front/Back Alpha Fade tables, divides
  the alpha sum by total weight, and writes:

```text
denom[p] = gathered_alpha
alpha_or_valid[p] = gathered_alpha
B[p].rgb = gathered_alpha * A[p].rgb
B[p].a = gathered_alpha
```

- The Front/Back Alpha Fade spans are scaled by the component coefficient:
  `int(alpha_fade * coeff)`. The table index uses `int(offset / coeff)` when
  `coeff > 0`, otherwise `offset`.
- `FUN_1800038d0` calls this prepass before scatter for every pixel in the row.
  The later scatter skip still checks the original source alpha in `A[p].a`,
  while `FUN_1800013e0` reads its alpha/validity contribution from
  `params+0x8088`.
- Current CLI `rotated-aex-prepass-full-choreo` already models this
  prepass/seed shape closely enough to be neutral on the tracked refs, so a
  second isolated prepass toggle is unlikely to be useful. The next implementation
  pass should target exact `FUN_1800013e0` caller/source ownership or
  `FUN_180001ec0` edge/validity semantics.

2026-06-13 returned non-opaque alpha probes:

- The discriminating returned cases are `db_angle0_alpha_fade_hard_edges`,
  `db_diagonal_alpha_ramp`, `db_size_variation_component`, and
  `db_sharp_tail_component`.
- Existing large switches are negative or neutral on those cases:
  straight-source RGB (`mean avg=35.4938`), binary alpha (`36.7963`),
  rotate-back denom alpha (`31.6693`), row-init zero (`22.9762`), trunc output
  (`22.9332`), and truncated span (`22.8996`) all trail the current
  `rotated-aex-exact-rowdriver` baseline (`22.2983`).
- New exact-rowdriver rotate-sampler probes are also neutral: plain input
  (`22.3134`), plain output (`22.2984`), and plain input+output (`22.3135`).
  Therefore the AEX rotate helper is not explained by simply switching between
  alpha-weighted and plain bilinear sampling.
- For `db_diagonal_alpha_ramp`, the current exact-rowdriver candidate is
  generally too dark in RGB while alpha is too high. Keep the next asm pass on
  exact `FUN_1800013e0` denominator/RGB normalization or the B alpha/RGB state
  immediately before rotate-back.

2026-06-14 signed-error correction (measured, software fr24 ramp):

- Re-ran exact-rowdriver through `run_reference_test.py` on the 4 returned
  cases and measured signed candidate-minus-reference error on
  `db_diagonal_alpha_ramp`. The earlier "RGB too dark" note is wrong for this
  case: in premultiplied space the candidate is too BRIGHT (R +7.31, G +7.88,
  B +5.57) and alpha is too HIGH (+10.86). The candidate over-accumulates; it
  does not under-darken.
- This rules out the rotate-back re-darkening hypothesis (alpha-weighted output
  rotate would make RGB darker, the opposite of what is observed), consistent
  with the earlier neutral plain-output/plain-rotate probes.
- The ramp fills the whole frame (both ref and candidate alpha > 0 on all
  2,073,600 px; 0 extra-spread and 0 missing px). So the error is NOT a
  span/edge/spread problem. It is a smooth ~8.6% gain on alpha
  (mean 136.70 vs ref 125.84) with premul RGB tracking it proportionally.
- Localizes to the max-based alpha output (`accum_alpha = max(source_alpha *
  weight)`), which over-picks the brightest neighbor across the 240px front
  blur on a smooth ramp. On hard-edge cases (`db_angle0_alpha_fade_hard_edges`)
  the max is needed, which is why `rotateback-denom-alpha` (sum/average alpha)
  lost on the global mean while it would likely help this ramp. The alpha
  reconstruction in `FUN_1800013e0`/`FUN_180001000` is therefore probably NOT a
  pure per-pixel max; the next asm pass should pin down how the max tracker
  (`pfVar7`) feeds the final alpha vs the denominator accumulator (`pfVar9`),
  rather than tuning a single global alpha switch.

2026-06-14 live Ghidra confirmation (MCP, program = OLMDirectionalBlur):

- Live decompile of `FUN_1800013e0` is byte-identical to the text dump in
  `decomp/OLMDirectionalBlur.aex.c.txt` -> the dump is current.
- Constants resolved live:
  - `DAT_18000b1e8 = 0x3F800000 = 1.0f`. This is both the weight-index stride
    base (`fVar17 = 1.0 / param_11`) and the "full" value in the taper.
  - `DAT_18000b3a0 = 0x7FFFFFFF` = the fabs bitmask; `(uint)(x) & DAT_18000b3a0`
    is `fabsf(x)`.
- `FUN_1800013e0`'s only callers are two `FUN_1800038d0` call sites
  (`0x180003b5b`, `0x180003bde`). `FUN_1800038d0` is the per-row driver and it
  runs TWO passes per row over the columns:
  1. `FUN_180001000(...)` first = the alpha prepass/gather (front table
     `+0x3ed8` strength `+0x4c`, back table `+0x7ee8` strength `+0x54`,
     exponent `+0x30`, scale `+0x38`). This is what the CLI `rowdriver_prepass`
     models.
  2. then, per column, the front+back `FUN_1800013e0` scatter calls.
- Front/Back Alpha Fade is, confirmed, a PER-COLUMN LINEAR TAPER fed as
  `param_11`, not a gather-window size:

  ```
  fVar11 = powf(comp_value / scale(+0x38), exponent(+0x30)) * key_factor   // size-variation / key
  fVar12 = 1.0 - fabsf((float)row - center_x(+8)) * fade_rate / size_y(+0xc)
  fVar10 = max(0.0, fVar12)
  FUN_1800013e0(..., front_table(+0x58), front_strength(+0x48), width, fVar10 * fVar11)  // front, fade_rate(+0x40)
  FUN_1800013e0(..., back_table(+0x4068), back_strength(+0x50), width, <back fVar10> * fVar11)  // back, fade_rate(+0x44)
  ```

  The per-component reference column `center_x` and span `size_y` come from the
  `param_7+0x8118` table (`+8` = center, `+0xc` = size). `key_factor` is 1.0
  unless OLM key mode (`+0x20 == 2|3`) is active.
- Inside `FUN_1800013e0`, `param_11` does the two things noted earlier:
  `param_9 = (int)(param_9 * param_11)` (shortens scatter span) and
  `fVar17 = 1.0 / param_11` (steepens the weight-index stride). So a small
  per-column taper both shortens the streak and front-loads the weights.
- Conclusion: the CLI must apply Front Alpha Fade as this per-column taper on
  the SCATTER `coeff` (`fVar10 * fVar11`), feeding both the effective span and
  the weight stride, instead of a box-average of alpha over a gather window.
  This is the implement-now target; the returned refs are already on disk so it
  needs no new Windows capture.

2026-06-14 param-struct mapping confirmed (FUN_180004a20 SmartRender setup):

The context struct (param_6 here, == param_7 in FUN_1800038d0 / FUN_1800013e0)
offsets are now pinned:

- `+0x48` = front scatter strength (span); `+0x50` = back scatter strength.
  Both scaled by the downsample factor `+0x34 = downsample_x.num/den`.
- `+0x4c` = front gather count (alpha prepass); `+0x54` = back gather count.
  Also downsample-scaled.
- `+0x58` / `+0x4068` = front / back scatter weight tables, built by
  `FUN_180001830(table, strength)` (the gaussian/weight builder), lengths
  `+0x48` / `+0x50`.
- `+0x3ed8` / `+0x7ee8` = front / back gather weight tables, built with lengths
  `+0x4c` / `+0x54`.
- `+0x30` = size-variation exponent; `+0x38` = its scale denominator (used in
  `powf(area/scale, exponent)` = `fVar11`).
- `+0x40` = front fade rate; `+0x44` = back fade rate.

CORRECTED param->offset mapping (from `FUN_180006c50`, the param checkout). The
checkout index (2nd arg to the param suite call) maps to struct offsets, and the
front/back trios are unambiguous:

- idx 5 -> `+0x48` front scatter strength  = Front Blur Strength
- idx 6 -> `+0x4c` front gather count      = Front Alpha Fade
- idx 7 -> `+0x40` = param/100 taper rate  = Front Sharp Tail
- idx 10 -> `+0x50` back scatter strength  = Back Blur Strength
- idx 11 -> `+0x54` back gather count       = Back Alpha Fade
- idx 12 -> `+0x44` = param/100 taper rate  = Back Sharp Tail
- idx 3 -> `+0x30` = param/100              = Size Variation exponent

So the EARLIER 2026-06-14 claim that `+0x40 = Front Alpha Fade` is WRONG and is
retracted. The truth:

- Front Alpha Fade = `+0x4c` = the GATHER count fed to `FUN_180001000` (the
  alpha prepass). The CLI `rowdriver_prepass` already models this.
- Front Sharp Tail = `+0x40` = the per-column TAPER rate (`fade_rate/100`) fed as
  `param_11` into `FUN_1800013e0`. The CLI `tail_factor` is the right shape for
  this.

The short-circuit guard `if (+0x44 < eps && +0x40 < eps && +0x30 < eps) -> fill
alpha = 1.0` is therefore "no sharp tail and no size variation -> full alpha".
For `db_diagonal_alpha_ramp` (Front/Back Sharp Tail 0, Size Variation 0) the
guard is TRUE, so NO scatter taper applies. The taper was a red herring for this
case; a taper probe would have driven the wrong parameter.

`FUN_180001000` (alpha prepass) decompiled and compared to the CLI
`rowdriver_prepass` (main.cpp:1057-1084): they match structurally --
`front_count = int(front_gather * size_factor)`, weight index `int(i /
size_factor)`, weighted average `sum(w*alpha)/sum(w)` seeded with center weight
1.0, then premult RGB = avg_alpha * center_rgb and alpha-channel = avg_alpha.

So the `db_diagonal_alpha_ramp` alpha/RGB over-accumulation (+10.9 alpha, +7
premul RGB, measured) is NOT explained by the taper or by a simple prepass bug.
The remaining suspects, in priority order:
1. The final two-stage normalization in `FUN_180004a20`: after scatter, RGB is
   divided by a separate denominator buffer `param_6[0x1010]`, and there is a
   `FUN_180001ec0` edge/validity pass plus the `param_6[0x1023]` validity buffer
   (set to 1.0 under the guard). The CLI divides `accum_rgb / accum_sum` instead
   -- the denominator construction may differ.
2. The scatter alpha max semantics (`pfVar7 = max(.., fVar16)` -> channel 3) vs
   the CLI `accum_alpha = max(...)`, including how the prepass-seeded alpha
   interacts with the max.
Next asm pass: trace what fills `param_6[0x1010]` (the RGB denominator) and how
`FUN_180001ec0` / `param_6[0x1023]` feed the final alpha, then compare to the
CLI's `accum_sum` / `accum_alpha`.

2026-06-14 RESOLVED: ctx[0x1010] / final normalization traced, gaussian-table
divisor was the over-accumulation bug.

Buffer map pinned from the 8bpc SmartRender body (`FUN_180004a20`, the branch
using populate `LAB_180006980` / output `LAB_180006b30`). `param_6` is a
`undefined8*`, so the `0x100f..0x1012` indices ARE the `0x8078..0x8090` byte
offsets:

- `param_6[0x100f]` = byte `+0x8078` = `_Dst` = RGBA buffer A
  (`iVar17*iVar9*4` floats).
- `param_6[0x1010]` = byte `+0x8080` = the per-pixel RGB DENOMINATOR
  (`iVar17*iVar9` floats, one per pixel).
- `param_6[0x1011]` = byte `+0x8088` = `alpha_or_valid` (one float/pixel).
- `param_6[0x1012]` = byte `+0x8090` = `_Src` = RGBA buffer B.
- `param_6[0x1023]` = a 4x (RGBA-sized) validity buffer, zeroed then set to
  `0x3f800000` (1.0) for every element ONLY under the no-tail/no-size guard
  `(+0x44 < 1e-4 && +0x8 < 1e-4 && +0x6 < 1e-4)`. It is consumed by
  `FUN_1800028e0` (component map) as a validity mask, NOT by the RGB divide.

What fills `ctx[0x1010]` (denominator):
- prepass `FUN_180001000` SEEDS `denom[p] = gathered_avg_alpha = sum(w*a)/sum(w)`
  (weight_sum seeded 1.0 with center weight, alpha_sum seeded center alpha),
  i.e. the SAME value it writes to `B[p].a` and `alpha_or_valid[p]`.
- scatter `FUN_1800013e0` then ADDS, at each scattered destination,
  `denom[dst] += fVar16` where `fVar16 = alpha_or_valid[src] * weight_table[idx]`.
- The matching RGB accumulation is `B[dst].rgb += A[src].rgb * fVar16` (raw
  source RGB times the same `fVar16`), and `B[dst].a = max(B[dst].a, fVar16)`.

Exact final normalization (8bpc, `FUN_180004a20` lines ~2540-2565):
- for every pixel `i`: `fVar22 = denom[i]`; if `fVar22 > 0.0`,
  `B.rgb[i] /= fVar22` (channels 0/1/2 only). `B.a` (offset +0xc) is NOT divided.
  `A[i]` is cleared.
- then `FUN_180001ec0(_Src=B, _Dst=A, w, h, -angle)` rotates B back into A. The
  rotate helper writes `dst.alpha = bilinear corner-sum of source alpha` and
  `dst.rgb = (sum of corner_weight*corner_alpha*corner_rgb)/alpha_sum`, then
  output reads A. So final alpha is the alpha-weighted bilinear of B.a (the max
  channel), final RGB is the alpha-weighted bilinear of the denom-normalized B.

CLI comparison (`render_rotated`, exact-rowdriver path): the per-pixel math
already matches -- `accum_sum` seed = prepass avg alpha = decomp denom seed;
`accum_rgb` seed = avg_alpha * raw_rgb; scatter adds `source_rgb*alpha*weight`
to RGB and `alpha*weight` to `accum_sum`, with `accum_alpha = max`. Final
`rgb /= accum_sum`, alpha = max, rotate-back alpha-weighted. So the
normalization shape was NOT the bug.

THE BUG (binary-confirmed): the weight-table builder `FUN_180001830` divisor.
Direct PE read of `aex/.../OLMDirectionalBlur.aex` (image base 0x180000000,
RVA->file via section headers):

- `DAT_18000b1ec` @ RVA 0xb1ec = `0x40400000` = float **3.0** (the divisor).
- `DAT_18000b1e0` @ RVA 0xb1e0 = double **1e-05** (the additive epsilon).
- `DAT_18000b1e8` @ RVA 0xb1e8 = float 1.0.
- `DAT_18000b340` @ RVA 0xb340 = double 1e-04 (the no-tail/no-size guard eps).

`FUN_180001830(table, length)` therefore builds
`w[i] = expf(-(i*i) / (2*(length/3.0)^2 + 1e-5))`.

The CLI `gaussian_weights` used a divisor of **0.5** instead of 3.0, making the
denominator ~36x too large, flattening the gaussian and over-weighting far
samples. Because the same builder feeds BOTH the scatter table (length
`+0x48` = Front Blur Strength) and the gather/alpha-fade table (length
`+0x4c` = Front Alpha Fade), this inflated both the prepass average alpha and
the scattered RGB/alpha -> the measured uniform over-accumulation
(`db_diagonal_alpha_ramp`: alpha +6.9, premul RGB up to +0).

Fix applied in `cli/OLMDirectionalBlur/main.cpp` `gaussian_weights`: divisor
0.5 -> 3.0 with the `2*ratio^2 + 1e-5` denominator. Measured software fr24
(returned cases, `rotated-aex-exact-rowdriver`, mean_diff):

| case | before | after |
| --- | ---: | ---: |
| db_angle0_alpha_fade_hard_edges | 29.9884 | 27.3729 |
| db_diagonal_alpha_ramp | 16.3346 | 11.8807 |
| db_size_variation_component | 23.4683 | 21.0120 |
| db_sharp_tail_component | 16.5056 | 14.9299 |

Also strictly improves the existing GPU-rendered pairs (no regression):
`db_existing_case_0001_software_pair` 38.52 -> 37.34,
`db_existing_case_0005_software_pair` 20.91 -> 17.60.

Remaining gap (measured signed candidate-minus-reference, after fix):
- `db_diagonal_alpha_ramp` (cleanest, full-frame, angle -45): alpha +3.05,
  premul RGB R/G/B = -2.18 / -2.00 / +0.28. Mild remaining under-darkening +
  small alpha excess.
- `db_angle0_alpha_fade_hard_edges`: alpha now -11.38 (was +4.69), premul RGB
  -3.27/-2.17/+0.05 -- alpha now slightly UNDER on the hard-edge case.
- `db_size_variation_component`: alpha -9.82, premul RGB -6.20/-4.09/+0.61.
- `db_sharp_tail_component`: alpha -9.36, premul RGB -5.34/-3.54/-0.64.
The fade-hard-edge / size-var / sharp-tail cases now read alpha slightly LOW
while the ramp reads slightly HIGH. The max-vs-bilinear interaction at edges
(`FUN_180001ec0` rotate-back alpha = bilinear corner-sum of the max-tracked
B.a) is the most likely remaining residual; all of these are GPU Rendering=1
references (see GPU-rendering caveat). No further change made without a new
binary/decomp fact to avoid PNG-fitting.

2026-06-06 truncated-span diagnostic:

- Added `rotated-aex-truncated-span` to test the exact `FUN_1800013e0` gate:
  `effective_span = int(strength * coeff)`, then process offsets
  `1..effective_span-1`.
- Measurement is mixed/minor against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4467` (tiny improvement), `case_0005 mean=1.1749`
  (worse). This confirms the integer span boundary is worth keeping in the IR,
  but it is not the dominant remaining residual on current refs.

2026-06-06 component-center diagnostic:

- Added `rotated-aex-float-center` to test whether the component map's
  vertical center should be `(min_y + max_y) * 0.5` instead of integer-dividing
  `(min_y + max_y) / 2` in the current C++ scaffold.
- Measurement is neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- This makes component `center_y` rounding unlikely to be the front-only
  residual. The next useful target remains exact `FUN_1800013e0`
  scatter/source ownership or host edge/populate semantics.

2026-06-06 component-tail diagnostic:

- Added `rotated-aex-component-tail-only` to disable the older global
  valid-range Sharp Tail gate while keeping the component-map Sharp Tail used by
  `FUN_1800038d0`.
- Measurement is neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4484`, `case_0005 mean=1.1703`.
- This makes a simple global-tail plus component-tail double-application
  unlikely to be the leading residual on the tracked front-only refs.

2026-06-06 global-tail-only diagnostic:

- Added `rotated-aex-global-tail-only`, the inverse of
  `rotated-aex-component-tail-only`: it keeps the older global valid-range
  Sharp Tail gate but disables the component-map Sharp Tail factor.
- Measurement is neutral/mixed against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4490`, `case_0005 mean=1.1702`.
- Together with `rotated-aex-component-tail-only`, this makes simple
  global-tail vs component-tail selection unlikely to be the leading residual.

2026-06-06 no-tail diagnostic:

- Added `rotated-aex-no-tail`, which disables both the older global valid-range
  Sharp Tail gate and the component-map Sharp Tail factor.
- Measurement is neutral/negative against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4597`, `case_0005 mean=1.1702`.
- `FUN_1800038d0` uses `SUBSS` followed by `ANDPS XMM?, XMM10` for the vertical
  Sharp Tail distance, so the Ghidra-looking cast/mask expression is a float
  absolute-value operation. The CLI's `fabs` shape is correct.
- Together with the component/global-tail probes, Sharp Tail itself is unlikely
  to be the leading front-only residual on the tracked references.

2026-06-06 Size Variation scale audit:

- Parameter setup at `180006dd7..180006dea` divides the UI integer by
  `DAT_18000b384` before storing `params+0x30`.
- Direct PE read of `plugins_2025/OLMDirectionalBlur.aex` at RVA `0xb384`
  shows bytes `00 00 c8 42`, i.e. float `100.0`.
- Therefore the C++ CLI parse `size_variation / 100.0` is binary-confirmed and
  should not be treated as a tunable residual source.

2026-06-06 binary-alpha diagnostic:

- Added `rotated-aex-binary-alpha` to test whether `FUN_1800013e0`'s
  `param_7`/`alpha_or_valid` side-channel behaves like a binary source-validity
  mask instead of continuous alpha on the tracked front-only refs.
- This keeps the full A/B choreography and only replaces the scatter
  `source_alpha[p]` side-channel with `rotated_alpha > 0 ? 1 : 0`.
- Measurement is neutral/negative against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1753`.
- This makes a simple binary-validity interpretation of the scatter
  side-channel unlikely to explain the current front-only residual.

2026-06-06 straight-source-RGB diagnostic:

- Added `rotated-aex-straight-source-rgb` to test whether `FUN_1800013e0`
  reads `param_4` as straight RGB, with alpha contributing only through
  `param_7`/denominator accumulation.
- This keeps full A/B choreography and the existing scatter alpha side-channel,
  but stores straight rotated RGB in `source_rgb`.
- Measurement is exactly neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- Both tracked input PNGs have fully opaque source alpha (`min=max=255`), so
  this probe is not discriminating for straight-vs-premultiplied source RGB on
  the current reference cases.

2026-06-06 subagent argument audit:

- `FUN_1800013e0 @ 1800013e0` reads source RGB from `param_4`. The
  `18000142b..18000144a` region loads `param_4[p].r/g/b` alongside
  `param_7[p]`.
- `FUN_1800038d0 @ 1800038d0` passes front/back rows with
  `param_4 = *param_3` (A/source), `param_5 = *param_4` (B/destination),
  `param_6 = *(params+0x8080)` (denom), and
  `param_7 = *(params+0x8088)` (alpha_or_valid).
- The scatter contribution is `alpha_or_valid[source] *
  weight_table[int(offset / coeff)]`; `FUN_1800013e0` accumulates
  `B.rgb += A.rgb * contribution` and `denom += contribution`.
- `B.a` is max-like, not summed. The loop around `180001550..1800015cc`
  updates `param_5[dst].a = max(old, contribution)`.
- `FUN_180001000 @ 180001000` owns the prepass seed state for `denom[p]`,
  `alpha_or_valid[p]`, and `B[p].rgba`. Zero source alpha clears all of them
  around `180001042..18000105b`; nonzero source alpha writes
  `gathered_alpha` into `denom`, `B.a`, and `alpha_or_valid`, while
  `B.rgb = A.rgb * gathered_alpha` around `18000136a..1800013c5`.
- `FUN_1800038d0` decides scatter skip from the original `A[p].a` around
  `180003a32..180003a3f`.
- Current implication: the leading front-only residual is less likely this
  argument mapping and more likely rotate/input populate, edge/validity, or
  render-context scale. Opaque references still cannot separate straight and
  premultiplied source RGB.

2026-06-05 diagnostic:

- Added C++ CLI algorithm `--algorithm rotated-aex-choreo` to test the first
  part of this order: populate a padded A buffer and rotate A into B before the
  existing rotated scatter scaffold.
- Current measurements: `case_0001 max=254 mean=4.4483`; `case_0005 max=246
  mean=1.1703`.
- This is a partial positive signal: it does not affect the angle-0 case, but
  it improves the diagonal front-only case compared with the previous rotated
  and rotated-preserve-alpha probes.

2026-06-17 live Ghidra rotate-back audit:

- User opened `OLMDirectionalBlur.aex` in Ghidra MCP. Live decompile of
  `FUN_180001ec0 @ 180001ec0` confirms the existing IR/source-destination
  convention: `param_1` is source, `param_2` is destination, `param_3/4` are
  width/height, and `param_5` is the float angle. The helper uses `cosf/sinf`,
  integer-centered coordinates `(x - width/2, y - height/2)`, rejects samples
  unless `0 < int(src_x) < width-1` and `0 < int(src_y) < height-1`, writes
  destination alpha as the bilinear corner alpha sum, and writes RGB as
  alpha-weighted bilinear RGB divided by that alpha sum.
- Live decompile of `FUN_1800013e0 @ 1800013e0` also reconfirms the existing
  scatter IR: source RGB is read from `param_4`, destination RGBA from
  `param_5`, denominator from `param_6`, alpha/valid from `param_7`, and the
  contribution is `alpha_or_valid[src] * weight_table[int(offset / coeff)]`
  after `param_11` scales both the integer span and inverse table index.
- Re-ran the returned `directionalblur_context_scale_20260606` reference set to
  test final rotate-back alpha/output variants:

| algorithm | case0001 | case0005 | angle0 hard | diagonal ramp | size var | sharp tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exact-rowdriver | 37.3363 | 17.6044 | 27.3729 | 11.8807 | 21.0120 | 14.9299 |
| plain-output | 37.3363 | 17.6042 | 27.3729 | 11.8810 | 21.0120 | 14.9299 |
| rotateback-denom-alpha | 37.7719 | 17.8455 | 30.7026 | 43.1009 | 23.1246 | 17.7014 |

- `plain-output` is effectively identical to `exact-rowdriver`, so the
  remaining error is not explained by an extra output premultiply/unpremultiply
  mismatch after rotate-back.
- `rotateback-denom-alpha` is clearly worse, especially on
  `db_diagonal_alpha_ramp`, so replacing the max-tracked B alpha with the
  denominator/summed alpha is the wrong branch.
- Current implication: keep `FUN_180001ec0` alpha-weighted rotate-back and
  `FUN_1800013e0` max-alpha scatter semantics as pinned facts. The next useful
  DirectionalBlur asm target is not another rotate-back alpha variant; inspect
  the populate/edge/validity path around `FUN_1800028e0`, `param_6[0x1023]`,
  and the `FUN_1800038d0` caller conditions that decide component ranges and
  row scatter coverage.

2026-06-17 live Ghidra component-map guard audit:

- Live decompile of `FUN_180004a20 @ 180004a20` reconfirms the 8bpc caller
  around `FUN_1800028e0` and clarifies the guard:

  ```
  if (+0x44 < 1e-4 && +0x40 < 1e-4 && +0x30 < 1e-4) {
      fill param_6[0x1023] as float 1.0;
      *(float *)(param_6 + 7) = 1.0;  // max-area denominator used by powf
  } else {
      build a temporary byte mask from rotated _Dst.a > 0;
      FUN_1800028e0(aegp_context, byte_mask, param_6[0x1023], width, height);
      *(float *)(param_6 + 7) = component_max_area;
  }
  ```

- So `param_6[0x1023]` is not a direct alpha plane in the normal component-map
  path. In the non-guard path, `FUN_1800028e0` receives a compact `width*height`
  byte mask generated from rotated `_Dst.a > 0` and writes the float component
  table to `param_6[0x1023]` / `params+0x8118`.
- In the guard path (no front/back Sharp Tail and no Size Variation), the AEX
  does not call `FUN_1800028e0`; it only sets the max-area denominator to 1.0.
  This is safe because `powf(component_area / max_area, 0)` collapses to 1.0
  and the Sharp Tail rates are zero. The row prepass still clears pixels whose
  original rotated source alpha is zero.
- `FUN_1800028e0` itself matches the existing component-map IR: it scans
  horizontal nonzero byte runs, merges overlapping runs between adjacent rows,
  sums run lengths into area, stores integer-floor center
  `float((min_y + max_y) / 2)`, and stores `half_height = max_y - center_y`.
- Current implication: the CLI's BFS component map from `rotated.a > 0` is
  equivalent for the non-guard path, and guard-vs-map generation should not be
  the leading residual for the current no-tail/no-size refs. The remaining
  DirectionalBlur risk is more likely exact host-scale/padded populate,
  alpha-weighted input rotate validity, or a still-missed `FUN_180001000`
  prepass detail than component connectivity.

2026-06-17 returned context-scale smoke audit:

- A read-only subagent re-ran `directionalblur_context_scale_20260606` with the
  current `rotated-aex-exact-rowdriver` command. The collapsed unique metrics
  were identical across fr24/fr30 and software/CUDA rows:

| case | max | mean |
| --- | ---: | ---: |
| existing case 0001 | 210 | 37.3363 |
| existing case 0005 | 178 | 17.6044 |
| angle0 no tail/size | 215 | 26.4272 |
| angle0 small strength | 205 | 17.1166 |
| alpha fade hard edges | 254 | 27.3729 |
| diagonal alpha ramp | 238 | 11.8807 |
| size variation component | 255 | 21.0120 |
| sharp tail component | 255 | 14.9299 |

- The fr24/fr30 equality keeps frame-rate scaling contradicted; keep
  `ctx+0x11c/0x120` mapped to `PF_InData.downsample_x.num/den`.
- The non-opaque cases do not support promoting straight RGB, binary alpha,
  rotate-back denominator alpha, or plain rotate sampling. Keep the current
  facts: source RGB from A, continuous `alpha_or_valid` from `FUN_180001000`,
  separate RGB denominator, max-tracked B alpha in `FUN_1800013e0`, then
  alpha-weighted `FUN_180001ec0` rotate-back.
- Next smallest parent action: perform a narrow Ghidra/objdump audit of the
  remaining edge/populate path, specifically 8bpc host populate into padded A
  and the first `FUN_180001ec0` non-opaque alpha/RGB validity behavior before
  component-map and row-driver execution. Do not add another broad PNG toggle
  unless that audit yields one concrete binary-backed difference.
- No extra Windows references are needed yet. If this edge/populate audit
  matches the current IR, the next unblocker should be new binary evidence, not
  image-only fitting.

2026-06-17 parent local edge/populate audit:

- Local decomp/disasm of `FUN_180001ec0 @ 180001ec0` matches the live-Ghidra
  rotate facts above. The helper uses `CVTTSS2SI` truncation, requires strict
  interior samples (`0 < xi < width-1`, `0 < yi < height-1`), and only writes
  destination RGBA inside the valid branch. Invalid samples therefore leave the
  already-cleared destination unchanged rather than explicitly writing a color.
- The current `rotated-aex-exact-rowdriver` path already mirrors that for the
  first rotate: `rotated.rgba` is zero-initialized before sampling, the default
  path does not preserve invalid input samples, and
  `sample_bilinear_alpha_weighted` / `aex_rotate_sample_valid` use the same
  strict interior validity. This makes first-rotate invalid handling unlikely
  to be the leading residual.
- 8bpc SmartRender uses `FUN_180006700` / PF Iterate8 at the first populate
  call site (`180005259..18000528a`) with callback `LAB_180006980`; the wrapper
  resolves `"PF Iterate8 Suite"` and invokes the suite function. Earlier 16bpc
  paths use `FUN_180006610` / PF iterate16, so do not read the iterate16 wrapper
  as the 8bpc populate behavior.
- Next focus should move one step earlier: audit the `LAB_180006980` callback
  itself and the exact padded A write offsets / channel scaling it applies
  before `FUN_180001ec0(A, B, pad_w, pad_h, angle)`. Do not add another
  first-rotate validity toggle unless `LAB_180006980` contradicts this mapping.
- A read-only explorer independently reached the same conclusion: padded A
  populate call order, first-rotate source/destination, alpha-weighted
  `FUN_180001ec0`, copy-back, and component-validity generation are mirrored by
  the current AEX-rowdriver CLI. Minor evidence caveat: the checked-in exported
  disasm has the `LAB_180006980` call site but not a readable callback body, so
  exact 8bpc channel-order/scaling still needs callback-body objdump/Ghidra
  evidence before implementation changes.

2026-06-17 direct objdump callback-body audit:

- `/usr/bin/objdump` over `plugins_2025/OLMDirectionalBlur.aex` recovers the
  callback bodies omitted from the exported Ghidra disasm. `0x180006980`
  confirms the 8bpc populate mapping exactly: PF bytes `+1/+2/+3/+0` become
  work floats `R/G/B/A`, each divided by `255.0f` at `0x18000b388`, and written
  to `*(params+0x8078)` at:

  ```text
  ((*(int *)(params+0x8098) + y) * *(int *)(params+0x80a0)
   + *(int *)(params+0x809c) + x) * 4
  ```

- `0x180006b30` confirms the 8bpc output callback: read
  `*(params+0x8090)`, multiply RGB only by `BrightnessGain` at `params+0x28`,
  clamp RGB to `1.0`, leave alpha ungained, multiply by `255.0f`, truncate via
  `CVTTSS2SI`, and write PF bytes `A/R/G/B` to `+0/+1/+2/+3`.
- This closes the callback-body evidence gap. The current CLI's padded
  populate/output/truncation diagnostics already mirror these facts, so do not
  add another host callback toggle. Remaining DirectionalBlur work should move
  back to `FUN_180001000`, rowdriver scatter ownership, final normalization, or
  another concrete objdump-backed difference.

2026-06-17 parent rowdriver/final-normalization closeout:

- Read-only rowdriver/final-normalization audit reconfirmed the current IR:
  `FUN_180001000` seeds `denom`, `alpha_or_valid`, and `B` from the gathered
  alpha; `FUN_1800013e0` scatters source RGB from A, contribution alpha from
  `alpha_or_valid`, accumulates RGB/denom into B/denom, and max-tracks B alpha;
  final normalization divides B.rgb by denom before alpha-weighted rotate-back
  to A.
- One small mismatch was real in the CLI: final normalization was guarded by
  `denom > 1.0e-8f`, while `FUN_180004a20` uses a binary `denom > 0.0` branch.
  `cli/OLMDirectionalBlur/main.cpp` now uses `denom > 0.0f`.
- Re-running `directionalblur_context_scale_20260606` after that patch produced
  the same collapsed metrics:

| case | max | mean |
| --- | ---: | ---: |
| existing case 0001 | 210 | 37.3363 |
| existing case 0005 | 178 | 17.6044 |
| angle0 no tail/size | 215 | 26.4272 |
| angle0 small strength | 205 | 17.1166 |
| alpha fade hard edges | 254 | 27.3729 |
| diagonal alpha ramp | 238 | 11.8807 |
| size variation component | 255 | 21.0120 |
| sharp tail component | 255 | 14.9299 |

- Treat the `denom > 0.0f` patch as correctness cleanup, not a visible fix.
  The main residual is now past the broad alpha/RGB/host-callback/rowdriver
  toggles already tested. Prefer moving active Ghidra time to RadialBlur or
  KiraKira unless a new DirectionalBlur binary fact appears.

2026-06-18 consistency cleanup:

- The primary `rotated-aex-exact-rowdriver` path already used the binary
  `denom > 0.0f` final-normalization guard. A legacy/direct diagnostic path in
  `cli/OLMDirectionalBlur/main.cpp` still used `denom > 1.0e-8f`; this was
  changed to `denom > 0.0f` so all C++ diagnostic paths use the same
  AEX-backed branch condition. This is not expected to move the current
  rowdriver metrics; it removes a stale diagnostic mismatch.
