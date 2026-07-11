# OLMDirectionalBlur angle-0 front-scatter emulation report (2026-07-06)

Local Unicorn emulation of `plugins_2025/OLMDirectionalBlur.aex` internal
functions, driving the front-scatter helper `FUN_1800013e0` directly to
fact-check the angle-0 `case_0001 (494,169)` miss (Windows `[164,0,0,255]`
vs local `[0,0,0,255]`, alpha delta 0).

Driver: `tools/emulation/test_dblur_angle0_scatter.py`
Raw output: `tools/emulation/_scatter_run_output.txt`
No project sources / ledger / notes changed. No commit. No PNG tuning.

Facts are labelled FACT (decomp + emulation agree) vs INFERENCE (reasoned,
not proven by a Windows witness).

---

## 1. ABI / leaf health

FACT. `FUN_180001830` (front gaussian table builder) driven under the
Windows-x64 harness matches an independent Python reference to
< 6e-8 abs for lengths 4/8/16/32:

```
len=  4 maxdiff=1.847e-08 PASS  head=[1.00000, 0.75484, 0.32465, 0.07956]
len=  8 maxdiff=2.669e-08 PASS
len= 16 maxdiff=5.085e-08 PASS
len= 32 maxdiff=5.846e-08 PASS
```

Table formula confirmed (decomp L304-323 + data section):
`d = 2*(len/3.0)^2 + 1e-5`, `w[i] = expf(-(i*i)/d)`.
Constants read from the PE data section:
`DAT_18000b1e0 = 1e-05` (f64 add), `DAT_18000b1ec = 3.0` (f32 divisor),
`DAT_18000b1e8 = 1.0` (f32; this is the `1/param_11` numerator base in the
scatter, decomp L180-181).

This validates PE mapping, the real `expf` import, XMM float returns, and the
calling convention end-to-end for this binary. ABI is sound for driving the
scatter.

### ABI note on `param_11` (11th argument, a float)

`FUN_1800013e0`'s `param_11` is at overall argument position 10 (0-based) and,
per Windows x64, rides on the **stack**, not in an XMM register. The harness's
`float_args` only packs positions 0-3, so `param_11` is passed as its raw
float bit-pattern in `int_args[10]` (the harness places it in the correct
stack slot). The emulated results below are self-consistent with the decomp
arithmetic, which confirms the slot placement is correct.

---

## 2. FUN_1800013e0 scatter behaviour (span / membership / direction) — measured

Buffer layout confirmed by driving the function and reading back:
`A` (source) and `B` (dest accum) are RGBA, **4 f32 per pixel**, pixel index
`= row*width + col` (decomp: `iVar12 = (param_1+param_2)*4`, A read at
`param_4 + iVar12*4*4` bytes). `denom` (+0x8080) and `alpha_or_valid`
(+0x8088) are **1 f32 per pixel**.

Production call (row driver `FUN_1800038d0`, decomp L1578-1580):
`FUN_1800013e0(col, row*width, '\x01', A, B, denom, alpha_or_valid,
table(+0x58), front_strength=int(+0x48), width, param_11=fVar10*fVar11)`.

### FACT (measured) — leftward scatter, source column never written

`src_x=500, fs=32, p11=1.0` -> span=32:
- written cols min=469 max=499, count=31.
- source col 500 NOT in written set (offset 0 never written). Confirmed.
- every written col `< 500` (leftward, `iVar11=-1`). Confirmed.

### FACT (measured) — exact reach formula

`dst = src - offset`, `1 <= offset < span`, `span = int(front_strength*param_11)`.
So the leftmost dst reached is `src-(span-1)`. Measured `min_dst_written`
equals the predicted `src-(span-1)` in **every** swept row (see Section 3).

### FACT (measured) — per-source weight is `alpha_or_valid[src]`

Contribution `fVar16 = alpha_or_valid[src] * table[int(offset/param_11)]`,
`B.rgb += A.rgb*fVar16`, `denom += fVar16`, `B.a = max(B.a, fVar16)`.
Scaling `alpha_or_valid[src]`:

```
alpha_or_valid[src]=0.0 -> nonzero_cols=0        (src scatters NOTHING)
alpha_or_valid[src]=0.5 -> R@494=0.4412 denom@494=0.4412
alpha_or_valid[src]=1.0 -> R@494=0.8825 denom@494=0.8825
```

B[494] RGB scales linearly with `alpha_or_valid[src]`; `denom` tracks it 1:1.
The final normalized RGB (B.rgb/denom, applied later in `FUN_180004a20`) is
therefore independent of the *magnitude* of a single source's `alpha_or_valid`
but its **presence/absence** (zero -> no contribution) is decisive.

---

## 3. Candidate 1 (span reach) vs Candidate 2 (param_11 degeneracy)

### Candidate 1 — span reach / source-column membership (measured)

Sweep of source column vs `param_11` (fs=32 fixed), asking "does dst 494 get
any contribution?":

