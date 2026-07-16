# OLMSmoother2 legacy key producer request contract - 2026-07-16

One fresh Windows Adobe After Effects 2025 Software, 8bpc run of
legacy_case_0012_gamma5_red_blue_current_aex at (91,841), pinned to AEX SHA-256
7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7.

Bind run_id, AfterFX PID, module base, case, pixel, AEX hash, renderer, and bit
depth on every event. Hooks are absolute module_base + RVA:
FUN_18000e170 (0xe170), FUN_18000f270 (0xf270), and FUN_18000e3a0 (0xe3a0).
At e170, read qword [RCX+0x18] as class_base, qword [RCX+0x28] as
class_stride, then center b0, previous-row b0, and left-pixel b1 from the
descriptor-derived addresses.

Required from that same run: e170 c return, f270/e3a0 return low byte, vertex
count, first vertex RGBA, and weight. Missing field/hook or mixed identity is
exact_bind_failure. Final-writer bytes and PNG/export artifacts are forbidden.
