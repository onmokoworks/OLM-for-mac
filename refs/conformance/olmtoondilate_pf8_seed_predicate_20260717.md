# OLMToonDilate PF8 Seed Predicate - 2026-07-17

## Result

- Status: **PASS_PF8_SEED_PREDICATE_DISCRIMINATED**
- AEX: `aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex`
- Worker/helper: `0x1801a6150` / `0x1801ac880`
- Execution target: checked-in AEX under local Unicorn; no PNG, production, host, or AE-exact claim.

## FACT

- Fixture is 5x1 PF8 ARGB, radius 1, with zero neighbors.
- x1 is paired at RGB `[255,40,80]` with alpha 254 versus 255; x3 is an alpha255 control.
- Raw output is captured as the first memory read after native worker return.
- Provenance/hash gate: `{"aex_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3", "expected_aex_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3", "expected_worker_function_sha256": "500bda28032d0ecf005415cc9488e8348c1b20e5b99f7c0c61f976cbae10f647", "function_hash_size": 256, "worker_address": "0x1801a6150", "worker_function_sha256": "500bda28032d0ecf005415cc9488e8348c1b20e5b99f7c0c61f976cbae10f647"}`
- Gates: `{"both_helpers_observed": true, "both_workers_returned": true, "padding_preserved": true, "paired_alpha_only_difference": true, "provenance_gate_passed": true, "raw_captured_immediately_after_return": true, "x3_opaque_control_retained_or_propagated": true}`

## MODEL COMPARISON

- `alpha == 255`: opaque seeds only; copied bytes remain raw.
- `alpha >= 254` plus conversion: threshold seeds and partial-alpha RGB is converted with integer `(channel*alpha+127)//255`.
- See the paired JSON for exact output bytes and both model comparisons.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/probe_olmtoondilate_pf8_seed_predicate_20260717.py
```
