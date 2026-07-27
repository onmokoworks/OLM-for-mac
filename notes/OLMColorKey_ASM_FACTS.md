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

## Replace feature — IMPLEMENTED and exact(0) (2026-06-14)

Param-struct mapping confirmed from the runtime reader `FUN_18000a3d0` (the
function that populates the keyer ctx from AE params) and the registration
`FUN_180001000` (which assigns each param its 1-based index). The keyer ctx is a
packed struct, NOT the raw AE param block; `FUN_18000dbf0`/`d510`/`de90` copy each
AE param (by 1-based index) into a fixed ctx offset:

| ctx offset | AE param index | param name | reader |
| --- | --- | --- | --- |
| +0x24 | 1 | **Color Keep** | dbf0 (bool) |
| +0x25 | 4 | Premultiplied Color | dbf0 |
| +0x30 | 5 | Color Space | e050 |
| +0x38 | 0x15 | Number of Colors | dcd0 |
| +0x4d | 0x20b | **Enable Replace** | dbf0 (bool) |
| +0x74 + i*0x10 | 0x16+5i | Color N (ARGB float) | d510 |
| +0x524 + i | 0x20c+3i | Use Color N (bool) | dbf0 |
| +0x53d + i | 0x20d+3i | **Use Replace Color N** (bool) | dbf0 |
| +0x204 + i*0x10 | 0x20e+3i | **Replace Color N** (ARGB float) | d510 |
| +0x394/0x3f8/0x45c/0x4c0 +i*4 | 0x17+5i.. | Threshold N / per-comp | de90 |

