# OLMDistanceGradation Layer/no-bg changes disabled A/B

Date: 2026-07-09

## Decision

Disabling the Layer/no-bg source/color changes does not recover case_0010/0011/0024..0028. Therefore the current-vs-depthgate split is not caused by the Layer/no-bg compose/inheritance changes alone; the top suspect remains the global 16bpc source-mask/depthgate rule or field input mask ownership.

The source and installed plug-in were restored to the current integrated build after this temporary A/B.

## Result

| case | max | nonzero px | status |
| --- | ---: | ---: | --- |
| 0008 | 0 | 0 | exact |
| 0010 | 2 | 351 | diff |
| 0011 | 2 | 501 | diff |
| 0012 | 16384 | 278028 | diff |
| 0013 | 16384 | 167383 | diff |
| 0014 | 16384 | 378683 | diff |
| 0016 | 9710 | 14131 | diff |
| 0020 | 0 | 0 | exact |
| 0021 | 0 | 0 | exact |
| 0022 | 0 | 0 | exact |
| 0023 | 0 | 0 | exact |
| 0024 | 20 | 1051915 | diff |
| 0025 | 6 | 860084 | diff |
| 0026 | 4 | 900709 | diff |
| 0027 | 4 | 451535 | diff |
| 0028 | 3080 | 457177 | diff |

## Interpretation

- FACT: `0010/0011/0024..0028` remain at the same current integrated residual levels even when the Layer/no-bg compose/inheritance changes are disabled.
- INFERENCE: the next A/B should target `source_mask_owns_alpha()` ownership, not Layer/no-bg color compose.
