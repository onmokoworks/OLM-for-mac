# DG_M1_NOTES — DistanceGradation 16bpc compose callback (`FUN_181170480`)

Static analysis only. Read-only pass over `disasm/DistanceGradation.aex.asm.txt`,
`decomp/DistanceGradation.aex.c.txt`, `notes/IR_OLMDistanceGradation.md`.
No binary was executed for this note.

Binary constants:
- `ImageBase = 0x180000000`, `SizeOfImage = 0x191e000`.
- `FUN_181170480 = base + 0x1170480` (16bpc iterate callback / compose+word-store).
- `FUN_181170280 = base + 0x1170280` (16bpc iterate wrapper that installs the callback).
- `FUN_181170380 = base + 0x1170380` (8bpc sibling wrapper, installs `FUN_181170870`).
- `FUN_181170870 = base + 0x1170870` (8bpc sibling callback, same refcon layout).

Legend: **FACT** = present verbatim in disasm/decomp; **INFERRED** = derived from
AE SDK convention + code shape; **UNCERTAIN** = plausible but not proven here.

---

## 1. `FUN_181170480` argument layout (the compose / word-store callback)

### 1a. Calling convention observed in the disassembly — FACT

Prologue at `0x181170480` (Win x64 fastcall + shadow space):

```
181170480  MOV [RSP+0x8],RBX          ; home RBX (arg2 slot, unused as arg here)
181170485  PUSH RDI
181170486  SUB RSP,0xa0
18117048d  CMP byte ptr [RCX+0x90],0x0 ; RCX = param_1 = refcon
181170494  MOV RBX,RCX                 ; RBX = refcon (kept for whole body)
181170497  MOV RDI,[RSP+0xd0]          ; RDI = param_5 = OUTPUT pixel ptr (5th arg, on stack)
18117049f  MOVSXD R9,EDX               ; R9 = sign-extend(EDX)  -> param_2 (x)
```

After `PUSH RDI` (+8) and `SUB RSP,0xa0` (+0xa0), the return address is at
`[RSP+0xa8]`. The first stacked argument (5th integer arg) sits at
`[RSP+0xa8+8] = [RSP+0xb0]`... but the code reads the output ptr from
`[RSP+0xd0]`. `0xd0 = 0xa8 + 0x28`, i.e. **the 5th argument** in the standard
`shadow(0x20)+retaddr(0x8)=0x28` layout relative to the pre-prologue RSP.
So the register/stack assignment for the callback is:

| Slot | Register / stack | Ghidra name | Meaning (this callback) |
| --- | --- | --- | --- |
| arg0 | RCX | `param_1` | **refcon** (pointer to the effect param/context block) — FACT |
| arg1 | EDX | `param_2` | **x coordinate** (column), sign-extended into R9 — FACT |
| arg2 | R8D | `param_3` | **y coordinate** (row) — FACT |
| arg3 | R9 | `param_4` | unused in body (Ghidra `param_4`, never referenced) — FACT (unused) |
| arg4 | `[RSP+0xd0]` | `param_5` | **output pixel pointer** (16-bit ARGB, RDI) — FACT |

Note the Ghidra C signature `FUN_181170480(longlong *param_1,int param_2,int param_3,undefined8 param_4,undefined2 *param_5)`
matches this exactly: `param_2`=x, `param_3`=y, `param_5`=out pixel words.

INFERRED (AE SDK): this is the After Effects **`iterate16`** callback signature
`(refcon, x, y, in_pixelP, out_pixelP)`. `param_4` is the *input* pixel pointer
that AE also passes; this callback ignores it because it fetches the source
and field pixels itself from worlds stored inside the refcon (see 1c). Only
`x`,`y`,`refcon`,`out` are used.

### 1b. Output pixel `param_5` (RDI) is a 16-bit ARGB quad — FACT

Stores are 16-bit words at offsets 0/2/4/6 of RDI:

```
181170810  MOV word ptr [RDI+0x2],AX   ; = R  (param_5[1])
181170818  MOV word ptr [RDI+0x6],AX   ; = B  (param_5[3])
181170820  MOV word ptr [RDI+0x4],AX   ; = G  (param_5[2])
181170828  MOV word ptr [RDI],AX       ; = A  (param_5[0])
```

