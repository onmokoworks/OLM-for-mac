# radialblur_prepass_local_20260716

- Status: `blocked` (fail closed).
- Result: `blocked_actual_capture_incomplete`.
- Scope: bounded local evidence; no AE-exact claim.
- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- CLI source SHA-256: `f1613bb0997e001d13eb5ef5b6f00695b82903779e0d58880e0455bf5b4c439c`
- Adapter source SHA-256: `9745c47a33ab864076d947411c7de800da5b48a0f512ca45892e9c1873e2698a`
- Adapter binary SHA-256: `406d41c7b54ebd6dd0230008664ce79af39922491332ab6c79fed7183374d241`

## Executed boundary

The runtime-compiled adapter source-includes `cli/OLMRadialBlur/main.cpp` and accepts arbitrary positive typed-polar geometry with `row_stride=width*4`, exact `width*height*4` float32 RGBA values, and exact `width*height` validity bytes. A local synthetic `1x4` payload passes the validation/echo gate. For each AEX run, the harness serializes only captured cells and leaves semantic execution blocked until the four-cell/four-row capture contract is complete.

## Boundary

The live scatter-entry capture proves angular_count=1, start_radius=0, end_radius=4, and four validity bytes. The current AEX projection still exposes only two RGBA cells and two scalar rows, so actual-AEX semantic comparison remains fail-closed until four RGBA cells, four scalar rows, and four validity bytes are captured. No values are padded or invented, and no mismatch or exactness is claimed.

Source loci under the recorded CLI source hash: the float helper, typed-input contract, polar/span planes, shared prepass/scatter operation, and typed export before final inverse sampling. The Ghidra call mapping is preserved in the JSON: polar RGBA `ctx+0x38`, filtered alpha `ctx+0x48`, span factor `ctx+0x50`, width `iVar22=1`, row window `floor(chunk*fVar35)` to `floor(next*fVar35)`, accum RGBA `ctx+0x3c940`, and max alpha `ctx+0x3c948`.

The live validity pointer is captured as four bytes, but the AEX projection currently exposes only two RGBA cells and two scalar rows. Post-prepass and post-scatter comparisons are marked `not_run`; no values are padded or invented, and there is no semantic mismatch classification or AE-exact claim.
