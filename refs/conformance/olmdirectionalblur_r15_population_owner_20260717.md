# OLMDirectionalBlur R15 Population-Owner Checkpoint

- Status: `blocked` by design.
- `FUN_180004A20` requests a float plane sized `width * height * 4`; the natural 16x16 fixture produces a 26x26 work plane, or `2704` bytes.
- The host-suite lock at `0x180004c79` returns the R15 buffer `0x2002ac88`, which is stored into `params+0x8090` at `0x18000562d`.
- For output `(0,0)`, the target layout is `row0=5`, `col0=5`, `stride=26`, cell index `135`, byte offset `2160`, and 16-byte RGBA cell size.
- The nearest actual AEX population callback is `0x180006980`, but the current natural fixture replaces that callback with `fixture.model_populate`; no actual AEX instruction writes the target cell in this run.
- The checkpoint therefore fails closed at the population owner. No production or ledger files were edited, and no Windows or AE-exact claim is made.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_r15_population_owner_20260717.py
```