Channel order is **A,R,G,B** in memory (AE `PF_Pixel16` = ARGB). Each word is
produced by `MULSS ...,DAT_181504ac4` (×32768) then **`CVTTSS2SI`**
(truncate-toward-zero to int) — FACT. This is the truncation writeback the IR
ledger flags as a binary fact not yet adopted on Mac.

### 1c. Field world and source world both come from the refcon `param_1` — FACT

Two AE worlds are read, both indexed by the same `(x=param_2, y=param_3)`:

- **Field world = `param_1[1]`** (offset `0x8` in the refcon):
  ```
  18117054d  MOV R10,[RBX+0x8]        ; field world header
  ...  CMP R9D,[R10+0x24]  (width)   ; +0x24 = width
       CMP R8D,[R10+0x28]  (height)  ; +0x28 = height
       IMUL EAX,[R10+0x20] (rowbytes); +0x20 = rowbytes/stride
       LEA RCX,[RCX + R9*8]          ; +x*8  (8 bytes/pixel = 4×u16)
       ADD RCX,[R10+0x18]            ; +0x18 = data base ptr
  ```
  Then reads words at `[RCX+2]` (green? see below) etc., scaled by
  `DAT_181504a80 = 1/32768` to get the distance value `fVar13 -> _X`.
  Decomp: `_X = puVar6[1] * (1/32768)` where `puVar6[1]` is the **word at
  offset +2 = the R channel of the field pixel** (ARGB ⇒ [0]=A,[1]=R,[2]=G,[3]=B).
  UNCERTAIN: IR text for the 8bpc path calls this the "green byte"; in the
  16bpc layout the compose reads `puVar6[1]` (offset +2), which is the **R**
  word under ARGB. The exact channel label (R vs G) should be re-confirmed
  against a live field dump, but the offset (+2) is a FACT.

- **Source/layer world = `*param_1` = `param_1[0]`** (offset `0x0`):
  ```
  1811705cd  MOV R10,[RBX]           ; source world header (same +0x18/0x20/0x24/0x28 layout)
  ```
  Read into `fVar19..fVar22` (A,R,G,B of the source layer), used only when
  `render_mode == 2` (Layer).

Field-world / source-world header layout (AE `PF_LayerDef`/`PF_EffectWorld`) — FACT:
`+0x18` = data ptr, `+0x20` = rowbytes, `+0x24` = width, `+0x28` = height.
Pixel stride is 8 bytes (4×u16). Bounds-checked; out-of-range ⇒ pointer stays 0.

### 1d. Refcon scalar offsets used by the compose body — FACT (offsets), INFERRED (labels)

All relative to `RBX = param_1 = refcon`:

| Offset | Access | Decomp expr | Meaning (inferred from use) |
| --- | --- | --- | --- |
| `+0x90` | byte | `(char)param_1[0x12]` | **degenerate/no-source flag**. If ≠0 → early degenerate write (block 1e). |
| `+0xc0` | byte | `(char)param_1[0x18]` | **use_background_color** (0/1). |
| `+0xc1` | byte | `*(char*)(param_1+0xc1)` | **invert** flag. If 0 → `_X = 1 - fieldX`. |
| `+0x94` | int | `*(int*)(param_1+0x94)` | **In/Out mode** (`==2` and `==3` branch = alpha derivation). |
| `+0xcc` | int | `*(int*)(param_1+0xcc)` | **interpolation mode** (1=Linear,3=Sphere,4=Power; `iVar1-1U` test). |
| `+0xc8` | int | `*(int*)(param_1+0xc8)` | **render mode** (1=Gradation color, 2=Layer/source). |
| `+0xa8` | float | `*(float*)(param_1+0x15)`→`+0xa8` region | Sphere/Power constants area. |
| `+0xd0` | float | `*(float*)(param_1+0x1a)` / `[RBX+0xd0]` | **Power exponent** (`powf(_X, power)`). |
| `+0xa0` | float | `*(float*)(param_1+0x14)` | Gradation Color R. |
| `+0x9c` | float | `[RBX+0x9c]` | Gradation Color G (green). |
| `+0xa4` | float | `[RBX+0xa4]` | Gradation Color B. |
| `+0xb0` | float | `*(float*)(param_1+0x16)` / `[RBX+0xb0]` | BG Color R. |
| `+0xac` | float | `[RBX+0xac]` | BG Color G. |
| `+0xb4` | float | `[RBX+0xb4]` | BG Color B. |

