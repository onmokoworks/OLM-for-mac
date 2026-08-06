# OLMToonDilate current Mac AE representative — 2026-08-06

- Status: **PASS**.
- AE 26.3x87, Software renderer, 32bpc, working space None, linear blending off.
- The current installed Universal binary SHA-256 is `7d2c24d8ad0f7436ee7035e0d926a2abaac1a74bc9305a4223f76230c1fc5537`; the nonce-bound fresh AE process mapped that exact path.
- A 64×64 AE-generated typed source rendered with Search Radius 13, with an exact parameter readback of 13.
- Both the no-effect and effect-on outputs repeat the retained canonical Mac output at all 16,384 raw FLOAT values. The effect branch differs from its control at 6,448 values, so this is not a no-op load smoke.

This closes the current-Mac-AE representative load/render release gate only. It does not broaden the existing Windows exactness boundary.
