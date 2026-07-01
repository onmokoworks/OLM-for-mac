# OLMDistanceGradation 16bpc rejected outside-threshold equality probe (2026-06-30)

- Target lane: Constant + `In/Out=Both` + `Outside Threshold=0` (`case_0023`), based on the 2026-06-30 Windows boundary return and the targeted outside-side helper diagnostic.
- Probe 1 (rejected): make the outside-side Constant helper use `dist >= t` when `Outside Threshold=0` in the live Mac plug-in.
  - Result: representative witness points flipped to the Windows endpoint, but the whole frame broadened catastrophically (`nonzero_px=182728`, `mean_diff=10.24408275462963`).
- Probe 2 (rejected): floor the effective outside-side Constant threshold to `1.0` and then use `dist >= t`.
  - Result: no observable improvement over the current baseline on the live Mac plug-in.
  - `case_0023`: `nonzero_px=73`, `mean_diff=0.0040925202546296295` in the single-case PNG compare, with the tracked witness points still wrong.
  - `case_0022`: unchanged control (`nonzero_px=192`, `mean_diff=0.010763888888888889`).
- Interpretation: the unresolved Constant lane is not solved by a simple equality tweak on the outside-side helper alone. Keep the current source path and treat the next proof as a stricter upstream helper-staging / threshold-ownership question, not a one-line comparator choice.
- Artifacts:
  - `/private/tmp/ae_single_case_olmdistancegradation_case0023_20260630_eqprobe`
  - `/private/tmp/ae_single_case_olmdistancegradation_case0023_20260630_eqprobe_v2`
  - `/private/tmp/ae_single_case_olmdistancegradation_case0022_20260630_eqprobe_v2`
