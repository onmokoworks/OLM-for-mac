# OLM Color Key — ASM facts

Live Ghidra (program = OLMColorKey, OLMColorKey.aex). Confirmed 2026-06-14.

## Color space dispatch and per-space comparator

`Color Space` popup string `RGB|HSV|Lab76|Lab94|YUV|YCrCb` -> 1-based indices:
1=RGB, 2=HSV, 3=Lab76, 4=Lab94, 5=YUV, 6=YCrCb.

The 8-bit keyer callback `FUN_1800029d0` reads the color space at `param_1+0x30`
and, per space, (a) converts sample+key into the space and (b) selects a
per-space comparator function (`pcVar18`). The converted sample/key are then
compared by that comparator. The comparator embeds the distance metric and the
per-channel `comp_scale` normalizers.

| space | convert fn | comparator fn |
| --- | --- | --- |
| 1 RGB   | none (identity)        | `0x180004190` (label, inside the keyer/jumptable) |
| 2 HSV   | `FUN_180009e10`        | `FUN_180004290` |
| 3 Lab76 | `FUN_180009f50`        | `0x1800043a0` |
| 4 Lab94 | `FUN_180009f50` (SAME as Lab76) | `FUN_180004510` |
| 5 YUV   | inline BT.601 matrix in keyer | `0x180004850` |
| 6 YCrCb | `FUN_18000a190`        | `0x180004910` |

Key point: **Lab76 and Lab94 use the same RGB->Lab conversion** (`FUN_180009f50`);
they differ ONLY in the comparator (CIE76 vs CIE94 distance). YUV converts with
an inline 3x3 matrix in the keyer; YCrCb converts via `FUN_18000a190`.

## Comparator signature and formula

`bool cmp(float *sample, float *key, float *comp_thresh, float *comp_scale,
          float global_eps, char per_component)`

- `comp_thresh` = per-channel Threshold(R,H,L,Y,Y)/(G,S,a,U,Cr)/(B,V,b,V,Cb)
- `comp_scale` = per-channel normalizer for the space (Lab76: 151.30099,
  264.36700, 295.573 — already in the CLI; other spaces have their own)
- `global_eps` = the 8-bit half-step (`0.5/255`)
- `per_component` = Per Component flag

HSV comparator `FUN_180004290`, confirmed:
- non-per-component = **EUCLIDEAN**:
  `sqrt(sum (s-k)^2) <= sqrt(sum comp_scale^2) * (global_eps + comp_thresh[0])`
- per-component = per-channel box with **hue wrap on channel 0**:
  `if (key[0] < sample[0]) key[0] += 1.0;` then
  `(key[0]-sample[0]) <= comp_thresh[0]*comp_scale[0] + eps` and
  `|key[c]-sample[c]| <= comp_thresh[c]*comp_scale[c] + eps` for c=1,2.
  (`DAT_18001f760 = 0x7FFFFFFF` is the fabs mask; `DAT_18001f6a4 = 1.0`.)

IMPLICATION for the CLI: `cli/OLMColorKey/main.cpp` currently uses ONE unified
comparator (per-component box, or non-per-component mean-of-abs/comp_scale). That
mean-of-abs happens to match RGB and Lab76 on the tested cases (Lab76 comparator
`0x1800043a0` must be mean-based), but it is NOT general:
- HSV needs Euclidean distance + hue wrap (above).
- Lab94 needs the CIE94 comparator `FUN_180004510` (decompile before porting).
- YUV / YCrCb need their comparators `0x180004850` / `0x180004910`.
So faithful color-space support requires per-space comparators in the CLI, not a
single shared distance. See [[port-correctness-bar-bytematch]].

## Converters (RGB -> space), DAT_ constants

- `FUN_180009f50` = RGB->Lab (Lab76 & Lab94). Matches CLI `rgb_to_plugin_lab76`.
  Uses `DAT_18001f638 = 0x3C1118C2 ~ 0.008856` (Lab epsilon),
  `DAT_18001f678 = 0x3EAAAA3B ~ 1/3` (powf exponent),
  `DAT_18001f6f0 ~ 7.787`, scale `*116-16`, `*500`, `*200`.
- `FUN_180009e10` = RGB->HSV. max/min of channels; hue via the standard
  6-sector formula; `fmod(hue, DAT_18001f730=360.0)`; output hue scaled by
  `DAT_18001f634`; S = (max-min)/max; V = max. (Resolve `DAT_18001f6fc/634/708/724`
  values before porting.)
