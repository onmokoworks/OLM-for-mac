# OLMDirectionalBlur Iterate8 Natural Pre-Render Follow-up

This evidence is produced by the new follow-up harness. It records the exact
natural early-return owner and records a first distinct write only when a real
overlapping memory event is observed. A blocked run is a successful
fail-closed verification result, with the write field left `null`.

The pre-render owner is `FUN_180007bd0`. It reads depth from
`param_6[0]+0x2c` into `R12W`; the 8bpc branch is selected only when `R12W == 8`.
The input checkout, output checkout, and `FUN_180006c50` parameter materializer
must each return zero. A nonzero value branches to the common return before the
8bpc worker can call PF Iterate8.

The harness uses the natural 16x16 crop and angle-0 8bpc settings from the
continuation harness and invokes the real AEX populate callback at
`0x180006980`. It records only writes overlapping the selected
`params+0x8090` cell. The output callback is deliberately not invoked because
the witness stops before that stage; it does not synthesize pixel output or
edit production or ledger files.

The earlier `0x820000e0` fault decodes to the second installed PF Iterate8
stub: callback slot `0x82000000 + 0x0e * 0x10`, label `PF_Iterate8`. The
populate callback continuation is now grounded through the loader's mapped
`0x90000000` return trampoline under an outer context save/restore, so that
synthetic stub fault is gone.

In the current run, all three render-entry gates are zero and the first PF
Iterate8 plus the first actual `FUN_180001ec0` transform checkpoint are reached.
The second, downstream Iterate8 is not reached: execution stops at the next
observed actual-transform boundary `0x180002064` inside `FUN_180001ec0`, with
zero rowdriver callbacks and no downstream callback. The fixture's raw
diagnostic still labels this generic return `pre-render-return`; the sidecar
normalizes it to `actual-rotate-helper-boundary`. This is no longer a
depth/checkout return and no first writer-plane write is observed. The report
therefore remains `status: blocked` with a null write field.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717.py
```
