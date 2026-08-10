# OLMDirectionalBlur public Noise pairwise matrix — 2026-08-11

Actual AEX owner and production are raw-byte exact for a 10-row pairwise covering array at each of PF16/PF32. Factors cover Noise Type 1/2/3, Seed 1/2, Offset 0/1, Thickness 3/10, Noise Variation 25/100, Front Fade 50 / Sharp 50 / Size 50, and 16×16 / 32×18 geometry. Type 3 uses a same-size fixed Layer. Admission is tuple-exact; unlisted higher-order combinations remain fail-closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_public_pairwise_actual_aex_20260811.py`