```
src=495 p11=0.5 span=16 min_dst=480 reach494=True  R@494=0.9862
src=500 p11=0.5 span=16 min_dst=485 reach494=True  R@494=0.6065
src=520 p11=0.5 span=16 min_dst=505 reach494=False
src=520 p11=1.0 span=32 min_dst=489 reach494=True  R@494=0.0956
src=540 p11=0.5 span=16 min_dst=525 reach494=False
src=540 p11=1.0 span=32 min_dst=509 reach494=False
src=540 p11=1.5 span=48 min_dst=493 reach494=True  R@494=0.0439
```

FACT: whether 494 receives anything is fully determined by
`src-(span-1) <= 494 <= src-1`. A source column exists that reaches 494 only
if it lies within `[495, 494+span]`. If the rotated work-row on row 169 has no
valid (`alpha_or_valid>0`) source column in that window, dst 494 accumulates
**zero** and normalizes to RGB 0 — exactly the local `[0,0,0,255]` symptom.
The falloff also matters: a distant source (src=520/540) reaching 494 lands
far out on the gaussian table, giving small `R@494` (0.04-0.10), so even when
reach succeeds, a source that is far right contributes only weakly.

### Candidate 2 — param_11 degeneracy / span collapse (measured)

`span = int(front_strength*param_11)`. The body is gated by `0 < param_9`
(outer) and `1 < param_9` (write loops). Measured skip boundary:

```
fs= 32 p11=0.03 span=0 body-skipped (0<param_9 false)
fs= 32 p11=0.06 span=1 body-skipped (1<param_9 false)
fs= 32 p11=0.10 span=3 body-ran (2 cols)
fs= 64 p11=0.03 span=1 body-skipped (1<param_9 false)
fs= 64 p11=0.06 span=3 body-ran
fs=  4 p11=0.25 span=1 body-skipped (1<param_9 false)
fs= 16 p11=0.10 span=1 body-skipped; p11=0.25 span=4 body-ran
```

FACT: for any `front_strength*param_11 <= 1.0`, the scatter helper writes
**nothing at all** for that source column (source column itself is never
written either, so it contributes zero to every dst). This is the
`param_11` (= `fVar10*fVar11`, the per-column sharp-tail taper × component/size
term) collapse. If on row 169 the component/taper coefficient drives
`param_11` low enough that `int(fs*param_11) <= 1`, the entire row's front
scatter is a no-op and every dst on the row (including 494) stays 0.

### Discriminator between the two (measured, not yet resolved for the witness)

Both candidates independently produce local RGB 0 at 494. They are
distinguishable by one measurement on the real rotated row 169:

- If, for the rotated row, there exist valid source columns in `[495, 494+span]`
  with `int(fs*param_11) > 1` yet local still emits 0 -> logic/pointer bug
  (not observed here; the isolated helper reaches 494 correctly whenever the
  window+span condition holds).
- If no valid source column lands in that window (membership gap) ->
  **Candidate 1**.
- If candidate columns exist but their `param_11` collapses span to <=1 ->
  **Candidate 2**.

The isolated-helper emulation proves the *mechanism* of both and shows the
helper itself is correct: given a valid source in range with span>1, dst 494
IS fed. Therefore the local `[0,0,0,255]` at 494 is NOT a bug inside
`FUN_1800013e0`; it is upstream — either no in-range valid source column
(Cand 1) or a collapsed `param_11` coefficient feeding the helper (Cand 2).
Resolving which requires the real per-column `alpha_or_valid`, `fVar10`,
`fVar11` on rotated row 169, which needs the full `param_7` params struct +
component map (+0x8118) + prepass — the `FUN_1800038d0` row-driver path, not
attempted here (heavier setup; see static report Section 2b).

---

## 4. Windows R=164 relationship / remaining work

- FACT (measured): the Mac front-scatter helper, when a valid source column
  sits within `[495, 494+span]` and `int(fs*param_11) > 1`, DOES write
  non-zero RGB into B[494] (e.g. `R@494=0.88` for a unit-red source at
  src=500). So the port's scatter kernel is capable of producing a non-zero R
  at 494; a zero there means zero *input* to the kernel at that dst.
- NOT PROVEN (honest blocker): I have no runtime Windows witness of row 169's
  per-column `alpha_or_valid`, component `area/center_y/half_height`, or the
  resulting `param_11`/span. Therefore I cannot state which specific source
  column produces Windows R=164, nor whether Windows differs from Mac by
  membership (Cand 1) or by coefficient (Cand 2). Asserting a numeric cause
  for 164 would be fabrication.
- What IS established as fact for the lane:
  1. Scatter geometry, reach formula, offset-0 skip, valid-alpha weighting,
     and the `span<=1` skip boundary are all emulation-confirmed.
  2. The 494 miss is upstream of `FUN_1800013e0`, in the row-driver inputs
     (source-column validity/membership and/or the `param_11` taper), not in
     the scatter kernel.
- Remaining bounded work to close it: drive `FUN_1800038d0` on row 169 with a
  populated `param_7` (pointer tables at +0x8080/+0x8088/+0x8118, scalars
  +0x30/+0x38/+0x40/+0x44/+0x48/+0x50/+0x58, noise mode +0x20=0) and the
  prepass `FUN_180001000` seeding, then read back per-column `alpha_or_valid`,
  `param_11`, span, and the leftmost reached dst. That produces the
  Candidate-1-vs-2 verdict directly. It still would not, by itself, source
  the Windows 164 without a Windows-side capture of the same row.
