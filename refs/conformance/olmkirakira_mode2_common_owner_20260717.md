# OLMKiraKira common-owner natural-lineage attempt (2026-07-17)

Status: **BLOCKED, fail-closed**
AE exact: **false**
Scope: Mac-only Unicorn execution of the checked-in Windows PE AEX.

The nearest common owner is `FUN_18114c8f0`. It reads the PF depth from
`*param4 + 0x2c`, obtains source/output worlds through the host suite at
`param4[1]`, and selects `FUN_18114d7f0` for PF32. That owner calls the Mode2
dispatch `FUN_18114f4a0`, then `FUN_18114e460`, whose PF32 loops enter
`0x18114e5d7` or `0x18114e739` and call `FUN_181230c20`.

The 1x1 PF32 attempt entered `FUN_18114c8f0` and successfully executed both
proven host world callbacks:

```text
0x18114c945 CALL R9
callback: PFWorldSuite.param4[1] slot +0x0
ABI: RCX=refcon, RDX=0, R8=&local_8a0, R9=callback pointer

0x18114c963 CALL R9
callback: PFWorldSuite.param4[1] slot +0x10
ABI: RCX=refcon, RDX=&local_8a8, R8=not assigned here (observed stale &local_8a0), R9=callback pointer
```

The input and output worlds are actual 1x1 PF32 headers with visible pixel
size 16, `rowbytes=24`, and independent 8-byte canaries. Both callback
returned pointers and both canaries are recorded in the JSON report.

Before the next boundary, the harness supplies the smallest complete table
for the fields read by `FUN_18114e860`. `FUN_1811542b0` scans
`[param1+0x8, param1+0xac)` for disk IDs and returns each match's zero-based
ordinal to checkout. The populated disk-ID order is:

```text
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,22,24,26,27,28,35
```

Selectors and defaults are sourced from
`refs/win_references/20260604_olm/OLMKiraKira/reference_manifest.json`
`case_0001`, with disk selectors grounded in
`mac/OLMKiraKira/OLMKiraKira.h`. Enum defaults are Channel=2,
Blur Mode=2, and Merge mode=1. The context time fields at `+0xe0`, `+0xe4`,
and `+0xf0` remain explicit zero defaults.

The populated entry is accepted and the scan reaches the parameter
checkout/check-in helpers. `FUN_181232760` is not a host world-suite callback,
allocator, or source-pixel fetch. Its decomp contract is:

```text
uVar1 = (**(code **)(param_1 + 8))(*(undefined8 *)(param_1 + 0xb8));
FUN_181230880(uVar1);
```

The assembly loads `RAX=[outer_context+0x8]`, loads
`RCX=[outer_context+0xb8]`, calls `RAX`, and forwards `EAX` to
`FUN_181230880`. Existing AEX/source harnesses identify this as
`PF_ParamCheckin(PF_ProgPtr refcon) -> PF_Err`; the harness installs only this
proven callback with `RCX=refcon=outer_context+0xb8` and returns
`PF_Err_NONE (0)`.

The checkout/check-in pair executes for the grounded selectors reached by the
run, with each `PF_ParamDef` zeroed to `0xb0` bytes and populated at `u+0x38`;
the JSON records selector, match-name, raw structure bytes, ABI registers,
stack time-scale, and check-in return values.

The rerun stops at the next exact unavailable boundary:

```text
FUN_181232350 +0x3b: MOV RAX,[RBX]
                     ; RBX = [outer_context+0x180]
fixture: [outer_context+0x180] == 0x0
required object: SPBasicSuite with AcquireSuite at [RBX+0x0]
required suite: PF ColorParamSuite1, acquired using suite name at 0x1814d6650,
                version 1, output pointer RSP+0x78
result: RIP=0x18123238b / UC_ERR_READ_UNMAPPED
```

The color-suite object and callback semantics were not fabricated. No natural
Mode2-to-PF32-writer lineage was claimed. The harness exits `2` and writes the machine-readable
details to
`refs/conformance/olmkirakira_mode2_common_owner_20260717.json`.
