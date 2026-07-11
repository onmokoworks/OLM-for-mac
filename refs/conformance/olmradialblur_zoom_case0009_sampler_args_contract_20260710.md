# OLMRadialBlur Zoom case_0009 Sampler-Arguments Contract

The answered target-gate return proves `EBX=x`, `R13D=y` and captures the three
requested top-row coordinates. Static disassembly shows that `+0x5e5b` occurs
before the sampler helper arguments are populated. The actual pre-call site is
`+0x5e68` (`CALL FUN_180009d80`); `+0x5e6d` is immediately after it.

Run the package-local `case_0009` once. At both sites collect x `7`, `8`, and
`24` at y `0` in the same CDB/AE process. The call record must include all
registers, `RDX` cell address/window, `RCX` pool address/window, `R8D`, `R9D`,
and stack floats at `rsp+0x28`/`rsp+0x30`. The return record must include all
registers and `RDI` cell window. No output-byte or final-plane inference is
allowed in this request.
