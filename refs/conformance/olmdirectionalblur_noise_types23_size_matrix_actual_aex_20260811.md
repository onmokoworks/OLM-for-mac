# OLMDirectionalBlur PF16/PF32 Noise Type 2/3 × Size — 2026-08-11

Actual AEX and production are raw-byte exact for Noise Variation 25/100 × Size 0/50 in both Type 2 (generated Block noise) and Type 3 (Layer) at PF16/PF32. Type 3 requires a non-null 16×16 Layer world with sufficient padded rowbytes and local origin 0,0; Type 2 does not consume it. Only this matrix is admitted.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_types23_size_matrix_actual_aex_20260811.py`
