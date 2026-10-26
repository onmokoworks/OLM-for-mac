# Removing fixture-specific code paths (F series)

## Background
- Early tickets made single tiny test fixtures match the AEX by adding special cases. Typical examples:
  - "if the size is 9x7 / 32x18 / 16x16 and the parameters are exactly (...), use this path";
  - named predicates such as `*Tuple`, `*Exact*`, `IsRetained*`, `use_aex_*`, `Matches*Fixture`.
- The general path is exact now, so most of these special cases are dead weight.
- RadialBlur (commit `e8c4cb60`) removed 68 such conditions and 1,484 code lines with zero output change. Use the same method.

## Method (the one that worked)
1. Inventory. List every fixture-style predicate in the plugin: sizes compared with literals, long chains of literal parameter equalities, and fixture-named helpers. Some predicates are general (no fixed size; things like "center is w/2" or geometry checks that random cases hit). Separate those and keep them.
2. Switch. Add a compile-time switch (for example `OLM_<PLUGIN>_FIXTURE_PATHS`, default 0 in the experiment) that makes every fixture predicate false. Build with it.
3. Random check. Run `tools/refactor/native_diff.py --base HEAD --head WORKTREE`, a few hundred cases.
   - Any difference means a "fixture" predicate is in fact general. Find it, keep it, and repeat until the result is 0.
4. Oracle check. Write a focused generator like `tools/refactor/fixture_fuzz_radialblur.py`: parse the predicates' literal conditions (size and parameter values), then build cases that satisfy them, with mostly opaque sources.
   - Run it against the original AEX twice, with the fixture paths ON (current) and OFF, at least 300 cases each.
   - Required: the Smart route gives exactly the same exact/uncompared counts both ways, and OFF has no Smart mismatch.
   - Classic is outside the contract for SmartFX plugins (T14), so it may change, but report it.
   - For Smoother v1, Classic is the contract route: there, Classic must stay exact.
5. Delete. Remove the predicates and every branch they guard by folding the constant `false` through the boolean logic. Do this with a small script, not by hand. Then delete what became unused (compile with `-Wunused-variable -Wunused-but-set-variable -Wunused-function`, iterate).
6. Gates. Run G1 (`native_diff` against the pre-change base: 3,000 cases, both archs, both builds; 0 differences). Run step 4's OFF campaign again on the final code. Report the non-comment line count before and after.

## Rules
- Only fixture-style code. Do not touch general arithmetic.
- If a fixture path really changes Smart output (the oracle check fails with OFF), keep that one and say why in one comment line.
