# OLMDistanceGradation PF32 owner executable probe

- Status: owner completed and intermediate field captured; final PF32 exact is not yet claimed.
- AEX entry: `FUN_181172a10`.

The first executable owner-level Unicorn probe establishes the six-argument ABI needed to supply the two stack-resident owner pointers. Omitting them faults at `0x181172a6c`; supplying mapped input/owner state reaches the first indirect callback at `extra.vtable+0x10`.

The probe now implements checkout/checkin and records the exact slot sequence `2,3,4,6,5,7,8,1,9,10,11,12`; callback argument 6 is at entry `RSP+0x30`. `PF ColorParamSuite` acquisition and the float-color callback execute for slots 7 and 8. Slot 7 is fail-closed as ARGB float `[1, 28/255, 0, 238/255]`.

It also distinguishes `PF Handle Suite` and reaches correctly sized 17x11 allocations, including the 748-byte scalar field buffer. Two probe-local OpenCV TLS singleton getters (`0x181187e20`, `0x181187f50`) return one zero-initialized, mapped 32-byte lifetime object. This is sufficient for the owner-level `cv::Mat` construction path while leaving the operation detours and pixel math untouched.

With that shim, the owner completes in 39,857 instructions, reaches `FUN_181174760`, and captures its returned `11x17` float field: 187 words, SHA-256 `13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf`. Mat header dimensions, the 748-byte field allocation, TLS object size/initialization, and field return address are retained in the JSON event stream.

The machine-readable run log is `olmdistancegradation_pf32_owner_probe_20260805.json`; rerunning `tools/emulation/probe_olmdistancegradation_pf32_owner_20260805.py` reproduces the callback and exact fault RIP.

No PF8/PF16 staging or callback is used, and no production/AEXCompat change is justified by this partial run.
