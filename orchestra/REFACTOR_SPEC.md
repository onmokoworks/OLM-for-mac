# Readability refactor before release (Q series)

## Why
- The user decided on 2026-10-26 to do this before the release.
- The plugin sources are 2,000-6,500-line single files full of bit-pattern constants, with no explanation of why the code has its current shape. The risk is that later changes break things without anyone noticing.
- The goal is code a maintainer can read and change safely. Behaviour must not change by a single bit.

## What "readable" means here
1. Constants. Give every non-obvious literal a named `constexpr`. This covers float bit patterns, table offsets, RVAs and thresholds. Each one gets a one-line comment saying:
   - what it is (for example "1/pi as float", "Cody-Waite pi split part 2", "sin minimax c3");
   - where it comes from (the AEX RVA, or the UCRT function).
   Keep the bit-pattern form (`F32FromBits(0x...)`) where exactness requires it. Do not convert it to decimal.
2. Structure. Split each giant file by responsibility, for example: params/UI, geometry/ROI, per-depth kernels, math helpers, Smart/Classic entry.
   - Preferred mechanism: headers or `.inc` files `#include`d from the plugin's main `.cpp`. This keeps a single translation unit, so inlining and FP codegen stay as close as possible, and the fuzz adapters that `#include "production_under_test.cpp"` keep working.
   - If you add real translation units, you must update every build entry point (see Gates). Explain why in the report.
3. Order-sensitive code. Where the evaluation order, the float/double width, the FMA avoidance or the NaN order mirrors the original binary, mark it with one short comment such as `// order matches AEX 0x1800123a0; do not reassociate`. Do not add a comment on every line.
4. Dead code. Remove code that is unreachable in the shipped and reference builds: old experiment branches, `#if 0`, unused helpers, duplicated near-identical functions. Duplicates that differ on purpose (for example a per-depth variant) stay, with a comment explaining the difference.
5. Names. Rename variables like `v14`, `local_38`, `uVar3` to meaningful names where the meaning is clear. Do not rename things you are unsure about. Leave those as they are rather than guessing.
6. Keep the existing comment density modest, and keep the house style. Do not rewrite algorithms, "simplify" arithmetic, change types or reorder operations.
7. Generated files (`*.generated.inc`, for example Smoother v1's instruction-level translation) are out of scope. Do not edit them. You may document how they are generated.
8. Keep the `OLM_REFERENCE_BUILD` reference/fast split and the `OLM_PARALLEL_MAX` behaviour exactly as they are.

## Gates (all must pass; report real numbers)
- G1 native differential against the pre-refactor base: `tools/refactor/native_diff.py` (built in Q00).
  - Build the plugin at `--base <base sha>` and at HEAD, in both reference and fast builds, for arm64 and x86_64 (Rosetta).
  - Compare raw output bytes on at least 3,000 random cases per plugin. Use all samplers: default, realistic, realistic-v2, odd-even, float colours, all depths, downsample, and some 4K cases.
  - Required result: 0 differences, 0 new refusals, the same refusal tags.
- G2: replay every corpus of the plugin in `tests/fuzz_corpus/` with its recorded flags. The results must equal the base results, including the known-failing ones; do not "fix" them here.
- G3: fresh fuzz seed 909, `--geometry realistic`, 100 cases against the default oracle. The result must equal the base.
- G4: `tools/perf/ref_vs_fast.py` for the plugin. Expected result: 0 mismatches.
- G5: build every entry point. That means the Xcode project, `scripts/package_mac_plugins.sh` (Universal) and `scripts/run_olm_release_gate_v2.py` (all stages it runs locally). The UI oracle compare (`tests/ui_oracle/compare_mac.py`) must pass where it applies.
- G6: compiler warnings must not increase.

## Rules
- One plugin (plus its own `core/` files) per ticket. Do not touch other plugins' code. `core/` files shared by two plugins belong to the ticket named in that ticket's scope.
- Commit in small steps. Run G1 at least after each structural step, so that a difference can be bisected to one commit.
- If G1 shows any difference you cannot explain and fix by undoing your change, revert that step. This is a refactor; differences are never accepted.
- Report: before/after line counts per file, the list of named constants (sample), the removed dead code (what and why it was dead), and the gate results.

## Size limits (the user is wary of workers writing very long code)
- A refactor must shrink the code, not grow it. In the plugin files in scope, the non-comment, non-blank line count after the change must be at most the count before. Report both numbers.
- No source file over about 1,000 lines after the split. Aim for files of 200-800 lines with a single responsibility.
- Do not add new abstraction layers, frameworks, templates or wrapper classes. Do not add "helper" files that only one place uses. Moving code is fine; inventing structure is not.
- New tools (Q00) stay small: one file, about 400 lines at most, reusing the existing fuzz adapters and `ref_vs_fast.py` code by import, not by copy.
- Evidence goes into the report as numbers. Do not commit new one-off verify, probe or summarize scripts for these tickets; the gates use the shared tools.
