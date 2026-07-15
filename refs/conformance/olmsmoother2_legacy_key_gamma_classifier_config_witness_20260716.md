# OLMSmoother2 legacy key/gamma classifier-config witness - 2026-07-16

- Verdict: `PASS_LOCAL_ACTUAL_AEX_LEGACY_GAMMA_CONFIG_BOUNDARY`
- Scope: checked-in actual-AEX CPU emulation only; no portable adapter is used as an oracle.
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex` SHA-256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`

## FACT

- The bounded actual-AEX rows cover c=2 append and classifier-one c=3.
- The normal cce0 config reaches mode byte 0 with `apply=0`.
- The Gamma Colors cce0 config reaches mode byte 3 with `gamma=2.1695473` and `apply=1`.
- The JSON artifact records the raw AEX-returned rows and all pass checks.

## INFERENCE

- This closes only the local classifier/config boundary and does not identify the live legacy case producer state.
- Key host setup remains unexecuted here; portable-only key simulation is deliberately excluded from compatibility evidence.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.py \
  --output-json refs/conformance/olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.json \
  --output-md refs/conformance/olmsmoother2_legacy_key_gamma_classifier_config_witness_20260716.md
```

Result: exit `0` when the actual-AEX checks pass.

## Claims Not Made

Windows/AE host binding, case mapping, AE exactness, final writeback equivalence, and portable-only compatibility.
