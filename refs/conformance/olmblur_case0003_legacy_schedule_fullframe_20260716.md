# OLMBlur Legacy case_0003 bounded schedule/full-frame probe

## FACT

- Pinned actual AEX: `plugins_2025/OLMBlur.aex` / `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`; Legacy entry `0x180005f20`.
- Exact case parameters are amount `248.600006103516`, smoothness `100`, repeat `10`, bias `1`, Legacy `1`, at `960x540`.
- With both helper bodies detoured to `RET`, the actual guest caller produced exactly `120` calls in ten `H x 6, V x 6` iterations. Captured radii: `[248, 248, 248, 248, 248, 248, 248, 248, 248, 248]`. Every call's dimensions, columns/rows, offset/pass range, radius, coefficient bytes, and pointers are retained in JSON.
- Coefficient provenance is `AEX guest caller with AexLoader host-backed Python math callbacks; not Windows CRT`. These bytes are explicitly not Windows CRT truth and were not tuned against retained outputs.
- Layer A runs the smallest two-pixel/one-output actual helper fixture for every distinct captured radius/direction. Both `2` fixtures match portable C++ byte-for-byte under a `3,000,000` instruction cap.
- The dependency reaches beyond the frame, so Layer B runs the complete `960x540` composition only in compiled native portable C++. It preserves the captured call schedule and coefficient bytes and completed in `16.718` seconds (wall `16.782`; cap `300`).
- All `20` known residual coordinates retain pre-store float32 bits and grounded PF16 writer predictions. Predictions match the pinned Windows RGB at `20/20` points. The authoritative current Mac verifier retains words for its first `10` samples, where predictions match `0/10`; the remaining Mac words are explicitly unavailable.
- Current 16bpc Legacy float-exp generation differs from the captured coefficient words at `16/4970` positions, split by iteration as `[0, 0, 0, 0, 2, 2, 4, 6, 2, 0]`. The bounded double-exp-to-float candidate matches `4970/4970`; for already-exact Legacy `case_0007`, it changes `0/110` coefficient words. The 8bpc and 32bpc Legacy workers are outside this candidate's scope.
- No actual full-frame x86 worker, Windows, NAS, SSH, or AE execution occurred.

## Witnesses

