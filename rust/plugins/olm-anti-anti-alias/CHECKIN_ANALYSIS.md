**Conclusion — fact:** both original builds issue an extra `PF_CHECKIN_PARAM` from the ordinary parameter-loading routine at RVA **`0x115a`**, immediately after slot 2's legitimate checkin, using the same stack `PF_ParamDef`. It precedes the palette loop and image processing and propagates a nonzero result. **Inference:** the best fit is **(b), duplicated explicit cleanup that also runs on success**, resembling two consecutive `ERR2(PF_CHECKIN_PARAM(...))` statements. There is no observed refresh operation, loop repetition, or separate parameter destructor. Optimized machine code cannot conclusively exclude an inlined scope guard or establish the author's intent. Native AE's response remains unknown; accepting the duplicate is a compatibility hypothesis, not SDK-guaranteed behavior.

**Recorded call sites and parameter identities.** Fresh headless AEXCompat recordings used the originals in place, `record`'s debugger and `witness`'s owned-process lifecycle, with callback addresses read from the actual `PF_InData`. No AE, GUI, source/tool edits, or AEXCompat changes. The [observer](local/r-aaa-checkin/capture_callbacks.py) and all raw evidence are ignored scratch. The direct 2025 Smart8 [recording](local/r-aaa-checkin/2025-smart8-direct-02/calls.jsonl) loaded the AEX at `0x7ffa4c7c0000`; all five callbacks below used parameter address `0x22fbcda040`.

| Operation in parameter loader `0x1000` | Call RVA | Return-address RVA | Recorded absolute return address | Callback result |
|---|---:|---:|---:|---:|
| Checkout slot 1 | `0x109b` | `0x109d` | `0x7ffa4c7c109d` | 0 |
| Checkin slot 1 | `0x10cb` | `0x10ce` | `0x7ffa4c7c10ce` | 0 |
| Checkout slot 2 | `0x111d` | `0x111f` | `0x7ffa4c7c111f` | 0 |
| Checkin slot 2 | `0x1140` | `0x1143` | `0x7ffa4c7c1143` | 0 |
| **Duplicate checkin** | **`0x115a`** | **`0x115d`** | **`0x7ffa4c7c115d`** | **4** |

The [native declarations](declarations.json) identify slot/disk ID **1: “Number of Colors”, `PF_Param_SLIDER` (type 1), integer 0–100, default 0**; **2: “Use automatic colors”, `PF_Param_CHECKBOX` (type 4), default off**. Loader `0x1000` resizes its palette from slot 1, reuses a zeroed 176-byte stack definition for slot 2, and stores that checkbox in render state at `+0xd0`. It then reads color slots 7 onward. These are ordinary scalar controls, not checked-out layer worlds. The historical [trace-0](../../tools/autoport/local/n-antialias/trace-0.json)/[trace-1](../../tools/autoport/local/n-antialias/trace-1.json) agree: 4 propagates without suppression; suppressing exactly the unmatched callback yields 0.

**Static evidence and interpretation.** Fresh Ghidra exports: [2025 C](local/r-aaa-checkin/ghidra/exports/7de2d03edc4e4086bcff58df94430641/function.c), [2025 disassembly](local/r-aaa-checkin/ghidra/exports/7de2d03edc4e4086bcff58df94430641/disassembly.txt), [2026 C](local/r-aaa-checkin/ghidra/exports/e048948184be4b73b4316f96cf027f1b/function.c), [2026 disassembly](local/r-aaa-checkin/ghidra/exports/e048948184be4b73b4316f96cf027f1b/disassembly.txt). The relevant decompiler excerpt is identical in both:

```c
iVar4 = (*(code *)param_1[1])(param_1[0x17],local_f8);
if ((iVar4 != 0) && (iVar3 == 0)) { iVar3 = iVar4; }
iVar4 = (*(code *)param_1[1])(param_1[0x17]);
if ((iVar4 != 0) && (iVar3 == 0)) { iVar3 = iVar4; }
```

Ghidra omits the second argument on the latter indirect call; **the disassembly and live records establish it**, so the inferred C prototype must not be treated as authoritative. Both builds have byte-identical instructions over `[0x1132,0x1166)`:

