# OLMDistanceGradation PF8 Smart natural exact

The actual AEX is entered through the same-state command `0xe` then command
`0xb` chain. Clearing request byte `+0x10` bit 0 selects `FUN_181170380`, which
acquires `PF Iterate8 Suite` v1 and invokes the actual `FUN_181170870` callback
187 times for a 17x11 frame. The typed wrapper is not called directly.

The input and preseeded destination use distinct rowbytes of 75 and 79 bytes
for a 68-byte active row. All `0xA5` input and output padding remains unchanged.
The retained pre-render object is 0x100 bytes, and result/max rectangles are
both `[0, 0, 17, 11]`.

The independently captured active output SHA-256 is
`4ae34c2cfbdf2ccfa6d3fa18887ec36b0f5e3582166c148a7cf7c1a346fe9fc3`.
The PF8 callback has its own byte/float truncation contract and is not routed
through PF16 quantization. For nonzero source alpha it computes alpha through
the typed float path and emits opaque-white RGB; zero source alpha retains the
preseeded field byte in RGB while alpha remains zero.

Production implements this only in `RenderSmartPF8PreseededField`. The test
compares all 869 destination bytes, including padding, with zero mismatches.
PF16 Smart remains exact for all 1,650 bytes, and the classic PF8/PF16 and PF32
fixtures remain unchanged and exact.
