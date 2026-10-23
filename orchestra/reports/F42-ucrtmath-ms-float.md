status: done

summary:
- Implemented OLM-internal `ucrt_sinf`, `ucrt_cosf`, and `ucrt_log2f` in `ucrtmath/ms/` from pinned UCRT behavior/disassembly.
- Native arm64 uses contraction-off compilation and explicit double FMA, with separate reduction/evaluation paths where required.
- All 4294967296 input words pass for each function in both modes: zero mismatches, including every NaN payload.
- No plugin, worker, release gate, forbidden-action list, Microsoft binary, or AMD implementation was changed.

facts:
- Read `AGENT_GUIDE.md`, emulation GOTCHAS, compatibility plan, relevant ledger matrix rows, F27/F28 analysis and existing Rosetta/F28 harness code. Branch is `orch/F42-ucrtmath-ms-float`.
- Initial `memory_pressure` reported 52% system-wide memory free. Scratch measured 1.3 MiB during full runs. Only two mathematical processes ran at once; campaigns ran serially, with bounded 4096-row streams and no full output arrays.
- Read-only disassembly used MAIN's existing `tools/emulation/.venv/bin/python`, `pefile`, and `capstone`, with the cached DLL. The initial scratch script name `inspect.py` shadowed Python's standard module and caused an import traceback; renaming it `inspect_ucrt.py` fixed the diagnostic. No numerical hypothesis was rejected and no tool permission was rejected.
- DLL SHA256: `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`, ucrtbase 10.0.28000.2705. The existing qualified loader itself is unchanged and enforces this hash and both FMA mode masks.
- `sh ucrtmath/tests/build.sh orchestra/state/F42-ucrtmath-ms-float/build` exited 0. Apple clang 17.0.0 (clang-1700.6.4.2); `file` identified the native producer as arm64 and comparator as x86_64. Library compilation uses `-arch arm64 -O2 -ffp-contract=off -fno-fast-math`.
- `python3 ucrtmath/ms/check.py` exited 0: 106167 inputs/function, zero mismatches in both modes for each function. Corpus includes seeded random words, ±128 windows at 12 branch/special boundaries, both signs, deduplicated.
- Full-run command: `python3 ucrtmath/ms/check.py --full`. Every unsigned 32-bit input is generated once; both modes are compared for each input. The driver checks both process exits, and the comparator checks exact count, record truncation, and raw result bits including NaNs and signed zeros.

| Function | Full inputs | Non-FMA mismatches | FMA mismatches | Elapsed seconds |
| --- | ---: | ---: | ---: | ---: |
| sinf | 4294967296 | 0 | 0 | 143.502 |
| cosf | 4294967296 | 0 | 0 | 165.454 |
| log2f | 4294967296 | 0 | 0 | 377.803 |

- Full-run driver exited 0. First mismatch: none in any campaign. No tolerance, final-byte fixes, expected-output table, or host libm substitute was used.
- Algorithm facts: sine degree-nine and cosine degree-ten double polynomials; mode-dependent evaluation order; split π/2 moderate reduction with non-FMA cancellation refinement; fixed-point large reduction with truncation; extra compensated large reduction for FMA cosine. Log2 uses 16 reciprocal/log pairs and a degree-four correction, with no fused operations in either reference mode. Constants and thresholds are individually sourced by RVA in `ucrtmath/ms/README.md`.
- `python3 ucrtmath/ms/check_harness.py` exited 0: all 12 valid/short/truncated/empty stream cases had the expected exits; expf 8128, atan2f 13779, powf 79201 targeted regressions had zero mismatches in both modes.
- `python3 ucrtmath/ms/retain.py` exited 0 and retained six F42 campaigns plus three F28 regressions. Numerical result files and source/build/DLL/target hashes are retained under `ucrtmath/ms/results/`.
- Regenerable scratch build directory removed after recording hashes; all started child processes exited. Scratch remaining: 3063516 bytes (logs and small reproducible corpora).
- `git diff --check` passed. No stopped/refuted numerical hypotheses or unresolved mismatches remain.

inference:
- Successful complete-domain comparisons qualify the stated raw-return-bit API against this pinned DLL and qualified Rosetta oracle, under round-to-nearest and gradual underflow. They do not qualify errno, exception flags, alternate rounding, another UCRT version, or native Windows/AE execution.
- Separate polynomial/evaluation and reduction choices explain why substituting AMD or Apple implementations is not sufficient. No plugin equality is inferred before integration and AEX boundary tests.

changed_files:
- `ucrtmath/ms/float.c`: independent algorithm-level implementation, special-value rules, reductions and polynomial evaluations.
- `ucrtmath/ms/tables.h`: required functional constants, separate from AMD data.
- `ucrtmath/ms/README.md`: OLM-internal restriction, per-constant provenance, algorithm and validation scope.
- `ucrtmath/ms/{check.py,check_harness.py,retain.py,results/*}`: bounded validation, F28 regression/stream checks, evidence and identities.
- `ucrtmath/{README.md,build.sh,include/ucrtmath.h}`: internal-only distribution notice, native build and API declarations.
- `ucrtmath/tests/{native.c,compare.c}`: extend the F28 harness to the three additional unary functions.
- `orchestra/reports/F42-ucrtmath-ms-float.md`.

verify:
From this worktree (all commands serial, maximum two math processes):
```sh
state="$PWD/orchestra/state/F42-ucrtmath-ms-float"
mkdir -p "$state"
export TMPDIR="$state"
python3 ucrtmath/ms/check.py > "$state/recheck-targeted.log" 2>&1
python3 ucrtmath/ms/check.py --full > "$state/recheck-full.log" 2>&1
python3 ucrtmath/ms/check_harness.py > "$state/recheck-harness.log" 2>&1
python3 ucrtmath/ms/retain.py > "$state/recheck-retain.log" 2>&1
git diff --check
```
Expected: exit 0 throughout; all three full campaigns have 4294967296 inputs and zero mismatches in both modes; targets have 106167 inputs/function and zero mismatches. Stream checks accept valid records (exit 0), reject short/truncated/empty streams (exit 2); F28 regressions have zero mismatches for expf 8128, atan2f 13779, powf 79201 inputs, both modes. Numerical JSON files reproduce exactly; binary hashes are build/toolchain-specific and timings are observational.

next:
- F30-style worker import shim: link the internal functions into a newly authorized worker build; explicitly select and qualify FMA mode; bind DLL/library/worker identities; replace the relevant host substitutions and rerun actual-AEX boundary cases.
- F31-style Mac call-site ticket: switch the confirmed sinf/cosf/log2f uses only after validating operand widths and original import reachability. Re-run DirectionalBlur, ColorKey, and RadialBlur regressions with the corrected oracle; keep double sin/cos/log imports separate.
- No worker or plugin integration is included here. Do not publish this internal implementation or the combined library standalone.

Build identities (SHA256):
- `native`: `d40514f295b68b3d2061d909ae95a0ed2395db473773a5e0673c3317f4f7c043`
- `compare`: `bc0adc58319f1eb4dc465c711593402eb0b82164261a1703db408784e52de492`
- `libucrtmath.a`: `f39b3e965e71f8a1f831e39df2b5d3db0fb82c6cb60b173fd9132ff0480f93c8`