- `(936,1)` float32 `[2845.499755859375, 0.0, 0.0]`, bits `['0x4531d7ff', '0x00000000', '0x00000000']`, predicted RGB `[2845, 0, 0]`, Mac ARGB `[32768, 2846, 0, 0]`, Windows ARGB `[32768, 2845, 0, 0]`.
- `(739,2)` float32 `[2857.499755859375, 0.0, 0.0]`, bits `['0x453297ff', '0x00000000', '0x00000000']`, predicted RGB `[2857, 0, 0]`, Mac ARGB `[32768, 2858, 0, 0]`, Windows ARGB `[32768, 2857, 0, 0]`.
- `(23,36)` float32 `[2850.499755859375, 0.0, 0.0]`, bits `['0x453227ff', '0x00000000', '0x00000000']`, predicted RGB `[2850, 0, 0]`, Mac ARGB `[32768, 2851, 0, 0]`, Windows ARGB `[32768, 2850, 0, 0]`.
- `(59,76)` float32 `[2852.49951171875, 0.0, 0.0]`, bits `['0x453247fe', '0x00000000', '0x00000000']`, predicted RGB `[2852, 0, 0]`, Mac ARGB `[32768, 2853, 0, 0]`, Windows ARGB `[32768, 2852, 0, 0]`.
- `(640,85)` float32 `[2865.499755859375, 0.0, 0.0]`, bits `['0x453317ff', '0x00000000', '0x00000000']`, predicted RGB `[2865, 0, 0]`, Mac ARGB `[32768, 2866, 0, 0]`, Windows ARGB `[32768, 2865, 0, 0]`.
- `(383,124)` float32 `[2871.49951171875, 0.0, 0.0]`, bits `['0x453377fe', '0x00000000', '0x00000000']`, predicted RGB `[2871, 0, 0]`, Mac ARGB `[32768, 2872, 0, 0]`, Windows ARGB `[32768, 2871, 0, 0]`.
- `(204,179)` float32 `[2860.499755859375, 0.0, 0.0]`, bits `['0x4532c7ff', '0x00000000', '0x00000000']`, predicted RGB `[2860, 0, 0]`, Mac ARGB `[32768, 2861, 0, 0]`, Windows ARGB `[32768, 2860, 0, 0]`.
- `(250,213)` float32 `[2862.49951171875, 0.0, 0.0]`, bits `['0x4532e7fe', '0x00000000', '0x00000000']`, predicted RGB `[2862, 0, 0]`, Mac ARGB `[32768, 2863, 0, 0]`, Windows ARGB `[32768, 2862, 0, 0]`.
- `(273,218)` float32 `[2864.499755859375, 0.0, 0.0]`, bits `['0x453307ff', '0x00000000', '0x00000000']`, predicted RGB `[2864, 0, 0]`, Mac ARGB `[32768, 2865, 0, 0]`, Windows ARGB `[32768, 2864, 0, 0]`.
- `(273,221)` float32 `[2864.499755859375, 0.0, 0.0]`, bits `['0x453307ff', '0x00000000', '0x00000000']`, predicted RGB `[2864, 0, 0]`, Mac ARGB `[32768, 2865, 0, 0]`, Windows ARGB `[32768, 2864, 0, 0]`.
- `(298,228)` float32 `[2866.499755859375, 0.0, 0.0]`, bits `['0x453327ff', '0x00000000', '0x00000000']`, predicted RGB `[2866, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2866, 0, 0]`.
- `(227,278)` float32 `[2861.499755859375, 0.0, 0.0]`, bits `['0x4532d7ff', '0x00000000', '0x00000000']`, predicted RGB `[2861, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2861, 0, 0]`.
- `(564,281)` float32 `[2870.499755859375, 0.0, 0.0]`, bits `['0x453367ff', '0x00000000', '0x00000000']`, predicted RGB `[2870, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2870, 0, 0]`.
- `(165,345)` float32 `[2858.499755859375, 0.0, 0.0]`, bits `['0x4532a7ff', '0x00000000', '0x00000000']`, predicted RGB `[2858, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2858, 0, 0]`.
- `(165,346)` float32 `[2858.499755859375, 0.0, 0.0]`, bits `['0x4532a7ff', '0x00000000', '0x00000000']`, predicted RGB `[2858, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2858, 0, 0]`.
- `(129,403)` float32 `[2856.499755859375, 0.0, 0.0]`, bits `['0x453287ff', '0x00000000', '0x00000000']`, predicted RGB `[2856, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2856, 0, 0]`.
- `(362,406)` float32 `[2870.499755859375, 0.0, 0.0]`, bits `['0x453367ff', '0x00000000', '0x00000000']`, predicted RGB `[2870, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2870, 0, 0]`.
- `(362,408)` float32 `[2870.499755859375, 0.0, 0.0]`, bits `['0x453367ff', '0x00000000', '0x00000000']`, predicted RGB `[2870, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2870, 0, 0]`.
- `(756,425)` float32 `[2856.5, 0.0, 0.0]`, bits `['0x45328800', '0x00000000', '0x00000000']`, predicted RGB `[2857, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2857, 0, 0]`.
- `(25,482)` float32 `[2850.499755859375, 0.0, 0.0]`, bits `['0x453227ff', '0x00000000', '0x00000000']`, predicted RGB `[2850, 0, 0]`, Mac ARGB `None`, Windows ARGB `[32768, 2850, 0, 0]`.

## INFERENCE

- Classification: `captured_legacy_schedule_actual_helpers_micro_exact_native_fullframe_predictions`.
- Layer A is function-level evidence for the two distinct radius/direction helper shapes under the captured callback coefficients.
- Layer B is a complete native portable prediction, not actual-AEX full-frame execution. Its retained Mac/Windows comparison localizes agreement under the declared coefficient backend but cannot establish Windows CRT coefficient equivalence.
- The coefficient A/B is a narrow source candidate supported by captured guest-caller bytes and retained Windows outputs; it still requires a fresh Mac AE 16bpc identity-bound rerun before `AE exact` promotion.
- The probe fails closed on dependency hashes, schedule count/order/partition, helper mismatch, missing inputs, malformed native output, or excessive runtime.

## Test

```text
python3 tools/emulation/test_olmblur_case0003_legacy_schedule_fullframe_20260716.py
```

## New files

- `tools/emulation/probe_olmblur_case0003_legacy_fullframe.py`
- `tools/emulation/probe_olmblur_case0003_legacy_fullframe.cpp`
- `tools/emulation/test_olmblur_case0003_legacy_schedule_fullframe_20260716.py`
- `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.json`
- `refs/conformance/olmblur_case0003_legacy_schedule_fullframe_20260716.md`
