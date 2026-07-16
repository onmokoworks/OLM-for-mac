# OLMKiraKira FilterEngine size/anchor lineage

Date: 2026-07-17

## Result

The actual-AEX CPU run reaches `FUN_1812b98e0` and stops at the unmodified
`cv::FilterEngine::init` assertion. The object is in `RDI`; its fields are:

```text
RDI+0x14 ksize.width = -2147483648 (0x80000000)
RDI+0x18 ksize.height = 1
RDI+0x1c anchor.x = -1073741824 (0xc0000000)
RDI+0x20 anchor.y = 0
```

The immediate object-field stores are:

```text
0x1812b9b38  MOV qword ptr [RDI + 0x14],RAX  RAX=0x0000000180000000
0x1812b9b4d  MOV qword ptr [RDI + 0x1c],RAX  RAX=0x00000000c0000000
```

The static and dynamic source lineage is upstream in `FUN_181281e90`:

```text
0x18128257a  MOV dword ptr [RBX + 0x8],R15D  (R15D=0x80000000)
0x18128257e  MOV dword ptr [RBX + 0xc],R14D  (R14D=0xc0000000)
```

The runtime write watch observes those exact bytes in the `R8` source object,
which is later read by `0x1812b9b3f/0x1812b9b46`. The `RDX` source supplies the
height/anchor-y pair `1/0`. Thus the failing values are generated AEX object
geometry, not host parameter values. The parameter checkout trace is retained
as a negative control and contains no matching raw `0x80000000` or
`0xc0000000` geometry word.

## Method and limits

`tools/emulation/test_olmkirakira_filterengine_size_anchor_lineage_20260717.py`
reuses the existing natural common-owner actual-AEX execution and emits a
separate report. It checks the checked-in static assembly, captures the real
register/object/write sequence, and leaves the assertion fail-closed. No value
patch, assertion suppression, writer claim, Windows/AE execution, or AE exact
claim was made.

Evidence: `refs/conformance/olmkirakira_filterengine_size_anchor_lineage_20260717.json`.
