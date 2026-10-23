# F27b: UCRT math oracle as a native x86_64 process under Rosetta

## Background (facts)
- F27 (merged; read `orchestra/reports/F27-ucrt-math-probe.md` and `tools/ucrt_math_probe/`)
  pinned ucrtbase.dll 10.0.28000.2705, sha256 `385a6d73…84f3`, under
  `~/.cache/olm-emu/ucrt/10.0.28000.2705/`.
- F27 also found the FMA3 dispatch: setter RVA `0xd6800`, capability RVA `0x13bdf4`, active
  mask RVA `0x13bdf0`.
- Under Unicorn the non-FMA path runs. The FMA path faults (`UC_ERR_INSN_INVALID` on
  `vfmadd213sd` / `vfnmadd231sd`), because Unicorn's TCG lacks FMA.
- Orchestrator check on this Mac (macOS 15.7.2, arm64): an `x86_64` binary under Rosetta
  executes `vfmadd231sd` correctly. fma(0.1, 10, -1) = `0x1p-54`, the fused result. CPUID
  bit FMA reads 0 even so.

## Goal
Build a fast UCRT math oracle that runs ucrtbase's own machine code natively under Rosetta. It
must cover both FMA modes. Then measure bit-exact agreement with AMD LibM and Apple libm,
exhaustively for unary functions.

## Steps
1. **Minimal PE loader** in C, at `tools/ucrt_math_probe/rosetta/`, built with
   `clang -arch x86_64`.
   - mmap ucrtbase.dll's sections at a fresh base, apply base relocations, and resolve the
     exports `expf atan2f sinf cosf powf` (also `exp sin cos atan2 pow` if cheap).
   - Bind imports to stub functions that abort with the import name. Do not run DllMain or
     CRT startup.
   - Set the FMA3 globals the way F27 did, for both modes.
   - Call through `__attribute__((ms_abi))` function pointers.
   - Keep it single-threaded and use no Wine.
2. **Qualify the oracle before trusting it.**
   - (a) Run the non-FMA mode under Rosetta and the non-FMA mode under F27's Unicorn probe on
     about 100k shared inputs per function. They must match bit-for-bit.
   - (b) Check the FMA mode for sanity against MPFR-correct values if available (via
     `brew`-free means, e.g. pip `gmpy2` in a scratch venv), or else against long double.
     It must stay within the paper's ulp bounds: expf 0.501, atan2f 0.584, sinf/cosf 0.530,
     powf 1.00.
   - (c) Every UCRT path that hits an import stub must abort loudly. Record which inputs do so
     (errno/matherr paths).
3. **Measure.**
   - Unary functions: run exhaustively over all 2^32 float32 bit patterns, chunked, streaming
     only counts and the first 1000 mismatches to files. Compare UCRT-FMA, UCRT-noFMA, Apple
     libm (arm64 or x86_64, label which), and AMD aocl-libm-ose.
   - For AMD, build only the scalar C functions, for x86_64 with `-ffp-contract=off` and
     with FMA. Record the commit.
   - Binary functions: run 10^8 random pairs plus the paper's worst-case inputs.
   - Use 1 process; at most 2 if a single run exceeds about 2 h. Check memory with
     `memory_pressure` before you start.
4. **Report** a table of bit-match counts and rates for each function and each pair, the first
   mismatches, and the run time per function.

## Rules
- Never commit Microsoft binaries.
- Keep `tools/ucrt_math_probe/` free of any import from OLM plugin code. It may later be split
  into its own repository.
- No plugin changes. No AEXCompat changes. No fuzzer oracle swap; propose that as the next
  ticket.
- Stop rule applies. Stopping on the first failed approach is not enough. Before stopping, try
  at least the Rosetta loader path and one fallback.
