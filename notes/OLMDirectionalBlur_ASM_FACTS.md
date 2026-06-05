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

2026-06-06 rotate-math diagnostic:

- `FUN_180001ec0` receives a float angle, uses `cosf` / `sinf`, and computes
  centers from integer `width / 2` and `height / 2`.
- Added C++ CLI algorithm `--algorithm rotated-aex-float-math` to apply those
  details to the current full A/B choreography.
- Current measurement is neutral against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4483`, `case_0005 mean=1.1703`.
- The remaining front-only residual is therefore not explained by double-vs-float
  trig or integer-center rounding in `FUN_180001ec0`. Keep looking at
  edge/validity semantics or row-driver scatter/source ownership.

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

2026-06-05 diagnostic:

- Added C++ CLI algorithm `--algorithm rotated-aex-choreo` to test the first
  part of this order: populate a padded A buffer and rotate A into B before the
  existing rotated scatter scaffold.
- Current measurements: `case_0001 max=254 mean=4.4483`; `case_0005 max=246
  mean=1.1703`.
- This is a partial positive signal: it does not affect the angle-0 case, but
  it improves the diagonal front-only case compared with the previous rotated
  and rotated-preserve-alpha probes.
