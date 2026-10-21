# RadialBlur Type1 pairwise source-guard readiness (2026-08-13)

Status: `pass_pairwise_source_guard_integrated_hostless`

The retained PF8/PF16 pairwise fixture sources reconstruct to four exact active-row identities:

- PF8_9x7: `3b62de8577b33598ede56c0a3ca5bc636a40b9bf7bc9599000d9840b531eeffe`
- PF16_9x7: `5c853513cbbbdab275383c7aa6b6d82e0f7fef95565a7d0d4f6dd04426a75b33`
- PF8_32x18: `85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000`
- PF16_32x18: `c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c`

Current production now requires these exact active-row identities. Both arm64 and x86_64 hostless probes retain all 16 pairwise outputs and reject first/middle/last mutations for each source (12 controls) with input unchanged and output untouched. A strict/deep-valid ad-hoc Universal candidate is complete; install and installed replay remain pending. AE was not launched.
