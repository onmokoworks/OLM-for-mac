# OLMSmoother2 32bpc case-01..10 AE exact

The declared Preserve-RGB 32bpc case set is Windows/Mac AE `26.3x87`
`AE exact` for all ten cases.

Cases 01–06, 08, and 10 were recaptured on Windows from the exact FLOAT EXR
used by Mac. Each hash-bound AEP contains two render-queue items: an
effect-disabled control and an effect-enabled output. One `aerender` process
rendered both items for each case. Its log was accepted only when it recorded
AE `26.3x87`, `OLM EXR 32 Float`, `32-bit float`, and `Preserve RGB` twice.
The unchanged Windows AEX SHA-256 is
`7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.

Raw semantic A/B/G/R FLOAT32 comparison against the final diagnostic-free
Mac plug-in
`c14bb3424b8b8ce58d09fe372a443f844319d18fec5db5ef1cfc1019e3e839eb`
produced:

| case | no-effect mismatches | effect-on mismatches | max raw-u32 delta |
| --- | ---: | ---: | ---: |
| 01 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 02 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 03 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 04 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 05 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 06 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 07 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 08 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 09 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |
| 10 | 0 / 8,294,400 | 0 / 8,294,400 | 0 |

Cases 07 and 09 retain their independent binary/runtime-grounded closeouts.
The new recapture closes the missing Windows entry contract for the other
eight cases; it does not retune the frozen 8bpc core. The old bulk effect
artifacts are superseded for this exactness decision because they did not
consume the exported Preserve-RGB EXRs as their proven effect entry.

Machine-readable input, AEP, output, log, process, and comparison hashes are
in `refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.json`.
