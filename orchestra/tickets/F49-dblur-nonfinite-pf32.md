# F49: DirectionalBlur — nonfinite PF32 inputs (the last DBlur Smart refusals)

## Facts (read `orchestra/reports/C51-dblur-smart-r1.md` and its evidence first)
- After C45, DirectionalBlur Smart is 296/0/2/2 (seed 1) and 294/0/2/4 (seed 104). All 4 refusals are PF32 inputs
  containing NaN/Inf, held back by the finite-input gate. The 4 inputs are retained in C51 evidence.
- C51 refuted two admission hypotheses. It stopped because the existing Python paired-trace fixture does not reproduce
  the F46 worker's final output (no SSE-NaN/UCRT semantics), so no trustworthy first divergent stage exists.

## Do
1. Get a trustworthy stage capture of the original AEX for these inputs. Prefer the real worker:
   use AEXCompat watch/trace on the F46 worker (rebuilding a trace-enabled copy of the F46 worker is authorized;
   install it under `~/.cache/olm-emu/worker-F49-trace/` and add an INDEX entry; never edit `04_Tools/AEXCompat*`).
   Prove complete output binding (traced final == F46 public output) before using any stage values.
2. Locate the first arithmetic/selection divergence for each of the 4 inputs; implement x86 SSE NaN/Inf semantics
   generally (`core/x86_float.h` helpers: generated-NaN sign, operand-order NaN propagation, min/max/compare selection).
3. Lift the finite-input gate only where proven: seed 1 + seed 104 + one fresh seed n300 with 0 admitted mismatches,
   corpus preserved-exact, ASan/UBSan clean. Otherwise keep the gate and document the exact remaining blocker.

## Rules
1-2 processes; `memory_pressure` >= 30% free before any Rust build; delete build trees afterwards.
No other plugin changes, no release gate/ledger changes.
