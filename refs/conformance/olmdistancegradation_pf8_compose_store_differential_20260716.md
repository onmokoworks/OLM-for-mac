# OLMDistanceGradation PF8 compose/store differential

- Status: `pass`
- Scope: **compose/store only; not AEX field generation**.
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; hash pin match: `True`.
- Fixture: `1024x512`, rowbytes `4096`, entry `B+0x1170870`.
- The three points use identical injected Mac-side field and source ARGB bytes in both lanes.

## FACT

- Actual-AEX PF8 callback execution and the portable/current Mac compose/store model were run in the same local test.
- The report records field/source addresses and bytes, pre-U8 compose floats, converted bytes, and final output bytes.

## INFERENCE

- A passing result bounds agreement to compose/store for these injected inputs; it does not validate AEX field generation or AE-host output.
- A hash mismatch or any missing stage/mismatch leaves the result `fail_closed`.

## Smoke

- Command: `python3 tools/emulation/test_dg_pf8_compose_store_differential_20260716.py`
- Result: `pass`.
