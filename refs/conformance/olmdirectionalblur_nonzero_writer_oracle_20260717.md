# OLMDirectionalBlur nonzero writer oracle (2026-07-17)

- Status: `pass`
- Exact match: `True` across `256` typed `PF_Pixel8` words.
- Fixture: checked-in `case_0001_before_effects.png` crop `[556, 316, 572, 332]`; no host pixels were fabricated.
- AEX chain: real `0x180006980` populate callback, real `FUN_180001ec0`, then real `0x180006b30` writer callback under the existing natural followup harness.
- Oracle: temporary source-included helper calling the production Mac `OLMDirectionalBlurTestRenderWorld` dispatcher with the same decoded RGBA bytes and parameter contract.
- Scope: local executable differential only; no Windows/AE claim and no production or ledger edits.
