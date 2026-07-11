# DG_FIELD_GEN_REPORT — FUN_181174760 field generation (2026-07-05)

Static-analysis pass done directly in the main session (subagents hit the account
session limit before saving). All claims below are read from
`decomp/DistanceGradation.aex.c.txt` unless marked INFERENCE.

## FUN_181174760 structure (decomp lines 3542506-3542560)

Pipeline (FACT, read operand-by-operand):
1. `FUN_181395030` ×4 — allocate 4 working buffers (`local_48/68/88/a8`), cv::Mat-like.
2. `FUN_181395230(local_48, CONCAT44(param_7,param_6), 8)` — seed buffer with the
   input value/mask.
3. `FUN_1812b15a0(local_48, local_88, 2, 0,0,0,0)` — **distance stage, type arg = 2**
   (matches `cv::distanceTransform` with `distanceType = CV_DIST_L2 = 2`). INFERENCE:
   OpenCV distanceTransform; strings are stripped so not name-confirmed, but the
   `(src, dst, type=2, mask=0…)` shape matches.
4. `FUN_1812aef70(local_88, local_68, 1)` — convert/scale.
5. `FUN_1812b6a40(local_68, local_a8, (double)fVar4, (double)fVar3, type)` — **threshold
   stage**. Signature `(src, dst, thresh, maxval, type)` matches `cv::threshold`.
6. `FUN_18117ca50(local_a8, param_3)` — write the field into the output buffer `param_3`.

External dependency: the distance + threshold stages are OpenCV-family
(`FUN_1812b15a0 / FUN_1812b6a40`, high addresses, cv::Mat buffers). **Full emulation
of the distanceTransform over the frame is heavy** and was NOT run here; the
threshold rule was established statically instead (chosen path — see below).

## Threshold / normalize binary reality (decomp 3542534-3542553) — FACT

```
uVar2 = 2;                         // default OpenCV threshold type = THRESH_TRUNC
fVar4 = (float)param_4;            // param_4 = distance threshold (e.g. inside=36, outside=0)
if (param_8 == 1) {
    uVar2 = 0;                     // -> THRESH_BINARY
    fVar3 = DAT_181504a90;         // maxval = 1.0  (DAT_181504a90 == 1.0, confirmed by the
    if (DAT_181504a90 <= fVar4)    //   "1.0 - X" invert usage at decomp 3540339/3540354)
        fVar3 = fVar4;             // maxval = max(1.0, threshold)
} else {
    fVar3 = fVar4;
    if (fVar4 == 0.0) {            // threshold==0 -> substitute default constant DAT_181504a8c
        fVar3 = DAT_181504a8c;
        fVar4 = DAT_181504a8c;
    }
}
FUN_1812b6a40(local_68, local_a8, (double)fVar4, (double)fVar3, type=uVar2);
```

- **type = 0 (THRESH_BINARY)** when `param_8 == 1`; else **type = 2 (THRESH_TRUNC)**.
- THRESH_BINARY semantics (OpenCV): `dst = (src > thresh) ? maxval : 0` — **strict `>`**.
- For the Constant/binary case_0023 path this is the THRESH_BINARY branch (consistent
  with the existing Mac fix noted in `notes/IR_OLMDistanceGradation.md` as the
  "Constant-specific THRESH_BINARY path from FUN_181174760").

## Cross-check against Strategy A field_x (strong consistency) — FACT

Strategy A reproduced Windows exactly using field_x = (0, 1, 1) for the triplet.
Applying the strict-`>` THRESH_BINARY rule to the recorded distances vs threshold 36:
- `(414,393)` dist 35.014 > 36 ? **No → 0** → field_x=0 ✓
- `(415,393)` dist 36.014 > 36 ? **Yes → maxval** → field_x=1 ✓
- `(416,393)` dist 37.014 > 36 ? **Yes → maxval** → field_x=1 ✓

The threshold operator is therefore grounded as **strict `>`** on the distance value.
The (0,1,1) that made compose match Windows is exactly what this operator produces.

## Implication for the 73px residual

- **8px threshold-crossing family**: these sit at distance ≈ threshold. With a strict
  `>` at exactly 36.0, field_x flips on sub-pixel distance differences. So this family
  is sensitive to the **distanceTransform (FUN_1812b15a0) sub-pixel output**, not to the
  threshold operator itself (which is now grounded). If Mac's distanceTransform yields a
  distance on the other side of 36.0 than Windows for those 8px, field_x flips → residual.
