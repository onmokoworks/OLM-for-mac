depends: F44-integrate-ms-float
depends: F43c-ucrtmath-ms-pow

# F45: integrate double ucrt_sin / ucrt_cos / ucrt_exp / ucrt_pow (worker + Mac + default oracle)

## Facts
- F43b (merged): `ucrt_sin/cos/exp` are bit-exact against UCRT. F43c provides `ucrt_pow`; if F43c
  ended blocked, integrate only sin/cos/exp and leave pow on host.
- F44 built the worker that routes float sinf/cosf/log2f and is the default oracle. Follow its
  pattern (`tools/emulation/aexcompat_patches/`).
- Double import users (plugins_2025):
  - DistanceGradation: cos exp pow sin
  - KiraKira: cos sin
  - RadialBlur: sin cos
  - ColorKey: sin
  - Smoother2: pow
  - OLMBlur: pow

## Do
1. Build a worker from F44 that also routes the double imports to `ucrtmath` in FMA mode. Add an
   INDEX entry. Validate the shim with 10^6 random inputs each against the Rosetta oracle,
   expecting 0 mismatches.
2. On the Mac side, switch the double-import call sites to `ucrt_*`, matching the original import
   boundary. Check `std::sin`/`std::cos`/`std::exp`/`std::pow` on doubles and `sin()`/`cos()`.
3. Make the new worker the default and keep F44 selectable.
4. Measure seed 1 plus one fresh seed, n300, on Smart for all 10 plugins, plus Classic for
   Smoother v1. Replay every corpus. No exact case may be lost.
   - Rebaseline only saved cases whose reference changed for a demonstrated double-math reason.
   - Report the before/after table.
- Use 1-2 processes. Check `memory_pressure` before the Rust build. Do not touch the release gate/ledger.
