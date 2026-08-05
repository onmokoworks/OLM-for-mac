# OLMRadialBlur case_0010 Rotation full-plane fixture (2026-08-05)

- Status: `pass`
- Fixture: `refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805`
- Geometry: `1800 x 1104` (1987200 cells)
- Eligibility mask: `{'0': 565113, '1': 1422087}`
- Source-alpha cells different from 1.0: `64703`
- Final normalization differing float32 words: `0`
- Stage contract: pre-scatter polar is preserved through scatter; scatter seeds exact `RGB=polar.rgb*scatter_alpha, A=scatter_alpha`; gather mutates the accumulator; final `RGB=accum.rgb/accum.a, A=max_alpha` reconstruction is bit-exact.
- Claim boundary: case_0010 actual-AEX internal Rotation planes only; this does not prove the legacy Windows PNG, Mac AE writeback, other parameters, or other bit depths.
