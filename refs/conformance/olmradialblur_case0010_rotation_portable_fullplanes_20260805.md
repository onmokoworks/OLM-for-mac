# OLMRadialBlur case_0010 portable Rotation full-plane comparison (2026-08-05)

- Status: `bit_exact`
- Implementation: `cli/OLMRadialBlur/main.cpp::render_olmradialblur_rotation_float`
- `accum_vs_post_normalize`: `0` differing float32 words; SHA-256 `36cb0bd6cb90bcc7b01293543e7725f16c29a73f5e4733753acea728fe6195b5`
- `scatter_vs_post_scatter`: `0` differing float32 words; SHA-256 `1158168d287ca036b310156a549a4c8c370812f6969c680a7f08fb7c5b57e2e4`
- `source_vs_pre_scatter`: `0` differing float32 words; SHA-256 `1b64638f4ad7ddcf17fe951647ac14b329fcd593026cf8e067cbc4d7c2cedff0`
- `collapsed_vs_post_normalize`: `0` differing float32 words; SHA-256 `fac9eab1c00f086bc4c51366f31c787642a46199349c32e37069b617f8a50644`
- The portable worker consumes the retained AEX polar RGBA, validity, source-scalar, and size-factor planes; no Windows machine is needed for this regression.
- Claim boundary: portable worker against retained case_0010 internal planes; no host writeback claim.
