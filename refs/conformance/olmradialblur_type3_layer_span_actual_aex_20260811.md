# OLM RadialBlur Type 3 Layer-to-span contract — 2026-08-11

Status: **exact static and executed composer contract**

The pinned Windows AEX composers execute exactly at PF8, PF16, and PF32 for Noise Variation 25/100. They convert the checked-out Layer pixel to float ARGB, premultiply RGB by alpha, calculate BT.601 luminance with double coefficients in binary instruction order, mix it with one by Noise Variation, and multiply the existing size-factor plane. Equal-size worlds with shifted origins prove that local out-of-bounds samples contribute zero luminance.

Changing Seed, Noise Offset, and Thickness leaves all span words unchanged. Static control flow independently proves why: Type 3 bypasses the generated-noise function receiving those fields. Zoom and Rotation dispatch after the common composition.

AEXCompat zero-filled Layer backing can therefore produce deterministic zero luminance, while a rejected/null Layer can preserve a zero-filled destination allocation. Those are harness initialization effects and do not admit Type 3 RenderWorld or native AE behavior.

Reproduction: `python3 tools/emulation/probe_olmradialblur_type3_layer_span_actual_aex_20260811.py`
