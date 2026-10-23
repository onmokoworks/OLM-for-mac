# F51: prove the x86_64 slice of the Universal `.plugin` bundles equals the arm64 slice

## Why
The shipped bundles are Universal (arm64 + x86_64). F47d proved arm64 bundle == original AEX (901 exact, then R02
fixed ColorKeep PF32). The x86_64 slice (Intel Macs, and AE under Rosetta) has never been rendered: under Rosetta the
Unicorn JIT crashes in AEX process attach (`F47d-native-plugin-all.md`, line ~43). Risks specific to x86_64: different
libm/intrinsics paths, `ucrtmath` FMA-mode emulation on CPUs without FMA, SSE vs NEON NaN behaviour in code that relies
on `core/x86_float.h`, `-ffp-contract`, and `long double`.

## Do
1. Build a plugin-only host mode that does not start Unicorn or attach the AEX (same fake AE host and suites as the F47d
   native-plugin bridge). Build it for x86_64 and run it under `arch -x86_64`. Building in a space-free directory under
   `~/.cache/olm-emu/build-F51/` is authorized (delete afterwards); install to `~/.cache/olm-emu/worker-F51-x86host/` with an
   INDEX entry. Never edit `04_Tools/AEXCompat*`.
2. For all ten plugins, render the same generated cases (seed 1 n300 Smart, plus Smoother v1 Classic) with the arm64
   slice (native) and the x86_64 slice (Rosetta), from the same Universal Release bundles (`tools/fuzz/build_F47_bundles.py`).
   Require byte-identical output and identical refusal decisions. Also replay every corpus.
3. Every difference is a finding: locate it (first differing stage/function) and fix it generally in the source
   (e.g. explicit `fmaf` use, compiler flags per arch, NaN helpers). Arm64 output must not change: re-verify arm64 bundle
   vs AEX with `verify_F47d.py` for any plugin you touch.
4. Also check whether the x86_64 slice requires any CPU feature (AVX/FMA) that older Intel Macs (deployment target 11.0)
   lack; report the instruction-set requirements found with `otool`/disassembly.

## Rules
1-2 processes; `memory_pressure` >= 30% free before Rust builds; delete build trees afterwards. No release gate/ledger changes.
