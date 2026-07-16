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
fixture: GS:[0x58] -> one-entry TLS table -> slot +0x04, with _tls_index=0 and epoch=-1
result: TLS read crossed; natural execution continued to 0x181162610
```

## FACT

`FUN_181162610` is not an unavailable host callback. Its grounded binary
contract constructs a `cv::Exception` from the supplied error code, message,
class, source file, and line, then calls `FUN_181162500`. That helper reaches
`_CxxThrowException`; the instruction at `0x181162672` is only the
non-returning fallback trap. A prior run reached this same exception
constructor with error code `-215`,
class `cv::details::TlsAbstraction::setData`, and source `system.cpp`; the
current one-key FLS contract crosses that boundary.

The allocation backtrace is:

```text
FUN_181157ed0 cv::Mat copy
  source geometry: rows=1, cols=1, flags=0x42ff401d
  decoded type: CV_32FC4, step=16, data bytes=16
FUN_18115eb30
  storage requests: 16, 48, 100 bytes
  selected callback: _aligned_malloc(size, 0x40)
  returns: 0x40000580, 0x40000600, 0x40000640
_aligned_free
  pointer: 0x40000580, size=16, alignment=64, lifecycle=freed
common owner
  returned at 0x18114c8f0 without reaching the PF32 typed writer callsite
```

The request is a genuine bounded `CV_32FC4` Mat allocation: rows=1, cols=1,
type `CV_32FC4`, step=16, and 16 data bytes. The allocator callback is
generalized to positive bounded requests from 1 through `0x100000`, with
power-of-two alignments from 8 through `0x1000`. Each returned pointer is
checked for the requested alignment, and `_aligned_free` validates live
ownership, recorded alignment, and double-free rejection. The run records all
three accepted sizes: 16, 48, and 100 bytes. The 48- and 100-byte allocations
remain live when the owner returns because no natural free was reached.

The one-key FLS/TLS contract then crosses successfully: `FlsAlloc` returns key
`0` for thread `0x50000000`, both `FlsGetValue(0)` calls return null, and
`FlsSetValue(0, 0x20000870)` returns `1`, followed by successful reads of the
stored per-thread value. The selector trace proves that the fixture's intended
Mode2 contract is selected: PF depth `0x20` reaches `FUN_18114d7f0`, Blur Mode
disk ID `9` is checked out at selector index `8` with raw value `02 00 00 00`,
and the PF32 mode field at `0xf0fe770` is `2`, selecting the binary value-2
branch and entering `FUN_18114f4a0`.

Mode2 then enters `FUN_181150790`, but no return or inner mode-selector branch
is observed before the harness exits. This is the first ambiguous control-flow
boundary. It is recorded fail-closed; it is not labeled as a Mode2 bypass, and
the writer is not called directly.

The exact next boundary is `FUN_181150790` entry with no observed return. No
additional host/runtime callback is entered, so the harness stops there.

## INFERENCE

The ColorParamSuite, the first PF Handle Suite v2 lifecycle boundary, the
minimal lazy TLS/runtime contract, the generalized bounded aligned allocation
contract, and the one-key FLS/TLS lifecycle are crossed in the existing
common-owner harness. Natural execution confirms Mode2 selection and stops at
the first ambiguous inner helper control-flow boundary. The natural PF32 owner
does not reach a typed writer.
No direct writer invocation or Python-mediated output transfer is used. No
Windows execution, After Effects host binding, final pixel, or AE exactness
claim is made.

The harness remains fail-closed; the machine-readable details
are in
`refs/conformance/olmkirakira_mode2_common_owner_20260717.json`.
