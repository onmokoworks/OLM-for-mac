# OLMSmoother2 16bpc case-01..10 AE exact

The declared Preserve-RGB 16bpc case set is Windows/Mac AE `26.3x87` exact.
Each case uses one Windows `aerender` process with an AEP-embedded
no-effect/effect-on pair, and every log proves the 16bpc depth warning,
`Preserve RGB`, `OLM EXR 32 Float`, and FLOAT32 output twice.

- Raw gates: `20/20` exact.
- Words per gate: `8,294,400`.
- Total mismatched words: `0`.
- Maximum raw-u32 delta: `0`.
- Windows AEX: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- Final Mac plug-in: `bad3472d3ce808bdd69f0fa55be493c3d2f76cd7ad8c49b519f03347b3e2cd7b`.

## Last residual

Before the fix, case-02 effect-on differed at only G `(362,670)`: Windows
stored PF16 code `2684`, Mac `2683`. Windows CDB captured cce0 G
`0x3da7b800` and PF16 ARGB words `8000 1792 0a7c 00cf`. The Mac AE trace
uniquely reconstructs the contracted ARM64 result as `0x3da7b7ff`; the
Windows `MULSS` then `ADDSS` order produces `0x3da7b800`. Routing PF16
through the existing separated scalar composite path closes the word.
A hash-identical fresh footage path was required to bypass stale AE frame
reuse without changing Adobe preferences or caches.

## Regression

- Frozen 8bpc suite: `12/12`, `max_diff=0`.
- Declared 32bpc set: fresh Mac `20/20` raw gates identical to the prior
  Mac planes already bound to the committed Windows exact record.
- The final source keeps PF8 on its original composite body.

Machine-readable evidence:
`refs/conformance/olmsmoother2_16bpc_case01_10_ae_exact_20260727.json`.
