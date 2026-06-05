# OLMSmoother2 ASM Facts

Updated: 2026-06-05

Purpose: keep OLMSmoother2 porting grounded in disassembly first, with PNG
diffs used as verification rather than as the source of algorithm truth.

## Current Reference Target

- Reference set: `refs/win_references/20260605_extra/OLMSmoother2`
- Most diagnostic case so far: `case_0002`
  - `Enable Color Key = 1`
  - `Color Key = [1, 1, 1, 1]`
  - `Invert Color Key = 1`
  - `Smoothness = 100`
  - `Extra Smooth = 0`
  - `Smooth Range = 2`
  - `Smoother Version = 2`
  - `Gamma Correction = 1`

## FUN_180004e10: Param Setter

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `180004e10`.

Initialization:

- `180004e54 MOV dword ptr [RCX + 0x8], ESI`
  - version-derived flag initialized to 0.
- `180004e57 MOV byte ptr [RCX + 0x1c], SIL`
  - class-plane/key predicate byte initialized to 0.
- `180004e72 MOV byte ptr [RCX + 0x60], SIL`
  - active palette count/gate initialized to 0.
- `180004e76 MOV qword ptr [RCX + 0x68], RSI`
  - active palette pointer initialized to null.

Version popup:

- `180004eec..180004f07` reads param disk id `6`.
- Stores `1` at `+0x8` only when version popup equals `1`.
- Frame setup later runs sRGB decode/encode when this flag is not `1`.

Color Key / Invert:

- `180004f0a..180004f1d` reads `Enable Color Key` disk id `1`.
- If disabled, key setup is skipped.
- If enabled:
  - `180004f1f..180004f30` reads `Invert Color Key` disk id `0xf`.
  - `180004f33..180004f57` reads and converts `Color Key` disk id `2`.

Non-invert key path:

- When `Invert Color Key == 0`, converted key color is stored in scalar slot
  starting at `+0x0c`.
- If byte `+0x1c` is still zero, it is set to `1`.
- This byte later influences class-plane threshold.
- `FUN_180002e90` also gates `FUN_180002a70` via byte `[SMParams + 0x14]`.
  `llvm-objdump` confirms the instruction bytes:
  `180002f84: 80 7b 14 00  cmpb $0x0, 0x14(%rbx)`.
  This byte sits inside the scalar key-color storage populated by the
  non-invert branch. Treat it as the scalar-key-active path, not as the UI
  `Invert Color Key` boolean.

Invert key path:

- When `Invert Color Key != 0`, converted key color is appended to the inline
  one-entry palette storage at `+0x80`.
- Setter then publishes that active palette through the palette count/pointer
  slots consumed by `FUN_180002930`.
- Practical porting conclusion: UI `Invert Color Key` does **not** mean
  "call `FUN_180002a70` with the UI key color". It routes the key color through
  `FUN_180002930`'s palette filter first.

Gamma colors path:

- `Gamma Correction == COLORS_ONLY` stores its list separately in the gamma
  config area (`+0x98` list, `+0xe8` count, mode byte `+0x48 = 3`).
- It does **not** publish that list through the frame-level active-palette
  pointer consumed by `FUN_180002930`. That pointer is for the Color Key +
  Invert path.

## FUN_180002e90: Frame Setup Orchestrator

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `180002e90`.

Order:

1. `FUN_1800024c0`
2. If byte `[SMParams + 0x18] != 0`: `FUN_180002840` unpremultiply
3. If qword `[SMParams + 0x60] != 0`: `FUN_180002930` active-palette filter
4. If byte `[SMParams + 0x14] != 0`: `FUN_180002a70`
5. If dword `[SMParams + 0x0] != 1`: `FUN_180002ba0` sRGB decode

Important caution:

- Ghidra decomp renders some of these as `param_4[6]`, `param_4[0x18]`, etc.
  Treat the disassembly offsets as primary.
- The `FUN_180002a70` gate is byte `[SMParams + 0x14]`, not the UI
  `Invert Color Key` checkbox. It corresponds to the non-invert scalar-key
  branch from `FUN_180004e10`.

## FUN_180002930: Active-Palette Filter

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `180002930`.

Behavior:

- Walk each float RGBA pixel.
- Walk active palette entries, each 16 bytes / 4 floats.
- Compare RGB only against `DAT_18002268c = 0.001960922`.
- If no palette color matches, set alpha to `0.0`.
- If any palette color matches, keep the pixel as-is.

