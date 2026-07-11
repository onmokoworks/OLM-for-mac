# OLMBlur case_0006 AEX CPU emulation

Date: 2026-07-10

## Retraction

The earlier version of this witness called `FUN_180001ea0`. That is the
Legacy helper and was not valid evidence for non-Legacy case_0006. This report
retracts that claim. The script now calls the actual non-Legacy helpers
`FUN_180001000` and `FUN_180001980`.

## FACT

- Binary: `plugins_2025/OLMBlur.aex`.
- The Legacy worker is `FUN_180005f20`; the 16bpc Non-Legacy worker is
  `FUN_180002280` and owns the `0x1000/0x1980` helper path.
- `FUN_180001000` has the decomp signature
  `(flags, src, dst, weights, width, height64, arg7, arg8, arg9)`.
  The call sites pass `param_6` with `CONCAT44(..., height)`, so the low
  dword is the height. Assembly confirms the stack reads for the 5th through
  9th arguments at the expected Windows x64 stack slots.
- `FUN_180001980` has the decomp signature
  `(flags, src, dst, weights, width, height, arg7, arg8, arg9)`.
  Its call sites and assembly likewise confirm four register arguments followed
  by five stack arguments.
- The witness uses active-mask bytes and float RGB triplets derived from
  synthetic 16bpc words. It exercises both helpers with nonzero radius and
  nonuniform weighted values.

## DistanceGradation host-callback inspection

The existing `test_dg_fieldgen_p1b.py` mock is structurally relevant:

- context `+0x180` points to an SPBasic vtable;
- `SPBasic.AcquireSuite` returns a PF Handle Suite vtable;
- the PF Handle vtable supplies `new`, `lock`, `unlock`, and `dispose`.

That pattern is also visible in OLMBlur `FUN_180005f20`, which acquires the PF
Handle Suite through `*(param_1 + 0x180)` and calls suite methods at offsets
`+0x08`, `+0x10`, and `+0x18`. It is therefore a plausible starting harness,
but it is not sufficient evidence for invoking the full worker: the OLMBlur
context layout, the four allocation ownership contracts, and the host-backed
source/output world objects used by this AEX are not independently grounded by
the DistanceGradation mock. The full-entry blocker is specifically this
missing OLMBlur layout/ownership contract, not a generic lack of Unicorn or a
claim that the PF suite shape is impossible.

## Actual command output

Command:

```text
python3 tools/emulation/test_olmblur_case0006.py
```

Output:

```text
FACT nonlegacy_helper_result {'functions': ['0x180001000', '0x180001980'], 'abi_horizontal': 'RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height64,arg7,arg8,arg9', 'abi_vertical': 'RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height,arg7,arg8,arg9', 'input_16bpc_words': [100, 200, 300, 1000, 2000, 3000, 300, 600, 900], 'input_float_lift': 'identity word-to-float for helper isolation', 'horizontal_output_rgb_triplets': [[600.0, 1200.0, 1800.0], [360.0, 720.0, 1080.0], [600.0, 1200.0, 1800.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], 'vertical_output_rgb_triplets': [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [2575.0, 3650.0, 4725.0], [750.0, 1500.0, 2250.0], [125.0, 175.0, 225.0], [1120.0, 1640.0, 2160.0], [1200.0, 2400.0, 3600.0], [200.0, 280.0, 360.0], [2575.0, 3650.0, 4725.0], [750.0, 1500.0, 2250.0]], 'horizontal_rax': '0x20000098', 'vertical_rax': '0x0', 'instructions': 1542}
FACT nonlegacy_helpers_are_import_free True
FACT full_entry 0x180002280
FACT dg_host_pattern: DistanceGradation uses ctx+0x180 -> SPBasic vtable, AcquireSuite -> PF Handle vtable, new/lock/unlock/dispose callbacks.
INFERENCE full_entry_blocker: OLMBlur FUN_180005f20 reaches the same PF Handle shape, but its four allocation sizes/ownership and the later OLMBlur host buffers are not independently grounded; direct full-entry output would therefore remain unactionable.
INFERENCE scope: non-Legacy helpers prove shared blur arithmetic execution only; they do not claim case_0006 PNG/store equivalence.
```

## INFERENCE

Both actual non-Legacy helpers execute and produce nontrivial weighted outputs;
for example, the horizontal helper produces `[600,1200,1800]` and
`[360,720,1080]`, while the vertical helper produces `[2575,3650,4725]`.
This proves the bounded helper arithmetic and ABI path, not final case_0006
PNG equivalence. The 16bpc unpack/store remains in the blocked full worker.
