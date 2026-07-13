# OLMRadialBlur A850/D80 float32 Mac AE A/B

Date: 2026-07-13

## Binary proof

The actual 2025 AEX `FUN_18000A850 -> FUN_180009D80` path and the local mirror
now agree raw-float exactly at `(6,0)`, `(7,0)`, `(8,0)`, and `(24,0)` after:

- rounding D80 radius/angle arguments to float32 at the ABI boundary;
- preserving the `SUBSS/MULSS/ADDSS` weight and accumulation order;
- using reciprocal-then-`MULSS` normalization.

The previous `(6,0)` alpha mismatch was `1.0` versus actual AEX
`0.9999999403953552`; it was a double-precision mirror artifact.

## Mac production A/B

The Mac outer inverse-sample helper used double weights and accumulation. It
was changed to explicit operation-by-operation float32. The PF8 alpha writer
was then changed from an ungrounded `+1e-4` epsilon to pure truncation, matching
the observed AEX float and existing `CVTTSS2SI` writer evidence.

Against `refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png`:

| Candidate | max | mean | differing pixels |
| --- | ---: | ---: | ---: |
| prior baseline | 1 | 0.0046 | 31,119 |
| float32 D80 order, old epsilon | 1 | 0.0046 | 31,116 |
| float32 D80 order, pure alpha truncate | 1 | 0.0032 | 21,429 |

The combined candidate changes 20,181 pixels relative to the epsilon build:
14,934 improve and 5,247 worsen. Channel residual counts are R=4,860, G=57,
B=60, A=21,275. The original top-row `(6,0)/(7,0)/(12,0)` alpha witnesses
remain 255 locally versus 254 on Windows, so this is not `AE exact`.

## Decision

Keep the float32 D80 operation order and pure-truncate writer as
binary-grounded improvements, but do not call the case complete. The surviving
lane is the full-frame polar cell/coordinate input to D80. Do not reopen the
now-grounded D80 arithmetic or add another writer epsilon.

Installed Debug universal binary SHA-256:
`20a06e95e7fecc93621f121f2d8341da93e3d84164987c4e4d74104ede961855`.
