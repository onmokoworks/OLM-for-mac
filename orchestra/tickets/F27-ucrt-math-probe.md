# F27: UCRT math feasibility probe (expf / atan2f / sinf / cosf / powf)

## Background (facts)
- The original AEX files import `expf`, `atan2f`, `sinf`, `cosf` (and some `sin`/`cos`) from
  `api-ms-win-crt-math-l1-1-0.dll`, which is ucrtbase.dll on real Windows.
- The AEXCompat worker does not run the Windows code. It substitutes host Rust `f32::exp`,
  `f32::powf`, `f32::sin`, and so on, which means macOS libm
  (`guest/crates/aex-guest-worker/src/x64/imports.rs`, `install_float_import`, around line 2637).
  The "oracle" is therefore Apple libm at these call sites.
- Zimmermann et al., "Accuracy of Mathematical Functions" (2026 update, MSVC 2026 column),
  binary32 max ulp:

  | function | MSVC | Apple | AMD LibM 5.3 |
  |---|---|---|---|
  | expf | 0.501 | 0.514 | 0.501 |
  | atan2f | 0.584 | 0.722 | 0.584 |
  | sinf | 0.530 | 0.846 | 0.530 |
  | cosf | 0.530 | 0.846 | 0.729 |
  | powf | 1.00 | 0.514 | 1.56 |

- The MSVC and AMD worst-case atan2f input is the same: (0x1.fffe24p+59, 0x1.000adcp+73).
  Inference: MSVC atan2f, and maybe expf, derive from AMD LibM.
- AMD aocl-libm-ose (github.com/amd/aocl-libm-ose) is BSD-3. It contains `src/ref/atan2f.c`,
  `src/optimized/{expf,powf,sinf,cosf}.c`, and `src/fast/*`.
- The x64 UCRT switches between FMA3 and non-FMA3 implementations at runtime
  (`_set_FMA3_enable`).

## Goal
Find out, per function, whether a bit-exact UCRT implementation is achievable on Mac. Do this
in two steps:
(A) get the real ucrtbase math code running inside the emulator as ground truth;
(B) test whether AMD LibM source reproduces it bit-for-bit.

## Steps
1. **Obtain UCRT binaries.**
   - Get `ucrtbase.dll` from the official Microsoft Windows SDK / UCRT redistributable, for
     example with the `xwin` tool (`cargo install xwin`; it downloads the MSVC CRT and the
     Windows SDK and accepts the license). Prefer the SDK `Redist/ucrt/DLLs/x64/ucrtbase.dll`.
   - Also note the static `libucrt.lib` if present.
   - Store them ONLY under `~/.cache/olm-emu/ucrt/<version>/`. Never commit Microsoft binaries
     to the repo; commit only their sha256 and version in your report.
   - Record the file version and sha256.
2. **Run the real ucrtbase math in the emulator** (minimal path).
   - Write a small standalone probe, either a Rust bin or Python+unicorn using the existing
     venv `tools/emulation/.venv`. It maps ucrtbase.dll, resolves the export, and calls
     `expf`/`atan2f`/`sinf`/`cosf`/`powf` directly as leaf functions (Win64 ABI, xmm0/xmm1).
     Stub whatever they touch.
   - Find the FMA3 dispatch global (look for `__use_fma3_lib` / `_set_FMA3_enable`
     disassembly) and run both settings.
   - Do NOT modify `04_Tools/AEXCompat*`. If you need a worker change later, describe it in
     `next`.
3. **Compare.** Build AMD aocl-libm-ose scalar functions natively on arm64 Mac. A
   clone and build under your scratch dir is fine; delete the build afterwards. Isolate the
   single functions if the full build is heavy; you may need to pick the C reference paths, not
   the x86 asm.
   - Inputs: about 2,000,000 random float32 per unary function, plus all floats in the ranges
     the plugins actually use (expf on [-100, 10]; sinf/cosf on [-8, 8]; a dense sample
     near zero), plus the paper's worst-case inputs. For atan2f/powf, use about 2,000,000
     random pairs plus the worst cases.
   - Compare raw bits for each pair: UCRT(FMA3 on), UCRT(FMA3 off), AMD, Apple libm.
   - Keep the emulator probe single-process, or at most 2 processes. Stream results to files.
4. **Report:** a per-function table of bit-match rates for each pair, the first mismatching
   inputs, the ucrtbase version and sha256, and which FMA3 mode is the default on a modern
   x64 CPU.

## Out of scope
- No plugin code changes.
- No oracle swap in the fuzzer yet. Propose the follow-up ticket instead.

## Deliverable
- `tools/ucrt_math_probe/`: probe sources, a README with exact reproduce commands, and small
  result CSV/JSON summaries (under 1 MB).
- `orchestra/reports/F27-ucrt-math-probe.md`.

Stop rule applies. If ucrtbase cannot be obtained or loaded after two distinct approaches, report
blocked with what failed.
