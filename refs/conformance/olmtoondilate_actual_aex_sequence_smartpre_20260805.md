# OLMToonDilate Actual-AEX Sequence + SmartRender — 2026-08-05

- Status: **PASS_SEQUENCE_AND_SMARTPRE_ENTRY**
- Sequence setup allocates and retains a 0x90-byte handle at out_data+0x28.
- Probe-local AEGP Utility v13 slot +0x48 assigns plugin ID 77.
- Command 0x17 invokes checkout_layer and copies distinct result/max rectangles exactly.
- Command 0x18 independently dispatches PF8/PF16/PF32. Integer-radius padded partial worlds through radius 4 and three independent fractional cases are typed-byte exact.
- Radius 2.01 is also exact after SmartPreRender for downsample_x 1/1, 1/2, and 2/1 at every depth, yielding effective radii 3, 2, and 5. Static worker disassembly identifies PF_InData offsets 0x11c/0x120 as the rational numerator/denominator.
- PF8 0x1, PF16 1x0, and PF32 0x0 empty-axis worlds return with backing bytes, headers, and guards unchanged. The AEX does not call the optional checkin callback.
- Public legacy Render command 0x0b dispatches to constant-zero stub FUN_1801a7840. Radius 0/2.01 at PF8/PF16/PF32 leave params and worlds untouched without suite or callback activity.
- Real AE host execution remains a separate boundary.