Label mapping cross-checked against IR §"16bpc compose's color-selection shape"
(`render_mode==1`→Gradation, `==2`→source RGB, `use_bg` mixes `BG*(1-X)+inner*X`).

### 1e. Two witnessed exit paths — matches the retained case_0023 facts — FACT

**Degenerate path** (`refcon+0x90 != 0`), block `0x18117048d..0x18117051b`:
- If `use_bg (+0xc0) == 0`: writes all four words = 0 → `A=R=G=B=0`.
- Else: `A = 0x8000`, `R = trunc(BGr*32768)`, `G = trunc(BGg*32768)`,
  `B = trunc(BGb*32768)`.

This is exactly the retained **hit0** observation: `out_pixel16_pre` all zero,
`r8 = 0x2d` (= y=45, a coordinate — see below). INFERRED: hit0 was a pixel that
took the degenerate `use_bg==0` all-zero write, or was sampled before compose.

**Normal compose path** (`refcon+0x90 == 0`), block from `0x18117051c`:
computes `_X` from the field R word, applies invert / interpolation, selects
RGB, and stores `A,R,G,B` via `CVTTSS2SI`.

Retained **hit23**: `rdx=0x391 (x=913)`, `r8=0x169 (y=361)`,
`out_pixel16_pre = 8000 8000 0000 0000  8000 8000 0000 0000 ...` — i.e. the
observed pre-store output words show `A=0x8000, R=0x8000, G=0, B=0` repeating.
FACT-consistent reading: `A=0x8000` = full alpha (0x8000 = 1.0×32768),
`R=0x8000` = red endpoint at 1.0, `G=B=0`. This matches the case_0023
representative "red endpoint" `[65535,0,0,65535]`-style selection at the
threshold plateau discussed in IR (`(415,393)` etc.), scaled to the 0x8000
= half-range that the callback stores before AE promotes to 16-bit-full.
NOTE: `0x8000` here is `1.0 * 32768`, the callback's internal 15-bit-ish
"AE 16bpc" max, not `0xFFFF`.

INFERRED coordinate reading of the retained facts:
- hit0: `r8 = 0x2d`. Under the ABI in 1a, **`r8` = param_3 = y**. So hit0 y=45.
- hit23: `rdx = 0x391` = param_2 = x = 913; `r8 = 0x169` = param_3 = y = 361.
- UNCERTAIN: the retained facts say "refcon qwords = 0x80008000 repeating" for
  hit0 — that pattern is the *output* word pattern (0x8000,0x8000), not the
  refcon; if it was genuinely read at the refcon pointer it would instead be
  the effect param block. Treat the `0x80008000` reading as most likely an
  output-word capture, pending the live dump.

---

## 2. `FUN_181170280` — role and arguments — FACT

Signature: `FUN_181170280(param_1, param_2, param_3, param_4, param_5)`.

Body (decomp `0x181170280..0x18117043?`):
```
iVar1 = *(int*)(param_4 + 0x38);     // render-context: bottom / y-extent
iVar2 = *(int*)(param_4 + 0x30);     // render-context: top / y-origin
*param_5 = param_3;                  // store a world/context ptr into refcon[0]
uVar3   = param_5[1];                // refcon[1] = second world (the field world!)
FUN_181174fb0(local_4b8, *(qword*)(param_1 + 0x180));   // acquire suites
... acquire "PF iterate16 Suite" -> local_1f8 ...
uVar5 = (*iterate16)(param_1, 0, iVar1 - iVar2, param_3,
                     param_4 + 0x2c, param_5, FUN_181170480, uVar3);
FUN_181174ff0(local_4b8);            // release suites
```

Role: **the 16bpc iterate driver.** It (a) fetches the AE `PF iterate16 Suite`,
(b) computes the row count `iVar1 - iVar2` (`= *(param_4+0x38) - *(param_4+0x30)`,
i.e. output rect height), (c) passes `refcon = param_5` (with
`param_5[0]=param_3` = one world and `param_5[1]` = the other world/handle) and
the callback `FUN_181170480`, then (d) invokes the suite's iterate function,
which fans `FUN_181170480` across every output pixel.

Arguments — FACT:
- `param_1` — effect handle / instance (suite table at `+0x180`).
- `param_3` — a world pointer stored into `refcon[0]` (`*param_5 = param_3`).
- `param_4` — a **render-context/rect struct**; `+0x30`/`+0x38` are y-origin/y-extent,
  and **`param_4 + 0x2c`** is passed to the suite as the iterate rect/area arg.
