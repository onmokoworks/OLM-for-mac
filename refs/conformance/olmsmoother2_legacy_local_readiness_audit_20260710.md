# OLMSmoother2 Legacy Local Readiness Audit

Date: 2026-07-10

## Verdict

`READY_FOR_ONE_NARROW_WINDOWS_WITNESS`; local evidence is sufficient to define
the next contract, but not to close the Mac/Windows fact. The shortest useful
producer/class-buffer witness is legacy `0012` at `(91,841)`.

No source change, package staging, global fallback tuning, or AE-exact claim is
justified by the current local artifacts.

## FACT

- The current-AEX final writer is already grounded. `0004` writes raw
  `0xe8e8e871` (`[103,103,103,113]` after AE premultiply); `0012` writes
  `0xffffff00` (`[0,0,0,0]`). The unresolved question is upstream of packing.
- The local Unicorn run passes the independent `FUN_180013630` weight-kernel
  check and exercises the actual AEX under the Win x64 ABI.
- The local `0012` descriptor is `[5,6,1,5,8,5]`, reconstructed from the
  recorded witness-relative shape. Local `FUN_18000e170` reads three class
  predicates and returns `c=2` for the witness pattern:
  `center_b0=0`, `prev_b0=1`, `left_b1=0`.
- Local `c=2` keeps `FUN_18000f270` alive and `FUN_18000e3a0` appends. In the
  three-byte sweep, the only f270 no-append family is
  `center_b0=0, prev_b0=0, left_b1=1`, yielding `c=4`.
- The exact local byte addresses are, for class base `B` and stride `S`:

  ```text
  center_b0 = *(B + y*S + x*4 + 0)
  prev_b0   = *(B + (y-1)*S + x*4 + 0)
  left_b1   = *(B + y*S + x*4 - 3)   # (x-1,y), byte 1
  ```

- The local working-struct binding is class base at `+0x18`, class stride at
  `+0x28`, current x/y at `+0x30/+0x34`; `FUN_18000e170` consumes `desc[0:2]`.
- For `0004`, the local `FUN_180013140` no-emit sweep identifies two families:
  `(iVar6 >= 4 && iVar5 >= 4)`, or `(iVar6 >= 2 && iVar5 >= 2 &&
  class_prev_b3 != 0)`. `class_prev_b3` is the left-pixel byte 3. This is a
  wider witness than `0012`, not a replacement for a Windows observation.
- The 2026-07-08 Windows returns are `failed_partial`: neither contains a
  same-run Windows Stage A bind or typed Stage B producer bytes. The 0004
  load/prewarm retry also stalled before target-module load.

## INFERENCE

- The smallest discriminant capable of classifying the first producer
  divergence is the `0012` tuple of three bytes plus observed `e170 c`. It can
  distinguish local append (`c=2`) from the local suppressing family (`c=4`)
  without needing final writer values.
- A local-only experiment cannot close the cross-platform fact. It can prove
  the AEX branch semantics, ABI, struct offsets, address arithmetic, and
  synthetic sweep coverage, but it cannot prove that reconstructed relative
  coordinates or synthetic class bytes equal the live Windows AE class buffer
  at `(91,841)`.
- Therefore local work may close a binary-semantic subfact, but only a fresh
  Windows witness-local bind can close whether the active divergence is already
  in the producer bytes/bitsum. Do not promote the local `c=2` to Windows truth.

## Exact Next Contract

Run one Windows Software-renderer request for
`legacy_case_0012_gamma5_red_blue_current_aex`, pixel `(91,841)`.

### Stage A: bind

At the first retained witness-local producer stop, return:

1. module base;
2. exact hook/breakpoint address;
3. exact case id and bound `(91,841)` coordinates;
4. live class-buffer base and stride, with the concrete pointer arithmetic for
   the three addresses above; and
5. the exact failed-bind reason if the witness stop cannot be retained.

### Stage B: read

From that same bound stop, return typed `center_b0`, `prev_b0`, `left_b1`, and
the observed `FUN_18000e170` bitsum `c`. Only after these are captured, add
`f270/e3a0` append state and cce0 pre-writeback floats.

Acceptance is `answered` only when Stage A binds the exact witness and Stage B
returns all four typed values. Final writer bytes alone, broad hit counts, or
local Mac/Unicorn values are not acceptance.

Defer `0004` until this succeeds. Its contract is the exact writer-frame
`c280`/`FUN_180013140` state: `iVar6`, `iVar5`, left-pixel byte 3, emit/no-emit,
polygon count, any helper source coordinate/sample/weight, and cce0 floats.

## Inspected Commands

```sh
sed -n '1,260p' tools/emulation/SMOOTHER2_PRODUCER_EMU_REPORT.md
sed -n '1,760p' tools/emulation/test_smoother2_producer.py
sed -n '1,260p' refs/conformance/olmsmoother2_producer_branch_table_20260707.md
sed -n '1,260p' refs/conformance/olmsmoother2_producer_branch_sweep_20260708.md
sed -n '1,260p' refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_contract_20260708.md
sed -n '1,220p' refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_return_intake_20260708.md
sed -n '1,220p' refs/conformance/olmsmoother2_current_aex_producer_bytes_return_intake_20260708.md
sed -n '1,240p' refs/conformance/olmsmoother2_current_aex_8bpc_decision.md
unzip -l refs/returns/windows/20260708_smoother2_0012_bind_then_read_failed_partial/*.zip
rg -n -C 5 'class_plane|cplane_base|cplane_stride|FUN_180013140|FUN_18000e170|FUN_18000f270|FUN_18000e3a0|build_polygon|cce0' mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp tools/emulation/test_smoother2_producer.py
rg -n -C 3 'FUN_180013140|FUN_18000e170|FUN_1800104d0|c280|cce0' disasm/OLMSmoother2_helpers_21.c.txt disasm/OLMSmoother2_port_gap_analysis.md
git status --short -- refs/conformance/olmsmoother2_legacy_local_readiness_audit_20260710.md
```

## Inspected Files

- `tools/emulation/test_smoother2_producer.py`
- `tools/emulation/SMOOTHER2_PRODUCER_EMU_REPORT.md`
- `refs/conformance/olmsmoother2_producer_branch_table_20260707.{md,json}`
- `refs/conformance/olmsmoother2_producer_branch_sweep_20260708.{md,json}`
- `refs/conformance/olmsmoother2_current_aex_8bpc_decision.md`
- `refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_contract_20260708.md`
- `refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_return_intake_20260708.md`
- `refs/conformance/olmsmoother2_current_aex_producer_bytes_return_intake_20260708.md`
- `refs/reports/runtime_trace_summary_smoother2_current_aex_0012_bind_then_read_20260708_225134.{md,json}`
- `refs/reports/runtime_trace_summary_smoother2_current_aex_producer_bytes_20260708_20260708_214839.json`
- `refs/returns/windows/20260708_smoother2_0012_bind_then_read_failed_partial/`
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
- `disasm/OLMSmoother2_helpers_21.c.txt`
- `disasm/OLMSmoother2_port_gap_analysis.md`

## Change Boundary

This audit is the only file changed by this worker. No source file was edited,
no package was staged, and no global fallback or threshold was tuned.
