# OLMSmoother2 legacy key/setup producer witness - 2026-07-16

- Verdict: `PASS_LOCAL_ACTUAL_AEX_LEGACY_KEY_SETUP_PRODUCER`
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex` SHA-256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`

## FACT

- Actual-AEX emulation reads the producer class bytes and executes `e170 -> f270 -> e3a0`.
- The bounded local row is `c=2`, `f270 append`, `e3a0 append`; the exact raw values are in the JSON.
- `e170` uses class base `+0x18`, class stride `+0x28`, and the three byte addresses recorded in the typed contract.

## INFERENCE

- The legacy producer reaches e3a0 under the observed c=2 class state; no gamma fallback is involved at this boundary.
- The local synthetic coordinates are translation-equivalent for the relative class addressing, but are not a Windows case mapping.

## Windows Typed Witness

- No same-run Windows producer return is present. The next witness is narrowed to one case/pixel and absolute RVA binding.
- Required memory contract: `class_base=[RCX+0x18]`, `class_stride=[RCX+0x28]`; bytes at `(91,841)`, `(91,840)`, and `(90,841)+byte1`; then `RAX` at e170/f270/e3a0 and vertex storage `+0x40/+0x50`.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_legacy_key_setup_producer_witness_20260716.py \
  --output-json refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.json \
  --output-md refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.md
```

Result: exit `0` when all local actual-AEX producer checks pass.

## Claims Not Made

- No Windows producer truth
- No AE exactness
- No portable compatibility
- No final-writer or PNG tuning
