# OLMKiraKira Mode3 32x18 bounded public closure (2026-08-14)

Status: **raw_exact_bounded_public_classic_and_smart**

The one wrapped-linear 32x18 RGBA source at Mode3 / Merge1 / Horizontal Length 50 / Rotation 0 / Brightness Gain 0.1 is raw-active-byte exact across the current Windows exported Smart owner and the Mac public Classic and Smart owners at PF8, PF16, and PF32. Input storage/headers and 12-byte row padding remain immutable.

Rotation 1, source mutation, layout/extent/rowbytes/depth mutations, a partial request, and every parameter checkout/checkin ordinal fail closed with output untouched. No install or After Effects launch is performed.

Verify: `python3 tools/emulation/test_olmkirakira_mode3_32x18_public_closure_20260814.py`
