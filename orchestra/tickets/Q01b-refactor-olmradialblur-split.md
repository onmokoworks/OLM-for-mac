# Q01b: RadialBlur refactor, part 2: split the remaining 5,923-line main file

Read `orchestra/REFACTOR_SPEC.md` first. The gates were revised: G1 decides, G2 compares the Mac side only, and there is no G3/ref_vs_fast/release gate per ticket.

## State
- Q01 (merged) moved the scalar math into `RadialMath.inc` and the point diagnostics into `RadialDiagnostics.inc`. It also named three constants and removed `SampleChannel`.
- Report: `orchestra/reports/Q01-refactor-olmradialblur.md`.
- `OLMRadialBlur.cpp` is still 5,923 lines. Its FLOAT32 trig bit patterns have no names or provenance yet.

## Do
- Split the main file into single-responsibility includes of at most about 1,000 lines each, for example: params/UI, geometry/ROI, the per-mode kernels (zoom, rotation, scatter...), per-depth pixel traits, and Smart/Classic entry. Keep the code that text-reading tests use in the main cpp.
- Name and annotate the remaining constants, following spec point 1.
- Look for and remove dead code, and mark the order-sensitive spots.
- Run G1 after each structural commit (at least 1,000 cases each time). Run the full 3,000 at the end.
- Size rule: the non-comment, non-blank line total must not grow.
