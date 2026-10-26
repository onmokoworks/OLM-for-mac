# C01: bit-exact cleanup, round 2: dedupe the math, move test code out, shrink the admission code, fewer warnings

depends: R13-release-gate-green

Read `orchestra/REFACTOR_SPEC.md`: its gates and size limits apply. G1 (`native_diff.py`, 0 differences) decides. This time the code must get clearly shorter.

## Do (one plugin or one shared piece per commit; run G1 after each)
1. Shared math. Move the UCRT/AEX-exact math copies (per-plugin sin/cos/exp/pow/atan2 etc., for example RadialBlur's `RadialMath.inc`) into one `core/` header. Where copies differ, keep the variants with a comment that says why they differ.
2. Test code out of the product. Move test entry points and fixtures (`RadialTestEntry.inc`, `RadialTestWorkers.inc`, ColorKey `AdmissionFixtures.inc`, and the like) under `tests/` or `tools/fuzz/harnesses/`. Release builds must not compile them. Harnesses include them explicitly.
3. Admission. Find refusal branches that are now unreachable or redundant after P02/T15b/B01. Remove them. Merge the rest into shared `core/olm_world_safety.h` helpers. Refusal tags must stay the same where G1 compares them.
4. Per-depth copies. Merge 8/16/32 duplicates into templates only where G1 stays at 0.
5. Warnings. Cut them, in particular unused variables and implicit conversions. Do not change any arithmetic type.

## Done when
- G1 is 0 for all 10 plugins, G2 (Mac side) is unchanged, and the release gate v2 still passes 7/7.
- The report shows the non-comment line count and the warning count per plugin, before and after.
- If the work is too big for one run, stop at a clean commit and report it as partial, with the next steps.