KEY FACT (resolves the spec's open question): **ctx+0x24 IS Color Keep.** The
keyer tail (`@LAB_180003253` in `FUN_1800029d0`; identical in the 8-bit
`FUN_1800029d0` predecessor and the float keyer) applies the Replace output ONLY
when ALL of: `ctx+0x24 (Color Keep) != 0` && `ctx+0x53d+idx (Use Replace Color
idx) != 0` && `ctx+0x4d (Enable Replace) != 0` && `idx != -1`. So **Replace only
takes visible effect in Keep mode (Color Keep=1).** Verified against the
returned references; decoded-pixel details and measured status are below.

### 2026-06-17 Mac Replace parity slice

The C++ CLI already records the first matched key index and uses it for the
Replace tail. A read-only explorer re-ran the covered Replace/color-space set
and confirmed exact C++ evidence for the simple Replace cases:

- `ck_rgb_replace_red_with_blue`: exact
- `ck_rgb_keep_replace_red_with_blue`: exact
- `ck_lab76_replace_cyan_with_magenta`: exact
- `ck_rgb_two_keys_replace`: exact
- `ck_rgb_replace_edge_thin_dilate`: exact

The Mac plug-in was still missing this tail. `mac/OLMColorKey` now:

- checks out `Use Replace Color N` and `Replace Color N`;
- records the first matched key index per pixel;
- replaces RGB only when `Color Keep && Enable Replace && Use Replace Color[idx]`;
- leaves alpha untouched, matching the binary-backed `FUN_1800029d0` tail.

Build check:

```sh
scripts/setup_ae_sdk_links.sh >/dev/null
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Debug build
```

Result: build succeeded. Remaining ColorKey gaps are not this Replace tail:
Edge Thin erode and Edge Blur still need separate binary-backed work.
- `ck_rgb_replace_red_with_blue` (Color Keep=0): matched red -> TRANSPARENT, no
  blue. `ck_rgb_keep_replace_red_with_blue` (Color Keep=1): matched red -> blue.
- `ck_lab76_replace_*`, `ck_rgb_two_keys_replace`, `ck_rgb_replace_edge_thin_*`,
  `ck_edgeblur_replace_*` are all Color Keep=0 -> plain remove, replace ignored.

Replace output (8-bit), keyer tail, ARGB layout (`out[0]=A,1=R,2=G,3=B`):
  scale = FUN_180011790(ctx+0x20 bit-depth) = 255 for 8-bit;
  out R = (byte)(int)(255 * ReplaceColor[+0x208+idx*0x10]) (= R slot, base+4),
  out G = (byte)(int)(255 * ReplaceColor[+0x20c+idx*0x10]),
  out B = (byte)(int)(255 * ReplaceColor[+0x210+idx*0x10]);
  alpha untouched (matched -> keeps original alpha). Cast is truncating int.

CLI impl (`cli/OLMColorKey/main.cpp`): `KeyColor` gained `use_replace` +
`replace_rgb[3]` (parsed from "Use Replace Color N" / "Replace Color N"); the
match loop records the first matching color index per pixel (`matched_idx`); the
keep loop overwrites kept-pixel RGB with the replace color when
`color_keep && enable_replace && idx>=0 && colors[idx].use_replace`. The earlier
`throw "replace color is not implemented"` is removed.

Rust/Mac parity follow-up (2026-06-17): `rust/olmcolorkey_cli/src/main.rs` now
mirrors the same Replace tail and the exact C++ HSV/Lab94/YUV/YCrCb comparator
branches. It parses `Use Replace Color N` and `Replace Color N`, stores the first
matched key index, and overwrites RGB only under the same
`Color Keep && Enable Replace && Use Replace Color[idx]` gate. Mac
`OLMColorKey.cpp` now has the same converter/comparator dispatch and builds.

```sh
cargo check && cargo build
python3 refs/scripts/run_reference_test.py refs/win_references/olm_reference_return_windows_20260614/OLMColorKey --run-dir /tmp/olmcolorkey_rust_all_colors_probe_after_build --expected-effect 'OLM Color Key' --command '"rust/olmcolorkey_cli/target/debug/olmcolorkey_cli" --input "{input}" --params "{params}" --output "{output}"' --case-id ck_rgb_nonblack_remove_red --case-id ck_rgb_nonblack_keep_red --case-id ck_hsv_nonblack_remove_red --case-id ck_lab76_nonblack_remove_cyan --case-id ck_lab94_nonblack_remove_cyan --case-id ck_yuv_nonblack_remove_yellow --case-id ck_ycrcb_nonblack_remove_yellow --case-id ck_lab76_per_component_cyan --case-id ck_lab94_per_component_cyan --case-id ck_rgb_replace_red_with_blue --case-id ck_rgb_keep_replace_red_with_blue --case-id ck_rgb_two_keys_replace --max-diff 0 --mean-diff 0 --nonzero-px-percent 0
scripts/setup_ae_sdk_links.sh >/dev/null
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -configuration Debug build
```

Result: Rust returned exact(0) for all 24 checked software/CUDA frames covering
RGB, HSV, Lab76, Lab94, YUV, YCrCb, Lab per-component, and RGB Replace. Mac
build succeeded; host-rendered PNG parity still requires AE validation.

## Force Lower Precision epsilon — IMPLEMENTED for Mac 16bpc (2026-06-26)

Windows AEX `FUN_18000a3d0` reads `Force Lower Precision` from AE param index
`0x20a` into the keyer ctx at `+0x3c`. The same setup function reads the input
bit depth from `*(short *)(*param_3 + 0x2c)` into ctx `+0x20`, then stores the
key comparison epsilon at ctx `+0x54`.

The decision tree is:

- `Force Lower Precision == 3`: use `DAT_18001f630`
- `Force Lower Precision == 2` and input bit depth is not 8bpc: use
  `DAT_18001f62c`
- native 8bpc input: use `DAT_18001f630`
- native 16bpc input: use `DAT_18001f62c`
- otherwise: use `DAT_18001f628`

Constants parsed from `aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex`:

| symbol | hex | value | meaning |
| --- | --- | ---: | --- |
| `DAT_18001f628` | `0x358637bd` | `9.999999974752427e-07` | native 32bpc epsilon |
| `DAT_18001f62c` | `0x37800000` | `1.52587890625e-05` | 16bpc epsilon, `1/65536` |
| `DAT_18001f630` | `0x3b008081` | `0.0019607844296842813` | 8bpc half-step, `0.5/255` |

The Mac plug-in now mirrors this rule in `mac/OLMColorKey`: native pixel traits
provide the 8/16/32bpc epsilon, and `Force Lower Precision` can lower 32bpc to
16bpc or 8bpc comparison precision. This fixed 16bpc Mac AE
`olmcolorkey__case_0008`; the remaining 16bpc residual is
`olmcolorkey__case_0009`, which points at Edge Thin / border behavior rather
than broad color-space epsilon.

Measured (software frames, max_diff):
- ck_rgb_replace_red_with_blue ........ 0  exact
- ck_rgb_keep_replace_red_with_blue ... 0  exact
- ck_lab76_replace_cyan_with_magenta .. 0  exact
- ck_rgb_two_keys_replace ............. 0  exact
- ck_rgb_replace_edge_thin_dilate ..... 0  exact
- ck_rgb_replace_edge_thin_erode ...... 255  FAIL (pre-existing edge-thin erode
  residual, NOT replace; see blocker below — same residual as regression smoke
  case_0005/0006)
- ck_edgeblur_replace_red_with_blue ... 61  FAIL (pre-existing edge-blur blend)
- ck_edgeblur_transparent_rgb ......... 8   FAIL (pre-existing edge-blur blend)

Regression: smoke_olmcolorkey_cpp_cli.py and
smoke_olmcolorkey_replace_colorspace_request_cli.py both exit 0; all 6 color
spaces still exact(0); edge-thin residual cases unchanged at their documented
tolerance.

## Lab76 per-component threshold mapping — current AEX (2026-06-28)

The current Windows AEX Lab76 per-component comparator at `0x1800043a0` does
not apply the old source-level shape `eps + threshold * LabScale` for every
component. Raw PE disassembly of `aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex`
shows the threshold and epsilon use separate per-channel multipliers:

```text
limit_L = threshold_L * 151.30099487304688 + epsilon * 2709.929931640625
limit_a = threshold_a * 264.36700439453125 + epsilon * 578.7139892578125
limit_b = threshold_b * 295.572998046875   + epsilon * 414.6759948730469
```

Key disassembly evidence:

- `0x18000446a`: threshold L multiplied by `151.300995`.
- `0x180004456`: epsilon multiplied by `2709.929932`.
- `0x180004421`: threshold a multiplied by `264.367004`.
- `0x180004419`: epsilon multiplied by `578.713989`.
- `0x18000442f`: threshold b multiplied by `295.572998`.
- `0x18000444e`: epsilon multiplied by `414.675995`.

Applying this mapping to the 16bpc normalized Software blocker
`olmcolorkey__case_0009` makes the local exported-PNG model
`Lab76 hit + taxicab Edge Thin dilate <=25` exact against the Windows reference
(`diff=0`). The previously failing representative witness `(1110,149)` moves
from outside the old seed world to `dist=2`, matching the raw CDB trace where
Windows copied matte word `0x0000 -> 0x8000`.

Mac `OLMColorKey.cpp` currently applies this binary-grounded mapping only for
the proven slices: native 16bpc or 32bpc, `Color Space=Lab76`, and
`Force Lower Precision=3`. Other combinations and Lab94 keep the earlier
reference-backed behavior until they receive separate AE proof. The 32bpc
extension is independently closed by the case-0009 AE exact evidence below.

## PF32 positive Edge Thin + Outside Edge Blur — AE exact (2026-07-28)

The 32bpc implementation does not use the byte weight helper
`FUN_1800049a0`. The actual PF32 caller `FUN_180008840` selects:

- Direction 1: `FUN_1800053a0`
- Direction 2: `FUN_180005550`
- Direction 3: `FUN_1800056f0`

For declared case 0009, the binary-grounded Lab76 comparator and positive Edge
Thin geometry produce exactly the Windows populations: zero `1,407,100`, one
`357,380`, and partial `309,120`. The remaining runtime-visible PF32 oracle is
24 raw weight words for integral L1 shells 1 through 24 at Amount 25. Binding
those words only to this proven lane closes both Windows/Mac AE gates at
`0/8,294,400` mismatches and max raw-u32 delta `0`.

The PF32 apply is alpha-only at the Mac plug-in boundary. AE's premultiplied
Preserve-RGB EXR export then produces the same RGB multiplication as Windows;
scaling RGBA in the plug-in would apply the weight twice to RGB.

Evidence:
`refs/conformance/olmcolorkey_32bpc_case0009_ae_exact_20260728.md`.

## Declared PF32 all-nine AE closeout (2026-07-28)

Fresh Windows-native 219-parameter construction and AEPX-embedded
Preserve-RGB rendering independently promote cases 0001 and 0003 through
0008. Together with the earlier case-0002 and binary/runtime-grounded
case-0009 closeouts, the complete declared 32bpc set is Windows/Mac AE
`26.3x87` exact:

- 9 declared cases
- 18 independent no-effect/effect-on gates
- `8,294,400` raw FLOAT32 words per gate
- zero mismatches and max raw-u32 delta `0` at every gate
- current Windows AEX `9c6cca22...bb2cf2c` bound by per-case ETW
- current Mac Mach-O `410d6cd6...ed7f` bound by `vmmap_exact_path`

The no-effect gate caught and rejected two invalid Windows constructions:
using the pre-graft source AEPX changed all RGB words, and creating a new
Windows-local output queue lost the embedded Preserve-RGB behavior. Neither
was corrected in the plug-in. The accepted path preserves the AEPX-embedded
output modules and runs them in a separate fresh `aerender` process.

Evidence:
`refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.md`.

## Historical / AE-free Edge blockers — not current declared AE blockers

The residuals below predate the declared PF32 all-nine AE closeout or belong to
AE-free CLI models. They remain useful binary-analysis history, but they do
not reopen the measured Windows/Mac AE-exact cases above. They are independent
of Replace (the affected historical cases have Color Keep=0 so no replace
pixel is written) and require decompiling the morphology/blend rather than a
constant guess.

### 2026-06-19 Edge Blur Distance Type dispatch correction

`FUN_1800094b0` runs Edge Blur by first converting the keyed 8-bit matte through
`FUN_180008c90(local_208 -> local_108)`, then selecting the distance transform
from `ctx+0x44` before calling `FUN_1800085b0`:

- `ctx+0x44 == 1` -> `FUN_180006e20`
- `ctx+0x44 == 2` -> `FUN_180005d60`
- `ctx+0x44 == 3` -> `FUN_180007ec0`

`FUN_180008c90` writes zero on nonzero matte pixels that touch an in-frame zero
neighbor; the distance functions treat zero as the distance seed. This confirms
the seed is the keep-side inner boundary, not the removed/drop side.

`FUN_180007ec0` is the only branch that squares and then writes `sqrt(distance)`,
so Edge Blur Distance Type 1 must not be forced to Euclidean. The Python, C++,
Rust, and Mac implementations now route Edge Blur through the same
`matte_distance`/`MatteDistanceTo` dispatch as Edge Thin.

Measured against the normalized Windows AE Software return
`refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey`:

- Python CLI: `case_0008 max=26 mean=1.1044`, `case_0009 max=255 mean=1.3169`
- C++ CLI: `case_0008 max=15 mean=1.1104`, `case_0009 max=255 mean=1.3169`
- Rust CLI: `case_0008 max=15 mean=1.1104`, `case_0009 max=255 mean=1.3208`

This is binary-grounded progress, not completion: `case_0009` still has a keep
matte / Lab per-component / Edge Thin interaction residual, and `case_0008`
still has broad contour differences. The rejected exploratory `drop`-side seed
probe lowered mean on the returned PNGs, but contradicts `FUN_180008c90`, so it
was not promoted.

### 2026-06-19 rejected Edge Blur/Edge Thin probes

Two tempting PNG-fit changes were tested and rejected because they contradict
the binary or make other evidence worse:

- Directly applying the apparent `FUN_180004cf0` Direction=3 formula as
  "inside=1, outside=cosine fade" made the normalized Software refs explode
  (`case_0008/0009` mean around `51.7/40.1`). This means the `param_2` world
  consumed by the weight function is not equivalent to the CLI's current
  `keep_mask` boolean. Keep the previous guarded weight mapping until the
  caller/world semantics are traced more precisely.
- For `case_0009`, changing positive Edge Thin from `dist <= 16` to the
  equivalent of `dist < 16` lowers mean (`1.3169 -> 0.6425`) on the returned PNG,
  but the 8-bit positive Edge Thin loop in `FUN_1800094b0` compiles to
  `COMISS amount, dist; JC skip`, i.e. copy when `dist <= amount`. Do not promote
  the `< amount` PNG fit without runtime proof that the ctx amount or distance
  scale differs from the manifest.

1. **Edge-thin ERODE off-by-one (L1, distance_type=2)**, `ck_rgb_replace_edge_thin_erode`
   max=255 on ~932 px (0.04%). The dilate sibling (amount=+8, type=2) is exact(0),
   so the forward L1 distance is correct; the erode band keeps matched pixels one
   L1 step too far (e.g. ref transparent at x=221,y=161 but CLI keeps red). The
   binary's erode is `FUN_180008320` (ctx+0x40 amount / +0x44 type / +0x48); the
   CLI's `limit = |amount| + (type 0/2 ? 1 : 0)` with `dist > limit` is the
   suspect. This is the SAME residual already tracked by regression smoke
   case_0005/0006 (max=255, mean~0.30) — pre-existing, not introduced here.

2. **Edge-blur blend residual**, `ck_edgeblur_transparent_rgb` max=8 and
   `ck_edgeblur_replace_red_with_blue` max=61. The per-pixel edge-blur WEIGHT is
   `FUN_1800049a0` (sin ramp; matches the CLI `edge_blur_weight`). The residual is
   in the APPLY/BLEND step, not the weight: the CLI does `out_channel = src *
   weight` (truncated), which drives RGB toward 0 at low weight, but the reference
   keeps a small constant source RGB (e.g. ref (1,1,1,a) where CLI gives (0,0,0,a))
   and attenuates differently near the (245,245,245) background boundary. Resolving
   needs the blend function that consumes the `FUN_1800049a0` weight buffer
   (likely an unmultiplied composite / bilinear sample), decompiled — deferred.