```asm
; RVAs; RDI = PF_InData*, EBX = accumulated error
1132  LEA RDX,[RBP+410h]       ; same PF_ParamDef
1139  MOV RCX,[RDI+0b8h]      ; effect_ref
1140  CALL qword ptr [RDI+8]  ; legitimate slot-2 checkin
1143  TEST EAX,EAX
1145  JZ 114ch
1147  TEST EBX,EBX
1149  CMOVZ EBX,EAX
114c  LEA RDX,[RBP+410h]       ; no intervening checkout/reset
1153  MOV RCX,[RDI+0b8h]
115a  CALL qword ptr [RDI+8]  ; duplicate
115d  TEST EAX,EAX
115f  JZ 1166h
1161  TEST EBX,EBX
1163  CMOVZ EBX,EAX
1166  XOR ESI,ESI             ; palette loop begins afterward
```

**Fact:** both checkins execute whether the preceding error is zero or nonzero; only adoption of their errors is conditional. No loop back-edge creates the duplicate. The actual later suite-handler cleanup is `0xaf50 → 0xaf60` in 2025, releasing acquired named suites ([decompilation](local/r-aaa-checkin/suite-cleanup-decomp.json)); it is distinct from these callbacks. **Inference:** this supports (b) over (a)/(c); deliberate host-tolerance/refresh behavior (d) has no supporting operation or documented contract here. A source-level copy/paste mistake is plausible, not proven.

**Depths, branches, builds, and error effect.** The shared Smart render routine is `0x6380` (2025), `0x6360` (2026). Its calls to loader `0x1000` return at these **observed** RVAs:

| Build | Smart8 | Smart16 | Smart32 |
|---|---:|---:|---:|
| 2025 | `0x6466` | `0x64ca` | `0x6532` |
| 2026 | `0x6446` | `0x64aa` | `0x6512` |

The [36-run summary](local/r-aaa-checkin/matrix-summary.json) and [runner](local/r-aaa-checkin/matrix.py) bind 11×7 renders, seed 20261113, to both original hashes and the unchanged harness:

- **6 direct renders:** duplicate returns 4; loader and Smart render return 4; no accepted output.
- **24 bridge renders:** existing suppression bridge, count 0/2 × automatic colors off/on × three depths × two builds. All complete with output; the duplicate call site remains observable and returns 0. Count 2 additionally checks out/checks in slots 7/8. These are diagnostic bridge results, not direct-host passes.
- **6 controlled error renders:** after the bridge suppresses the duplicate, the debugger substitutes **37** for that callback's return in its owned process. Loader and Smart render both return **37**, and no output is accepted. This distinguishes propagation from an unrelated fixed error 4.

Static control flow places the duplicate before all empty/nonempty palette and automatic-detection image branches. Thus it occurs on **every supported Smart8/16/32 path reaching the loader**, not necessarily on earlier world-checkout failures or exceptions. Unsupported/classic selectors were not forced. In 2025, the loader result is tested at `0x6468`, `0x64cc`, or `0x6534`, branching on error to cleanup at `0x66d5` before pixel processing ([render listing](local/r-aaa-checkin/ghidra/exports/cbf884168c8643e1b5b6fe6fd8ca8fe1/disassembly.txt)). The effect is render failure rather than a measured pixel difference between two successful outputs. Merely overriding the direct host's 4 to 0 lets the plug-in return 0 but does not erase AEXCompat's recorded violation ([control](local/r-aaa-checkin/2025-smart8-zero/calls.jsonl)).

**Native AE — inference only.** The [SDK interaction-callback guide](https://ae-plugins.docsforadobe.dev/effect-details/interaction-callback-functions/#interaction-callbacks) requires balanced checkouts/checkins and says parameter fields become invalid after checkin. It documents a `PF_Err` return, but no already-checked-in result, idempotence guarantee, or refresh use. A tolerant implementation could return `PF_Err_NONE` for this already-released scalar definition; validation could instead return an error. Neither a particular nonzero code nor AE returning zero is established by this evidence. Native AE was never launched.

Provenance: 2025 SHA-256 `9ea6e2d85ab64ec6549653072a00e81315ae9c6791752a5ee634d2f599490cc0`; 2026 `c0348e4d8351a71c9cca0420cfdfcbda151413c0a013818e2cc1ebf20f05ec4e`; harness `68a251fed8131d3a32cdcbd8797aba9959be417d8da68d1e80f44d087c75e9ba`. Originals retained their hashes. All matrix process trees report verified cleanup. Owned Ghidra launcher PID **57412**, server PID **5448**, free port **54624**, and recorded descendants exited gracefully ([stop record](local/r-aaa-checkin/ghidra/reports/last-stop.json)); initial failed launcher 9316 also exited. No commits/pushes or changes outside this report and ignored scratch.
