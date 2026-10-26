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

## Gates (revised after Q01; all must pass; report real numbers)
- G1 is the decisive gate: `tools/refactor/native_diff.py` against the pre-refactor base.
  - Run it at HEAD vs base, both archs, both builds, with at least 3,000 cases per plugin.
  - Required: 0 differences, 0 new refusals, 0 execution errors.
  - Because G1 compares reference-base with reference-head and fast-base with fast-head, a separate `ref_vs_fast.py` run is not needed.
- G2 corpus replay: replay every corpus of the plugin with its recorded flags, on base and head. Compare only the Mac side: the native output hashes, refusal tags, and pass/fail per witness.
  - Oracle-side diagnostics, crash snapshots and wall-time budget outcomes can vary between runs and are not part of the comparison. The oracle is not changed by these tickets.
  - Report any Mac-side difference.
- G3: none. The fresh-seed oracle campaign is replaced by G1. The orchestrator runs its own seed after merge.
- G4 build: the plugin's Xcode project builds for both archs. The text-reading and UI tests for the plugin pass, including `tests/ui_oracle/compare_mac.py` where it applies.
  - The release gate v2 and packaging run once at the end of the Q series, by the orchestrator, not per ticket.
- G5: compiler warnings must not increase.

## Rules
- Some tests read the main `.cpp` by text. Examples: `tests/ui_oracle/compare_mac.py` extracts `UpdateParameterUI` and its dispatch, and some `tests/test_*parameter_ui*` files assert literal expressions. Keep the code these tests read in the main `.cpp`. If that is impossible, change the test only so that it reads the new file. Never weaken what a test asserts. Run those tests (part of G5).
- G3 compares Smart only, against the base run. Classic mismatches are outside the contract for the SmartFX plugins (see notes/KNOWN_ORIGINAL_BUGS.md, T14), so they only need to equal the base.
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
