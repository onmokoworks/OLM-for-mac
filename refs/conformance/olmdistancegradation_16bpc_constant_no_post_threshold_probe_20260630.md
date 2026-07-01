# OLMDistanceGradation 16bpc Constant No-Post-Threshold Probe

- Date: `2026-06-30`
- Request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Probe output root:
  `refs/reports/ae_single_case_distancegradation_constant_no_post_20260630/`
- Code change under test:
  remove the `INTERP_CONSTANT && no blur` post-compose `X > 0 ? 1 : 0`
  threshold from `compose_pixel()` in
  `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`

## Why this probe exists

The latest Windows Constant-boundary runtime return narrowed the remaining
`case_0020/0022/0023` residuals to threshold ownership / plateau membership
before final writeback. Because the Windows decomp for `FUN_181170480` does not
show a separate Constant/no-blur compose branch, the Mac port's extra
post-compose Constant threshold became suspicious.

This probe tested that hypothesis directly on live Mac AE renders before
promoting any source change.

## Result

The change had no measurable effect on the representative Mac AE outputs:

| Case | Status | Result |
| --- | --- | --- |
| `olmdistancegradation_extended__case_0012` | control, unchanged | `max=16476`, `mean=332.83683244116514`, `nonzero_px=285406` |
| `olmdistancegradation_extended__case_0020` | unchanged | `max=61165`, `mean=0.014407913773148148`, `nonzero_px=1` |
| `olmdistancegradation_extended__case_0022` | unchanged | `max=61165`, `mean=2.7663194444444446`, `nonzero_px=192` |
| `olmdistancegradation_extended__case_0023` | unchanged | `max=61165`, `mean=1.0517777054398147`, `nonzero_px=73` |

## Interpretation

- The extra post-compose Constant threshold is not the active cause of the
  remaining 16bpc Constant-boundary residual family.
- The residuals stay anchored in upstream field prep / threshold ownership /
  plateau formation, exactly where the latest Windows runtime return pointed.
- Keeping the current Mac compose threshold is acceptable for now because
  removing it does not improve the authoritative AE outputs on the tracked
  witnesses.

## Operational outcome

- The source change was reverted after the probe.
- The installed MediaCore plug-in was rebuilt and restored to the reverted
  source state.
- Next DistanceGradation work should stay upstream of compose:
  `<` vs `<=`, equality-side ownership, local plateau formation, and the exact
  Constant/THRESH_BINARY ownership around the boundary witnesses.
