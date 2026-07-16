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

## FACT

The minimal `SPBasicSuite` contract was then installed at
`outer_context+0x180`. `AcquireSuite` accepts only the exact AEX request
`"PF ColorParamSuite"`, version `1`, writes a one-slot
`PF_ColorParamSuite1` at the requested output address, and `ReleaseSuite`
returns `PF_Err_NONE`. The suite's slot 0 implements the grounded
`PF_GetFloatingPointColorFromColorDef(effect_ref, PF_ParamDef*, PF_PixelFloat*)`
shape, copying the checked-out `PF_RGBColor` bytes at `PF_ParamDef+0x38` to
normalized float channels. The run records five successful acquisitions,
five color conversions, and five releases.

The existing parameter path remains intact: 25 grounded checkouts and 25
checkins execute, and both world-suite callbacks still return the 1x1 PF32
worlds with their padding canaries preserved.

The rerun stops at the next exact unavailable boundary:

```text
FUN_181231ec0 +0x7e: MOV RAX,[R14]
                      ; R14 = SPBasicSuite at [param+0x180]
request: AcquireSuite("PF Handle Suite", version 2, output RSP+0x38)
fixture: strict minimal AcquireSuite returns 1 for this unimplemented suite
result: AEX exception path at RIP=0x18123204f / UC_ERR_EXCEPTION
```

## FACT

The minimal binary-grounded `PF Handle Suite` v2 contract is now installed
alongside the retained ColorParamSuite contract. Its four suite slots are
`new(size)`, `lock(handle)`, `unlock(handle)`, and `dispose(handle)`.
The natural run accepts the exact `"PF Handle Suite"` version `2` request,
allocates one bounded 16-byte handle payload, and returns its payload pointer
from `lock`. The JSON records the suite acquisition, `new(16)`, and
`lock(handle)`. No `unlock` or `dispose` callback was reached.

The rerun stops at the next exact unavailable boundary:

```text
PF Handle Suite v2: new(16) -> lock(handle) completed
next call: FUN_181159da0 +0x4b at 0x181159deb
operation: lazy runtime singleton / TLS epoch read
result: Invalid memory read / UC_ERR_READ_UNMAPPED
```

## INFERENCE

The ColorParamSuite and the first PF Handle Suite v2 lifecycle boundary are
now crossed in the existing common-owner harness, but the natural PF32 owner
does not yet reach a typed writer. The next Mac-only action is the bounded
runtime/TLS singleton contract, not a direct writer invocation or
Python-mediated output transfer. No Windows execution, After Effects host
binding, final pixel, or AE exactness claim is made.

The harness remains fail-closed and exits `2`; the machine-readable details
are in
`refs/conformance/olmkirakira_mode2_common_owner_20260717.json`.