- `param_5` — the **refcon** the callback receives as its `param_1`. Its first
  qwords are worlds ( `[0]`=source/output world, `[1]`=field world ), and the
  compose scalar params live at `+0x90..+0xd0` (§1d).

INFERRED (AE SDK): the iterate16 suite call is
`iterate(effect_ref, progress_base, progress_final, src_worldP, areaP,
refcon, fn, dst_worldP)`. So `uVar3 = param_5[1]` is passed as the **dst world**
and `param_3` as the **src world**, while the compose fn reads its own field
world from `refcon[1]`. The 8bpc sibling `FUN_181170380` is byte-identical in
shape but requests `"PF Iterate8 Suite"` and installs `FUN_181170870`.

---

## 3. Call-chain needed to drive `FUN_181170480` standalone

To obtain witness compose output at `(414/415/416, 393)` you must reconstruct
the **refcon** the way `FUN_181170280` builds it, because `FUN_181170480` reads
everything (worlds + params) from that one block.

Two viable strategies:

**A. Drive the callback directly (leaf-level, recommended for M1).** — INFERRED
Build a refcon buffer in emulator memory with:
- `[0x00]` = pointer to a source/layer `PF_EffectWorld` header (only needed if
  `render_mode==2`).
- `[0x08]` = pointer to the **field world** header (`+0x18` data ptr,
  `+0x20` rowbytes, `+0x24` width, `+0x28` height). Populate the field pixels'
  **+2 word** (`R`) with `X*32768` at the target pixels.
- `+0x90` byte = 0 (normal path), `+0xc0` = use_bg, `+0xc1` = invert,
  `+0x94` = in/out mode, `+0xc8` = render mode, `+0xcc` = interp mode,
  `+0xd0`/param area = Power, and the color floats at
  `+0x9c/0xa0/0xa4` (Gradation RGB) and `+0xac/0xb0/0xb4` (BG RGB).
Then call `FUN_181170480(refcon, x, y, 0, out_ptr)` per pixel and read the four
words at `out_ptr`. This exercises the exact compose+writeback with no AE suite
dependency and no OpenCV. This is the smallest reproduction of the case_0023
endpoint decision.

**B. Drive via `FUN_181170280`.** — requires stubbing the AE suite acquisition
(`FUN_181174fb0`, the `"PF iterate16 Suite"` lookup, `FUN_181174ff0`) and
supplying a fake iterate that walks the rect calling `FUN_181170480`. More
faithful (it also builds `refcon[0]/[1]`), but it pulls in the suite plumbing
and the whole field-prep upstream (`FUN_181174760` etc.) if you want a real
field. Only needed if the goal is to prove field construction, which for the
compose-word witness it is not.

For the compose RGBA / output-word witness (the current case_0023 ask),
**strategy A is sufficient and minimal**: the field values at the triplet are
already known (`field_x = 0` at (414,393), `1` at (415/416,393)), so we feed
those directly and read the stored words.

Upstream producer chain (for reference, from decomp callsites): the field
world fed as `refcon[1]` is produced by `FUN_181174760`
(`distanceTransform → threshold → normalize`, Constant switches mode 2→0) and
combined for `Both` by `FUN_181182b20` (`cvAdd`). `FUN_181170280`/`FUN_181170380`
are called from the render body around decomp line 3542245 / 3542224.

---

## 4. Import-independent leaf functions for validation

Goal: a tiny arithmetic/table function with no AE-suite / no OpenCV / no libm
import dependency, so it can be emulated leaf-only and checked by hand.

**Best candidate — `FUN_181170480` itself in the degenerate branch.** — FACT
When `refcon+0x90 != 0` and `refcon+0xc0 (use_bg) != 0`, the entire body is:
```
R = trunc(BGr * 32768);  G = trunc(BGg * 32768);  B = trunc(BGb * 32768);  A = 0x8000
```
No imports, no field read. Predicted I/O (build a refcon with `+0x90=1`,
`+0xc0=1`, BG floats `+0xb0=1.0, +0xac=0.5, +0xb4=0.25`):
- expected out words: `A=0x8000 (32768)`, `R=0x8000 (32768)`, `G=0x4000 (16384)`,
  `B=0x2000 (8192)`. This isolates the ×32768 + `CVTTSS2SI` truncation contract
  with zero dependencies.
