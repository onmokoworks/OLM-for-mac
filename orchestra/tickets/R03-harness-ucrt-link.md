# R03: release/unit harnesses — add ucrtmath to every legacy link recipe

## Facts (read `orchestra/reports/I03-integration-check.md` and `I03-classification.json`)
I03 class (a) "Missing UCRT link inputs": 71 fixture records + 22 generic gate entries fail to COMPILE/LINK, not on pixels.
Boundaries: F31 (float `_ucrt_expf/powf/atan2f` in Blur/ColorKey/Directional/Distance/Kira/Radial harness recipes),
F45 (Kira warp fixtures: `_ucrt_cos/_ucrt_sin`), F46 (Smoother2 default/ROI/gamma: `_ucrt_pow`). Also
`tools/fuzz/test_colorkey_existing_F20.py` fails on missing UCRT linkage, and the parameter-UI audits for
Directional/Distance/Radial.

## Do
1. Find every harness/test build recipe (scripts/, tests/, tools/) that compiles plugin sources, and link `ucrtmath`
   the same way the fuzz adapters and Xcode projects do (one shared helper if practical, not 90 copies).
2. Rerun exactly the I03 class-(a)-link commands. Each must now compile; then report its real outcome
   (pass / numeric failure / stale binding). A numeric failure is a finding: report it with its first difference.
3. Do not change assertions, expected bytes, or bindings here (that is R04/R05).

## Rules
OLM_TEST_JOBS=2, 1-2 processes. No plugin production changes.
