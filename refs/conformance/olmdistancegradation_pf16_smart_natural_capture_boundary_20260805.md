# OLMDistanceGradation typed natural Smart capture boundary

- Status: `PASS_TYPED_SMART_NATURAL_PRODUCTION_EXACT`.

The authoritative audit is now fail-closed and executable. It verifies the
same-state command `0xe` then `0xb` chain for both typed branches, rather than
accepting an inventory-only or gated probe result.

PF16 naturally reaches `FUN_181170280`, invokes 187 actual callbacks, preserves
rowbytes 146/150 and all padding, and matches production for all 1,650 output
bytes. Its active SHA-256 is
`40033c11b790b2b93832553dc9e422b5bd6293f2965bf593df4b0f14c58c252f`.

PF8 independently reaches `FUN_181170380`, invokes 187 actual callbacks,
preserves rowbytes 75/79 and all padding, and matches production for all 869
output bytes. Its active SHA-256 is
`4ae34c2cfbdf2ccfa6d3fa18887ec36b0f5e3582166c148a7cf7c1a346fe9fc3`.

Both captures retain a 0x100-byte pre-render object and result/max rectangles
`[0, 0, 17, 11]`. The audit also verifies the production helper connections
and reruns classic PF8, PF16, and controlled/zero PF32 exact regressions. A
direct typed-wrapper call, classic fixture reuse as a Smart oracle, or PF16
quantization reused for PF8 cannot satisfy the gate.
