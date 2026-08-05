# OLMDirectionalBlur Type 3 Layer Size Contract

- Status: `pass`.
- A 12x12 Layer and a 20x20 Layer were each checked out naturally against a 16x16 source.
- Both actual-AEX runs stopped after the populate callback, with zero rotate calls and no complete output callback.
- Production rejects the same dimension mismatch through its exact gate.
- There is no crop/clamp/local-coordinate rule to port for unequal dimensions in this bounded PF8 path: the AEX rejects the geometry before field construction.
- Consequently no actual-AEX full frame exists for unequal size; claiming pixel exactness would be fabricated. Mac AE behavior remains unclaimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_size_contract_20260805.py`