And with `+0xc0=0` (use_bg off): all four words = `0`.

**Secondary candidate — the Linear+Grad compose path (no libm).** — FACT
With `+0x90=0`, `+0xcc=1` (Linear, skips pow/sqrt/powf), `+0xc8=1`
(Gradation color), `+0xc0=0` (no bg), `+0xc1=1` (invert on ⇒ `_X = fieldX`),
in/out mode `+0x94=1` (neither 2 nor 3 ⇒ `fVar18 = 1.0`), field R word = `0x4000`
(⇒ `_X = 0.5`): the output alpha path gives `A = trunc(1.0 * 0.5 * 32768)=0x4000`,
and RGB = Gradation color × ... . This exercises the arithmetic path but still
no imports (Linear avoids `pow`/`sqrt`/`powf` at `0x1813a0426/32/2c`).

AVOID as leaf checks: any path with `+0xcc==3` (Sphere → `sqrt`/`pow` at
`0x1813a0426`,`0x1813a0432`) or `+0xcc==4` (Power → `powf` at `0x1813a042c`);
those call libm thunks.

---

## 5. Minimal verification commands for the main session

The generic PE64 loader `tools/emulation/aex_loader.py` is base `0x180000000`,
so `FUN_181170480 = 0x181170480` maps directly. Suggested minimal checks
(pseudocode contract for a new `test_dg_compose.py`; do not run here):

1. **Degenerate/use_bg leaf (no deps):**
   ```
   load DistanceGradation.aex at 0x180000000
   refcon = alloc(0x100); write byte refcon+0x90 = 1; refcon+0xc0 = 1
   write f32 refcon+0xb0=1.0, refcon+0xac=0.5, refcon+0xb4=0.25
   out = alloc(8)
   call 0x181170480(rcx=refcon, edx=0, r8d=0, r9=0, [stack arg5]=out)
   assert words(out) == [0x8000, 0x8000, 0x4000, 0x2000]   # A,R,G,B
   ```
   Then flip `refcon+0xc0 = 0`, expect `[0,0,0,0]`.

2. **case_0023 triplet compose (strategy A):**
   ```
   build field world header (data,rowbytes,width,height) with 3 pixels:
     (414,393).R_word = 0            # field_x = 0
     (415,393).R_word = 0x8000       # field_x = 1.0
     (416,393).R_word = 0x8000       # field_x = 1.0
   refcon+0x08 = &field_world; refcon+0x90 = 0
   set +0xc1 (invert), +0x94 (in/out), +0xc8 (render), +0xcc (interp),
       gradation/bg color floats per case_0023 params
   for (x,y) in [(414,393),(415,393),(416,393)]:
       call 0x181170480(refcon, x, y, 0, out); record words(out)
   compare to Windows typed triplet (35.014->blue endpoint, 36.013/37.013->red)
   ```
   Expected per retained facts: the `field_x=1` pixels store the endpoint
   pattern seen in hit23 (`A=0x8000,R=0x8000,G=0,B=0`) under the case_0023
   render/color config; the `field_x=0` pixel stores the opposite endpoint.

3. **ABI sanity:** confirm the loader passes arg5 on the stack at the slot the
   prologue reads (`[RSP+0xd0]` after `PUSH RDI` + `SUB RSP,0xa0`), i.e. the
   standard 5th-integer-arg position. If the loader mis-places arg5, the
   callback writes through a garbage `RDI`; the degenerate leaf test (step 1)
   is the fastest detector because it has a known fixed output.

---

## Summary of confidence

- **FACT**: ABI (RCX=refcon, EDX=x, R8D=y, arg5[stack]=out pixel), ARGB word
  order + ×32768 + `CVTTSS2SI` truncation writeback, refcon field-world at `+0x8`
  / source world at `+0x0`, world header offsets `+0x18/0x20/0x24/0x28`, the two
  refcon scalar offsets and the degenerate/normal split, `FUN_181170280` as the
  iterate16 driver installing `FUN_181170480`.
- **INFERRED**: AE `iterate16` callback semantics, the exact param-name labels
  for the refcon scalar offsets (cross-checked with IR), coordinate reading of
  the retained `rdx/r8` values (x=rdx, y=r8).
- **UNCERTAIN**: whether the field distance is read from the R word (+2) vs a
  "green" channel as older IR text says; whether the retained hit0
  `0x80008000` bytes are refcon contents or output words (most likely output).
