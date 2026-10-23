# F27c: exhaustive UCRT vs AMD vs Apple sweep (Rosetta oracle)

## Background (facts, F27b merged; read its report and `tools/ucrt_math_probe/rosetta/`)
- The Rosetta PE loader runs ucrtbase 10.0.28000.2705 in both FMA modes.
- Qualification: non-FMA output is 500k/500k exact against Unicorn, and the FMA mode stays
  within the MPFR sanity bounds.
- Results on 100k samples:
  - expf and atan2f: UCRT == AMD aocl-libm-ose on 100%.
  - powf: 99.984%.
  - sinf and cosf: about 99.1%.
  - Apple differs from both (expf 99.885%, atan2f 79.5%).
- Full-domain coverage was blocked only because the error paths (overflow, inf/NaN domain
  errors) call `GetLastError`, and every import stub aborts.

## Orchestrator decision (this overrides F27b's abort-all policy)
- Implement the Windows imports that the error/errno path needs as benign stubs:
  `GetLastError`/`SetLastError` (a per-thread variable), plus `FlsAlloc`/`FlsGetValue`/
  `FlsSetValue`/`TlsAlloc`/`TlsGetValue`/`TlsSetValue` if they are reached. Back them with
  a zeroed fake per-thread-data block, and add whatever else the errno path needs.
- These calls only set errno/last-error state. They must not change the returned value.
- Log each stub with a hit count. Any other import still aborts.
- Qualify the stubbed paths: on every input that previously aborted, compare the returned bits
  against MPFR/IEEE expectations. For example expf(100) = +inf, sinf(inf) = NaN with the sign
  and payload recorded, and powf(-1, 0.5) = NaN.

## Steps
1. Add the stubs and the qualification above.
2. Add an in-process, chunked, resumable sweep:
   - all 2^32 float32 patterns for expf, sinf, cosf;
   - 10^8 random pairs plus the Zimmermann paper worst-case inputs for atan2f and powf.
   Sweep each in both UCRT modes against AMD (both builds) and Apple x86_64 libm. Stream only
   counts, per-exponent-bucket mismatch counts, and the first 2000 mismatches per pair to files.
   Use 1 process, 2 at most. Check `memory_pressure` first. Estimate the run time from a 2^24
   chunk before starting the full sweep.
3. For sinf/cosf/powf, where AMD is not identical, characterise the mismatch region: which
   exponent ranges, and whether it is argument reduction or polynomial. Diff the UCRT
   disassembly against the AMD source for that path. Report whether a small AMD patch could
   explain all mismatches. Do not write the patch yet.

## Rules
- Never commit Microsoft binaries. Keep committed results small (under 5 MB).
- `tools/ucrt_math_probe/` must stay independent of OLM plugin code.
- No plugin, AEXCompat, or fuzzer-oracle changes.
- Stop rule applies. A blocked import is not a stop reason if a benign stub exists; stub it and
  record it.