- YUV (inline in keyer) uses BT.601-family luma `DAT_18001f670/698/650 ~
  0.299/0.587/0.114` plus chroma coeffs `f69c/68c/64c` and `f684/668/65c`.
- `FUN_18000a190` = RGB->YCrCb, matrix with `DAT_18001f688 = 0.5` and
  `f66c/694/654` (luma) etc.

## Confirmed comp_scale = {1,1,1} for all spaces (8-bit keyer)

In `FUN_1800029d0` the comparator's `comp_scale` arg (`&local_228`) is set to
`{1.0, 1.0, 1.0}` and never overridden per space. So the per-space distinction is
the COMPARATOR (metric + how threshold maps), NOT a comp_scale table. The CLI's
Lab76 `comp_scale = {151.30, 264.37, 295.57}` is therefore a CLI-side artifact
that happens to match the measured Lab76 cases; the binary normalizes inside the
Lab76 comparator instead. Leave Lab76 as-is (measured exact) but do not assume
comp_scale is a real per-space input for the remaining spaces.

## HSV — IMPLEMENTED and exact(0) (2026-06-14)

Confirmed by measurement (`ck_hsv_nonblack_remove_red` software: max=0). The
standard HSV converter + Euclidean comparator with comp_scale=1 is correct:
- convert: 6-sector hue in degrees (coeff 60, offsets 120/240), `fmod 360`,
  normalize `/360` to [0,1]; S=(max-min)/max; V=max. (constants are mathematically
  forced by the confirmed structure + `DAT_18001f730=360`, `DAT_18001f6a4=1.0`;
  verified exact by measurement.)
- non-per-component: `sqrt(sum (cmp-key)^2) <= sqrt(3) * (eps8 + threshold)`,
  eps8 = 0.5/255.
- per-component: hue wrap `if (cmp_h < key_h) cmp_h += 1.0`, then
  `(cmp_h - key_h) <= eps8 + thresh_h` and `|cmp_c - key_c| <= eps8 + thresh_c`.
Implemented in `cli/OLMColorKey/main.cpp` as a `color_space==2` branch; RGB/Lab76
unchanged (still exact), edge-blur transparent rgb still max=8 (separate issue).

## ALL 6 color spaces implemented and exact(0) (2026-06-14)

Measured 9/9 returned color-space cases exact(0) (software). Constants read
directly from `aex/.../2025/OLMColorKey.aex` `.rdata` (PE parse), comparators
disassembled with capstone (they are jumptable targets Ghidra did not recover as
functions, so decompile-by-name/address fails; raw-disassemble instead).

- Lab94 (space 4): converter = `FUN_180009f50` (same as Lab76). Comparator
  `FUN_180004510` = CIE94-style: `Cmean = sqrt(C1*C2)`, hue `atan2(b,a)*180/pi +
  180 mod 360`, `dC=(C2-C1)/(1+0.045*Cmean)`, `dH=(h2-h1)/(1+0.015*Cmean)`,
  `dist=sqrt(dL^2+dC^2+dH^2) <= (float)((double)(eps+thresh)*352.978)`.
  Per-component = box `|d| <= (eps+thresh[c])*scale[c]`, scale={151.30,264.37,295.57}.
- YUV (space 5): inline matrix Y=0.299R+0.587G+0.114B, U=0.436B-0.28886G-0.14713R,
  V=0.615R-0.51499G-0.10001B. Comparator `0x180004850`: ch0 (Y) `|d|<=t+eps`;
  ch1 (U) normalized `f(u)=(float)((double)u*1.146789+0.5)` then `|f(d)|<=t+eps`;
  **ch2 (V) NOT compared** (only a threshold>=0 no-op gate).
- YCrCb (space 6): converter `FUN_18000a190` -> {Y, Cb, Cr};
  Y=0.29891R+0.58661G+0.11448B, Cb=0.5B-0.16874R-0.33126G, Cr=0.5R-0.41869G-0.08131B.
  Comparator `0x180004910`: ch0 (Y) and ch1 (Cb) box `|d|<=t+eps`;
  **ch2 (Cr) NOT compared**. comp_scale={1,1,1}.

Both YUV and YCrCb intentionally key on luma + blue-difference chroma only and
ignore the red-difference chroma channel.

Remaining OLMColorKey work (separate from color spaces): the Replace feature
(`Enable Replace=1`, ~17 returned cases — CLI currently throws) and the edge-blur
transparent-rgb residual (`ck_edgeblur_transparent_rgb` max=8).
