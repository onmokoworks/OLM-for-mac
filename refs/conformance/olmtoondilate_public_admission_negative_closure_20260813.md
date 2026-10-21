# OLMToonDilate public admission negative closure — 2026-08-13

Verdict: `PASS_PUBLIC_ADMISSION_NEGATIVE_CLOSURE`

Frozen production source: `42b47acbc3cd37bcaefdedc1b46f0507ed2e478c5eaab921f645f9055a9c8470`. A fresh isolated arm64 bundle rejected all 633 admission one-aways and satisfied 69 callback/lifecycle rows across PF8/PF16/PF32 (702 total).

Every rejection pins the exact PF_Err, rejection stage, callback counts, unused optional layer checkin, and byte-for-byte immutability of input/output storage (including padding/guards) plus both world headers. The matrix covers all five admitted families, every geometry/extent/origin/flag/format/depth/radius/downsample field, first/middle/last source bytes, input padding, and exact/directional partial overlap.

Callback closure covers null and returned-error layer/output/parameter callbacks, null pica and suite function pointers, suite acquisition/get-format/release failures, null-world returns, and successful proof that optional `checkin_layer_pixels` is unused. This is AE-free and install-free; it does not claim native After Effects host execution.

Reproduce read-only: `python3 tools/emulation/test_olmtoondilate_public_admission_negative_closure_20260813.py`
