# OLMRadialBlur Scatter-Tail Binary/Source Audit

Date: 2026-07-17
Scope: Mac-only, read-only comparison of live-grounded AEX
`RadialBlur_scatter_tail_by_direction` (`FUN_180001c90`) against the current
`mac/OLMRadialBlur/OLMRadialBlur.cpp` implementation.

## Findings

1. **FACT: mode-1 span selection differs in Zoom.**

   The AEX selects mode 1 as `base + caller_distance`, mode 2 as
   `max(base, caller_distance)`, and mode 3 as `caller_distance`; it then
   upper-clamps the resolved span to `3000` and computes
   `trunc(span * span_gate)` (`decomp/OLMRadialBlur.aex.c.txt:585-600`).
   Mac Zoom has no mode-1 branch (`mac/OLMRadialBlur/OLMRadialBlur.cpp:849-854`).
   Mac Rotation does contain the three branches, but its post-selection
   `span - 1` is a separate mismatch (Finding 2).

2. **FACT: Rotation effective length is decremented.**

   The AEX clamps the resolved span to `3000` before multiplying by the gate
   (`decomp/OLMRadialBlur.aex.c.txt:596-600`; raw clamp and conversion are at
   `disasm/OLMRadialBlur.aex.asm.txt:829-838`). Mac computes `span - 1` before
   clamping (`mac/OLMRadialBlur/OLMRadialBlur.cpp:857-864`).

3. **FACT: table-step input and sample origin differ.**

   AEX computes the positive-length divisor as integer
   `trunc(30000 / effective_len)` and samples table entries from offset `1`
   while the offset remains below `effective_len`
   (`decomp/OLMRadialBlur.aex.c.txt:599-603,619-690,702-714`). Mac generates
   a vector indexed from `0` through `length - 1`
   (`mac/OLMRadialBlur/OLMRadialBlur.cpp:834-846,1205-1218`). The quotient
   form exists in both, but Mac supplies the altered length and zero-origin
   sequence.

4. **FACT: outer and inner table bases are not modeled separately.**

   AEX reads the outer table at `ctx + 0x68` and the inner table at
   `ctx + 0x1d528` (`decomp/OLMRadialBlur.aex.c.txt:619-620,733-734`). Mac
   synthesizes one generic Rotation weight vector
   (`mac/OLMRadialBlur/OLMRadialBlur.cpp:834-846`) and bypasses Rotation when
   Inner Strength is nonzero (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1122-1127`).

5. **FACT: inner angular underflow and radius-row behavior differ.**

   AEX inner underflow rewinds to the angular row tail and advances the
   destination to the next radius row
   (`decomp/OLMRadialBlur.aex.c.txt:726-731,807-824`). Mac applies same-row
   circular angular wrapping to every tap
   (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1205-1208`) and has no equivalent
   inner-row transition. Mac's final inverse sampler independently clamps both
   radius neighbors (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1311-1320`).

6. **FACT: source-alpha accumulation and max-alpha ownership differ.**

   AEX multiplies the passed source alpha by each table weight, accumulates all
   four RGBA channels, and updates a persistent max-alpha plane using
   `old <= new && new != old`
   (`decomp/OLMRadialBlur.aex.c.txt:619-627`). Mac uses a local maximum only
   in the small path and writes source alpha directly in convolution paths
   (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1204-1218,1260-1265,1288-1295`).

7. **FACT: NaN propagation differs at the Mac weighted-alpha guard.**

   Mac only writes normalized RGB when `weighted_alpha > 1e-8`; a NaN fails
   that test (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1214-1218`). The AEX helper
   accumulates the float contribution after the caller gate without that
   weighted-alpha guard (`decomp/OLMRadialBlur.aex.c.txt:619-627`).

## Interpretation Boundary

**INFERENCE:** The AEX max comparison and C++ `std::max` have equivalent
ordinary quiet-NaN ordering when considered alone. The source-level NaN
mismatch established here is the Mac conditional suppression of the RGB path,
combined with the missing persistent max-alpha plane; no broader NaN claim is
made.

**Non-claim:** No production patch, PNG tuning, or ledger change is authorized
by this audit. A function-level equivalence harness must first cover span
selection, effective-length conversion, table indexing, outer/inner row
transitions, source-alpha/RGBA accumulation, max-alpha comparison, and NaN
inputs. Until that harness exists and passes its intended equivalence cases,
these findings remain audit evidence only.