Porting implication:

- For `case_0002`, this should keep only pixels matching white after unpremul.
- Applying this asm fact changed the C++ CLI result from:
  - old: `max=255 mean=41.8427 nz=972482/2073600`
  - new: `max=75 mean=0.0216 nz=2980/2073600`

## FUN_180002a70: Non-Invert Scalar-Key Filter

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `180002a70`, plus
`llvm-objdump` confirmation of the frame gate at `180002f84`.

Behavior:

- Walk each float RGBA pixel.
- Compare RGB against the scalar key color with
  `DAT_18002268c = 0.001960922`.
- If all RGB channels match the scalar key, set alpha to `0.0`.
- Otherwise keep the pixel.

Porting implication:

- This is the `Enable Color Key + Invert Color Key == 0` path.
- Applying it after the active-palette fix changed:
  - `case_0003`: `mean=1.3899 -> 0.0000` exact
  - `case_0004`: `mean=1.3052 -> 0.0189`

## FUN_18000ada0 / FUN_18000ae10: Class-Plane Generation

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `18000ada0` and
`18000ae10`; verified against `plugins_2025/OLMSmoother2.aex` with
`llvm-objdump` when needed.

Call order:

- The 8bpc render path calls frame setup first:
  `FUN_180002e90`.
- It then calls `FUN_18000ada0`, which iterates `FUN_18000ae10` to build the
  4-byte-per-pixel class plane.
- Practical implication: class-plane distances are computed from the
  post-frame-setup scratch buffer, after key filtering and version-v2 sRGB
  decode. The current port follows this order.

Threshold:

- `FUN_18000ae10` reads `dword [SMParams + 0x1c]`.
- The effective threshold is:
  `float(*(int *)(SMParams + 0x1c)) / 100.0 + 0.001`.
- For no-key `case_0001`, `+0x1c` remains zero, so threshold is `0.001`.
- For non-invert scalar key, setter writes byte `+0x1c = 1`, so threshold is
  effectively `0.011` because the upper three bytes are zero.

Byte layout written by `FUN_18000ae10`:

- byte 0: self vs left, when `x >= 1`
- byte 1: self vs top, when `y >= 1`
- byte 2: self vs top-left, when `x >= 1 && y >= 1`
- byte 3: self vs top-right, when `y >= 1 && x + 1 < width - 1`

The asm writes `0` or `1` using `SETNC`, not `0xff`. The downstream polygon
logic observed so far treats these bytes as zero/nonzero flags, so the port's
`0xff` storage is equivalent for current uses. If a future exact port finds a
path comparing byte values numerically, change storage to `1`.

Optional pruning:

- After the four local comparisons, `FUN_18000ae10` has an extra pruning block
  guarded by byte `[SMParams + 0x70]` (`18000af9a`).
- `FUN_180004e10` initializes `+0x70` to zero (`180004e7a`) and only populates
  the related `+0x68/+0x70` active-palette slots for the Enable Color Key +
  Invert Color Key path (`180005036..18000503a`).
- Therefore no-key `case_0001` should not take this pruning path. Do not add
  the pruning block as a fix for `case_0001` unless new references or asm show
  that a different structure is passed to `FUN_18000ae10`.

Constant check:

- Direct `.rdata` dump of `plugins_2025/OLMSmoother2.aex` confirms:
  - `DAT_180022dd0 = 100.0`
  - `DAT_180022dd4 = 0.125`
  - `DAT_180022dd8 = 0.2`
  - `DAT_180022de8 = 0.4`
  The current corner-helper constants are not the likely cause of the no-key
  residual.

ROI / extent caution:

- The full render path around `FUN_180004270` builds an initial rectangle,
  calls `FUN_18000bff0`, generates the class plane via `FUN_18000ada0`, refines
  the rectangle via `FUN_18000beb0`, then calls `FUN_180003d90`.
- `FUN_180003d90` / `FUN_1800036e0` only invoke `FUN_18000cce0` inside the
  chosen rectangle.
- If the caller's extent flag (`param_6[0x16]` in decomp's qword indexing) is
  clear, the initial rectangle is full-frame. `FUN_18000bff0` keeps it
  full-frame, and `FUN_18000beb0` returns full-frame when the input rectangle
  area is at least half the image area.
