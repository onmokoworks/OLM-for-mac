# OLMSmoother2 PF32 case 07 — current Mac AE host result

The current Universal `OLMSmoother2` binary (`fe782f…42c34`) completed the case-07 host path in After Effects 26.3.0x87, Software renderer, 32bpc, Preserve RGB/working space None.

The run has nonce-bound pre/post Mac process and loaded-module attestation. AE parameter readback is checked at its actual float32 storage boundary; discrete values remain exact, and color/slider values are compared by IEEE-754 float32 words rather than a tolerance.

Results:

- PF32 input-entry witness versus source EXR: 8,294,400 words, 0 mismatches.
- Mac no-effect control versus Windows Preserve RGB control: 8,294,400 values, 0 mismatches.
- Mac effect-on versus Windows Preserve RGB effect-on: 8,294,400 values, 0 mismatches.

This establishes raw FLOAT32 artifact exactness for this single case on the current Mac binary. `ae_exact_claim` remains false because the retained Windows renders do not have a same-run AfterFX process and loaded-AEX attestation bound to both outputs. It does not cover other cases, parameters, bit depths, renderers, or AE versions.

Machine-readable hashes and the exact evidence boundary are in `olmsmoother2_pf32_case07_current_mac_ae_raw_exact_20260806.json`.
