# OLMSmoother2 case_0004 float-to-packed boundary - 2026-07-18
## Verdict

`PASS_BOUNDED_WRITER_RULE_NEXT_SAME_RUN_FLOAT_WITNESS`

The Mac-local actual-AEX PF8 worker has a bounded typed-store rule, but the retained case_0004 Windows writer-frame tuple does not explain the retained PF8 bytes under straight, premultiplied, or unpremultiplied RGB interpretations.

## FACT

- AEX SHA-256: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- The actual PF8 worker emits A,R,G,B bytes using float32 `value * 255 + 0.5`, truncation, and clamp to `0..255`.
- Case_0004 retained frame `(0.80824906, 0.80824906, 0.80824906, 0.44156867)` emits memory bytes `71cecece`.
- The retained case_0004 Windows PF8 record is memory bytes `71e8e8e8` (`0xe8e8e871` as the logged little-endian integer).
- Case_0012 retained frame emits `00ffffff`, matching its retained Windows record `00ffffff`.

## BOUNDED RESULT

| Interpretation of case_0004 frame | Actual-AEX memory | Expected memory |
| --- | --- | --- |
| `straight` | `71cecece` | `71e8e8e8` |
| `premultiplied_rgb` | `715b5b5b` | `71e8e8e8` |
| `unpremultiplied_rgb_clamped` | `71ffffff` | `71e8e8e8` |

To emit the expected RGB byte `232`, the actual worker input must lie in `[0.9078431129455566, 0.9117646813392639)` per channel. The expected alpha byte `113` requires `[0.44117647409439087, 0.44509804248809814)`.

## NEXT MISSING WITNESS

A same-run writer-entry float4 witness is required: bind the exact case_0004 render identity and capture the four float32 bit patterns immediately at the typed PF8 worker input, alongside the final raw bytes. A post-cce0 tuple that is not the worker input cannot close this boundary.

No production source was changed and no global writeback rule was inferred from PNGs.

## Reproduction

```sh
python3 tools/emulation/audit_olmsmoother2_case0004_writeback_rule_20260718.py
python3 tools/emulation/test_olmsmoother2_case0004_writeback_rule_20260718.py
```
