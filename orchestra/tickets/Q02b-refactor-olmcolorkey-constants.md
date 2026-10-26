# Q02b: ColorKey refactor, part 2: constants, names, dead code

depends: B01-address-dependent-admission

Read `orchestra/REFACTOR_SPEC.md` (the revised gates).

## State
- Q02 (merged) split ColorKey into single-TU includes: Diagnostics, Parameters, Distance, ColorMath, AdmissionFixtures, BlurMath, Pixels, Kernel and Render. The main cpp is now 333 lines.
- Its constant-naming step (`6eee3860`, reverted in `362e1c86`) was reverted because of a G1 difference. B01 later traced that difference to address-dependent admission in the base, not to the renaming.

## Do
- Redo the constant naming and the declaration cleanup, starting from `git show 6eee3860` (rebased on the current tree), plus spec points 1, 3, 4 and 5.
- Run G1 with 3,000 cases, both archs and both builds. If B01 has merged, 0 differences are required. Run G2 on the Mac side.