- For current `case_0001`, the PNG input alpha is nonzero over the full
  1920x1080 frame, so a simple alpha-bbox ROI would still be full-frame. Do not
  add an ROI shortcut for `case_0001` without stronger evidence about AE's
  actual extent rectangle in the Windows render.

Distance metric:

- `FUN_18000b2b0` returns zero when both alphas are zero.
- Otherwise it returns:
  `max(abs(dR), abs(dG), abs(dB), abs(dY709)) + abs(dA)`.
- Luma coefficients are:
  - R: `0.2126`
  - G: `0.7152`
  - B: `0.0722`

Current conclusion for `case_0001`:

- `case_0001` has `Enable Color Key=0`, `Smoothness=100`,
  `Extra Smooth=0`, `Smooth Range=2`, `Version=2`, `Gamma Correction=1`.
- The class-plane call order and local byte-generation formula now match the
  disassembly closely.
- A Python diagnostic that reproduced the current class-plane/index formula
  showed the large-diff pixels are dominated by switch index `0x00`:
  `big>=16` diff pixels: `0x00 = 15350`, then `0x17 = 425`,
  `0xe8 = 421`, `0xe9 = 361`, `0x97 = 349`.
- `idx=0` dispatch is the simple four-corner path:
  `FUN_1800134c0`, `FUN_180013570`, `FUN_180012ce0`, `FUN_180012c20`.
  The corner helpers' guard conditions, coordinates, and weights
  (`step * smoothness * 0.4/0.2`) match the decompilation/objdump.
- After the writeback-premul fix, `case_0001` remains `max=131 mean=0.1832`.
  A fresh diff/class-index diagnostic shows large residual pixels are still
  dominated by `idx=0x00`: `big>=16` count `17000`, with `idx=0x00 = 15280`.
- The sign is mostly `candidate < reference` in RGB, while alpha is much
  closer. Many top residual pixels have `reference == input` but the candidate
  was smoothed, which points back to class-plane / `FUN_18000c280` firing rather
  than the final PNG premultiply.
- `idx=0` dispatch is still the four-corner path only, and the four helpers'
  coordinates/weights match the objdump/decomp. Remaining `case_0001` work
  should focus on why those pixels enter `idx=0` in the port, or on a subtle
  source-plane / class-plane parameter mapping issue, not on changing the
  corner constants.

## FUN_18000c0d0 / FUN_18000ab00 / FUN_18000b120: Per-Pixel Accumulation

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `18000ab00`,
`18000b120`, `18000c0d0`, and the `FUN_18000cce0` call sequence.

`FUN_18000cce0` call order after polygon construction is:

1. Load center pixel from the post-frame-setup float plane. The cce0 prologue
   confirms `RDX/param_2` is the source float plane and `R8/param_3` is the
   class-plane descriptor passed onward to `FUN_18000c280`; the current port's
   source/class-plane order matches this.
2. `FUN_18000bb10` computes a packed gamma result:
   - low 32 bits: gamma float
   - high byte: apply flag
3. `FUN_18000c0d0`:
   - if apply flag is nonzero, pow center and every sample RGB by `1/gamma`
   - premultiply center RGB by center alpha when alpha is not `1.0`
   - premultiply every sample RGB by sample alpha when alpha is not `1.0`
4. `FUN_18000ab00`:
   - if sample count is zero, copy center
   - otherwise sum all sample weights
   - clamp the total sample weight to `[0, 1]`
   - center residual weight is `1 - clamped_sum`
   - output is center residual plus `sum(sample.rgba * sample.weight)`
5. `FUN_18000b120`:
   - if output alpha is neither `0.0` nor `1.0`, unpremultiply RGB by alpha
   - if apply flag is nonzero, pow RGB by `gamma`
   - clamp RGBA to `[0, 1]`

Porting implication:

- The current `composite()` body matches `FUN_18000ab00` structurally. Do not
  tune the residual by changing center/sample blend math unless new asm evidence
  contradicts this.
- For `Gamma Correction = None`, `FUN_18000bb10` should leave the apply flag
  zero, so `FUN_18000c0d0`/`FUN_18000b120` still do premul/unpremul and clamp,
  but do not perform the per-pixel gamma pow pair.
- Remaining `case_0001` residual is therefore more likely in polygon/sample
  generation, frame setup, or writeback/color-space details than in
  `FUN_18000ab00`'s accumulation formula.

