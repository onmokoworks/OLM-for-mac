# OLMDirectionalBlur Actual Populate Checkpoint

- Status: `pass` for the bounded callback checkpoint.
- The fixture's `model_populate` substitution was removed at runtime and replaced with the actual AEX callback `0x180006980` using the grounded `(params, x, y, source_pixel)` ABI.
- The natural 26x26 plane state was reached. The actual callback populated `params+0x8078`; the separate writer buffer at `params+0x8090` was captured before downstream copy/rotation.
- Execution stopped immediately after that capture. The PF Iterate8 continuation was not synthesized or recovered; this is the first unresolved boundary.
- No production or ledger files were edited. No Windows values or AE-exact claim are made.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_actual_populate_checkpoint_20260717.py
```
