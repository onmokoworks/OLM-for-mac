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

- It starts at offset 1 and uses `offset < span`; offset 0 is not scattered by
  this helper, and a truncated span of 1 skips the helper body.

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

Current implication:

- The final rotate-back source is the normalized second RGBA work buffer, not
  the just-cleared first buffer.
- The final rotate-back destination is the first RGBA work buffer, and
  `params + 0x8090` is repointed to that destination for the host-output pass.
- The CLI's older "copied-buffer / zero-denominator init" probes are still
  useful negative evidence, but the next faithful implementation pass should
  mirror this explicit A -> rotate into B -> copy B back to A -> row-driver
  writes/normalizes B -> clear A -> rotate B back into A -> output A order.

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

2026-06-06 truncated-span diagnostic:

- Added `rotated-aex-truncated-span` to test the exact `FUN_1800013e0` gate:
  `effective_span = int(strength * coeff)`, then process offsets
  `1..effective_span-1`.
- Measurement is mixed/minor against `rotated-aex-full-choreo`:
  `case_0001 mean=4.4467` (tiny improvement), `case_0005 mean=1.1749`
  (worse). This confirms the integer span boundary is worth keeping in the IR,
  but it is not the dominant remaining residual on current refs.

2026-06-05 diagnostic:

- Added C++ CLI algorithm `--algorithm rotated-aex-choreo` to test the first
  part of this order: populate a padded A buffer and rotate A into B before the
  existing rotated scatter scaffold.
- Current measurements: `case_0001 max=254 mean=4.4483`; `case_0005 max=246
  mean=1.1703`.
- This is a partial positive signal: it does not affect the angle-0 case, but
  it improves the diagonal front-only case compared with the previous rotated
  and rotated-preserve-alpha probes.
