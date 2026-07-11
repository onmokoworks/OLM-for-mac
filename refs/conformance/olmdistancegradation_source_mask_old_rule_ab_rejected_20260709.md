# OLMDistanceGradation source-mask old-rule A/B (rejected)

Date: 2026-07-09

## Decision

Rejected. Reverting 16bpc source_mask_owns_alpha() to alpha>0 makes the canonical 16bpc batch much worse (1/16 exact) and reopens case_0023 (73px/max 61165). The depth-gated source mask is necessary; the current-vs-depthgate split must come from another changed path or validation/provenance delta, not simply from using alpha>0 globally.

The source and installed plug-in were restored to the current integrated build after this temporary A/B.

## Result

| case | max | nonzero px | status |
| --- | ---: | ---: | --- |
| 0008 | 0 | 0 | exact |
| 0010 | 1440 | 11228 | diff |
| 0011 | 65347 | 4290 | diff |
| 0012 | 1440 | 14114 | diff |
| 0013 | 734 | 12079 | diff |
| 0014 | 92 | 13307 | diff |
| 0016 | 257 | 5438 | diff |
| 0020 | 61165 | 1 | diff |
| 0021 | 61165 | 1 | diff |
| 0022 | 61165 | 192 | diff |
| 0023 | 61165 | 73 | diff |
| 0024 | 20669 | 1054204 | diff |
| 0025 | 16656 | 862157 | diff |
| 0026 | 11480 | 902747 | diff |
| 0027 | 12301 | 454039 | diff |
| 0028 | 14750 | 459649 | diff |

## Interpretation

- FACT: global `alpha > 0` source-mask ownership is far worse than the current depth-gated rule and reopens `case_0023`.
- INFERENCE: keep the depth-gated source-mask rule. The unexplained difference between the 2026-07-08 depthgate checkpoint and the 2026-07-09 current integrated batch likely comes from another path, artifact, or provenance difference, not from replacing the depth gate with the old inclusive mask.
