# OLMRadialBlur case_0010 Mac production Rotation planes (2026-08-05)

- Status: `native_exact` for the bounded internal-plane and actual-AEX CPU PF8 writeback comparison.
- Scope: `RenderRotation8`, 1920x1080 PF8 input, Rotation, center `(960,540)`, outer strength `4`, no offsets, no edge fade, no inner blur, repeat border, ratio `1`, angle `0`, quality `5`.
- The Mac production entry path matches the retained actual-AEX fixture bit-for-bit for polar RGBA, eligibility, source scalar, final RGBA accumulator, max alpha, and normalized polar RGBA.
- Exact SHA-256 identities are recorded in `olmradialblur_case0010_rotation_mac_production_planes_20260805.json`.
- The implementation uses AEX paired float32 trigonometry, rounded float32 `1/255` multiplication, the two-stage `FUN_180002780 -> FUN_1800024c0` worker contract, explicit float32 multiply/add/divide boundaries, and the pinned Windows span-3 Gaussian rounding.
- The completed actual-AEX owner reaches the native PF8 packer. Its sampler-to-internal-cell pointer relation, XMM input words, `255.0f` scale, and immediate post-store ARGB bytes are exact at `(1612,6)` and `(1614,6)`.
- Mac production matches the native witnesses: `(1612,6)` is ARGB `(255,5,5,5)` and `(1614,6)` is `(255,255,255,255)`. The white result comes from truncating the negative RGB value `0xbb85c1ca` after multiplication by 255 and storing the low byte, without a lower clamp.
- This closes the bounded actual-AEX CPU sampler → internal frame → PF8-world boundary. Mac AE module loading, Software host render, and PF-world-to-export provenance remain separate host gates.