## FUN_1800036e0: Output Writeback Premultiply

Primary evidence: `decomp/OLMSmoother2.aex.c.txt` around `FUN_1800036e0`,
cross-checked against the render/writeback flow.

- After `FUN_18000cce0` returns the straight-float RGBA result, the writeback
  path optionally applies the output sRGB encode.
- It then checks byte `(param_8 + 0x19)`.
- When that byte is nonzero and output alpha is not `1.0`, RGB is multiplied
  by output alpha before quantizing/writing the AE pixel.
- The current Windows reference PNGs show this behavior even in no-key
  `case_0001`: low-alpha pixels such as reference `[1,1,1,1]` were previously
  emitted by the port as straight-looking `[224,224,224,27]`.
- Therefore the port keeps the final writeback premultiply path enabled for
  AE/CLI output. Do not tie this byte to the UI `Enable Color Key` gate.

Porting result:

- `case_0001`: `max=255 mean=0.4304 -> max=131 mean=0.1832`
- `case_0002`: unchanged at `max=75 mean=0.0216`
- `case_0003`: unchanged exact
- `case_0004`: unchanged at `max=95 mean=0.0189`

Remaining `case_0001` residual after the writeback-premul fix is no longer a
gross straight-vs-premultiplied PNG mismatch. Continue with polygon/sample
generation, frame setup, or finer color-space/writeback details.

## FUN_18000bb10 / Gamma Mode Caution

Primary evidence: `disasm/OLMSmoother2.aex.asm.txt` around `180004e10`,
`18000a9c0`, and `18000bb10`; `decomp/OLMSmoother2.aex.c.txt` around
`FUN_180004e10`, `FUN_18000a9c0`, `FUN_18000bb10`, and `FUN_18000cce0`.

- `FUN_18000cce0` passes `(param_5 + 10)` as the gamma config pointer to
  `FUN_18000bb10`, then passes `bb10`'s packed float/apply-byte result to
  `FUN_18000c0d0` and `FUN_18000b120`.
- Decompilation shows `FUN_18000bb10` treats gamma config mode byte `1` as
  "return gamma value and set apply byte = 1".
- `FUN_180004e10` shows the AE UI popup values are not the same as that
  internal `bb10` mode byte:
  - UI `Gamma Correction = 1` / None leaves byte `[SMParams + 0x48] = 0`.
  - UI `Gamma Correction = 2` / Gamma Colors stores the gamma color list at
    `+0x98` with count at `+0xe8`, writes gamma config at `+0x30..+0x48`,
    and sets byte `[SMParams + 0x48] = 3`.
  - UI `Gamma Correction = 3` / All Colors writes gamma value at `+0x30` and
    sets byte `[SMParams + 0x48] = 1`.
- Therefore the port must map UI values to internal modes:
  `None -> 0`, `Gamma Colors -> 3`, `All Colors -> 1`.
- `FUN_18000a9c0` is the mode-3 Gamma Colors predicate. It compares RGB only
  against the gamma color list using `DAT_18002268c`; for v2 inputs it first
  encodes the candidate RGB through `FUN_180004d70`.
- Gamma Colors do **not** populate `FUN_180002930`'s frame-level active palette
  at `+0x68/+0x70`. That palette is populated by Enable Color Key + Invert
  Color Key. Treating Gamma Colors as a frame alpha mask caused
  `case_0010..0012` to blow up around `mean=22`.
- A direct port experiment that removed the current `p.gamma_mode !=
  GAMMA_NONE` guard improved `case_0001` only slightly (`mean=0.4304 ->
  0.4201`) but regressed the green key-path case `case_0004`
  (`mean=0.0189 -> 0.1048`).
- After applying the UI->internal mode mapping and moving Gamma Colors out of
  the frame-level palette filter, the 20260605 extra refs improved:
  - `case_0010 mean=22.3914 -> 0.0538`
  - `case_0011 mean=22.3670 -> 0.0607`
  - `case_0012 mean=22.4019 -> 0.1042`

## Current Known Gaps

- `case_0001`, `case_0002`, and `case_0004` remain non-exact after the
  palette/scalar-key and writeback-premul fixes:
  - `case_0001 mean=0.1832`
  - `case_0002 mean=0.0216`
  - `case_0004 mean=0.0189`
- These should be investigated through class-plane / polygon builder / smoother
  dispatch facts, not by image-diff parameter tuning.