- **65px inside=1.0 family**: field_x = 1 on both sides (fully inside), so this is **NOT
  a threshold flip**. Separate cause — most likely the convert/normalize step
  (`FUN_1812aef70`) or a different channel/pass, NOT the binary threshold.

## Chosen path & why

Full distanceTransform emulation was deferred: it is the heavy OpenCV op and the
threshold *operator* (the actual open question for the 8px crossing family) is
statically determinable and cross-consistent with Strategy A. Running OpenCV
distanceTransform under Unicorn to get exact Windows sub-pixel distances at the 8px is
the remaining work, but it is a distance-value question, not a threshold-rule question.

## Remaining / not done (no over-claim)

1. distanceTransform (`FUN_1812b15a0`) not emulated → no exact Windows distance values at
   the 8px crossing pixels; cannot yet prove Mac-vs-Windows distance divergence there.
2. Decompiler arity ambiguity: call sites show 4 args, definition shows 8. `param_8`
   (which selects BINARY vs TRUNC) source not pinned to a specific params-struct field;
   BINARY is inferred for case_0023 from the field_x match + existing Mac fix.
3. No live Mac field dump compared in this pass.
4. `DAT_181504a8c` (threshold==0 substitute) value not read.

---

## ADDENDUM (2026-07-05, main session) — 8px crossing localized to threshold-scaling ownership

### Mac port already uses exact EDT (chamfer hypothesis REJECTED)
`mac/OLMDistanceGradation/OLMDistanceGradation.cpp:159` — the Mac port uses a
**Meijster 2-pass exact Euclidean distance transform**, explicitly "Produces the SAME
result as OpenCV distanceTransform(DIST_L2, DIST_MASK_PRECISE)". Windows `FUN_1812b15a0`
is called with `distanceType=2 (DIST_L2), maskSize=0 (DIST_MASK_PRECISE)` — the same exact
transform. So the distance VALUES are grounded-identical; the 8px flip is NOT a
chamfer-vs-precise difference.

### Threshold operator matches (both strict `>`)
Mac constant path `OLMDistanceGradation.cpp:440`: `out[i] = (out[i] > t) ? 1.0f : 0.0f;`
— strict `>`, matching OpenCV THRESH_BINARY. Operator is grounded-identical.

### The one remaining knob: threshold-scaling / resolution ownership
- **Mac** (`OLMDistanceGradation.cpp:436`): `float t = (float)threshold * ds_scale;`
  — scales the UI threshold by the averaged downsample factor. The Mac source itself
  flags this at lines 428-431 as "only implementation-grounded ... the exact
  threshold-scaling ownership in the caller path is not fully proven yet."
- **Windows** (decomp 3541111 / 3541117 / 3541133): the caller passes the **RAW threshold
  integer** to `FUN_181174760` — `(int)param_6[0x17]` (inside), `*(param_6+0xbc)`
  (outside), `iVar5`. **No ds_scale multiply at the call site.** The EDT runs on
  `param_2`'s Mat (whatever resolution the caller staged) and threshold compares raw.

### Conclusion (binary-grounded)
Distance values and threshold operator are proven identical between Mac and Windows.
The 8px threshold-crossing residual is localized to the **(EDT resolution × threshold
scaling) pairing** — precisely the `ds_scale` application in `dt_to_normalized` that the
Mac source already marks as unproven. Windows applies NO scale to the threshold at the
`FUN_181174760` call site.

### Concrete close-out step (not done here; needs render-resolution fact)
Determine case_0023's actual working resolution (`ds`) for this render:
- If `ds == 1.0` (full-res), Mac `t = 36*1 = 36` == Windows raw 36 → the 8px must then be
  float-rounding at exactly d==36.0 (extremely narrow); revisit whether Mac's `>` vs a
  possible Windows `>=` matters at exact equality.
- If `ds != 1.0`, Mac scales the threshold while Windows (per call site) does not scale it
  — that mismatch flips boundary pixels and IS the 8px residual. Fix = align Mac's
  threshold-scaling to the Windows caller (raw threshold vs the staged Mat resolution).

The 65px `inside=1.0` family is unaffected by this (field_x=1 both sides) and remains a
separate cause (convert/normalize `FUN_1812aef70` / NORM_MINMAX denom).
