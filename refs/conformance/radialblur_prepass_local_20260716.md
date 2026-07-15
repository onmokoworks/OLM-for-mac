# radialblur_prepass_local_20260716

- Status: `comparable_stage_pass`.
- Result: `comparable_stage_pass`.
- Scope: bounded local evidence; no AE-exact claim.
- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- CLI source SHA-256: `71d677115a909790894cdfa7a303caa7e04b263a8c27089382cb04a88ca3098b`
- Adapter source SHA-256: `28f85b5256c960d921e442954e1a8e867354a8f3c5214cc7f0caa4cca0dd8523`
- Adapter binary SHA-256: `975b8e6df90aa0d534cd2f07268924fb541c6b4f398dfcb0a597fcd25b6e0ef7`

## Executed boundary

The runtime-compiled adapter source-includes `cli/OLMRadialBlur/main.cpp` and accepts arbitrary positive typed-polar geometry with `row_stride=width*4`, exact `width*height*4` float32 RGBA values, and exact `width*height` validity bytes. A local synthetic `1x4` payload passes the validation/echo gate. The AEX run supplies the complete four-cell/four-row plane, four validity bytes, and same-run outer base span.

## Boundary

No blocker remains at this bounded prepass/scatter/collapse boundary. Both Repeat Border runs pass every compared stage at the configured one-ULP ceiling.

Source loci under the recorded CLI source hash: the float helper, typed-input contract, polar/span planes, shared prepass/scatter operation, and typed export before final inverse sampling. The Ghidra call mapping is preserved in the JSON: polar RGBA `ctx+0x38`, scatter span gate `ctx+0x40`, filtered alpha `ctx+0x48`, prepass factor `ctx+0x50`, width `iVar22=1`, row window `floor(chunk*fVar35)` to `floor(next*fVar35)`, accum RGBA `ctx+0x3c940`, and max alpha `ctx+0x3c948`.

The old two-cell display limit was removed after Ghidra and same-run scatter arguments proved the `1x4` allocation. Repeat Border 0 and 1 now match at injected polar RGBA, filtered source alpha, accumulated RGBA, max alpha, and collapsed RGBA. This is a bounded actual-AEX/portable differential, not an AE-exact claim.
