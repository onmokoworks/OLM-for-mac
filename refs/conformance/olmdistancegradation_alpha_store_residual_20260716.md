# OLMDistanceGradation alpha-store residual classifier

- Status: `classified_not_closed`
- Classification: `Mac-closable exclusions complete; upstream field/pre-store/store boundary remains unresolved`
- FACT/INFERENCE boundary: the measured words and local evidence checks are FACT; the boundary assignment is INFERENCE constrained by those facts.
- `AE exact` promotion: **No**.

## FACT

- Windows PF16 alpha-store words are `3268` at `case_0010 (6,40)`, `9876` at `case_0010 (901,394)`, and `28359` at `case_0011 (915,392)`.
- Retained Mac stores are `3267`, `9877`, and `28360`; Windows-minus-Mac is `+1, -1, -1`.
- Typed Mac field-bit reuse check: `True`.
- PF16 writer direct-boundary check: `True`.
- Active compose fixture writer hits: `0`.
- case_0026 missing-field-word fail-closed check: `True`.

## INFERENCE

- A single global final-writer rounding change is rejected by the sign-flipped one-word residual.
- The residual is already present at the Windows PF16 store boundary, so PNG/export is not the primary explanation; same-run true16 export is still unproven.
- Mac-side evidence cannot separate Windows field packing from compose pre-store alpha generation. The safe classification is the upstream field/pre-store/store boundary, with no production change authorized.

## 未証明点

- Windows coordinate-bound field raw words and the compose pre-store `out_a` for the three points.
- A live AE host dispatch from compose to the PF16 writer; the bounded writer census is `inactive_for_fixture`.
- Same-run true16 TIFF/EXR export values.

## 実行コマンド/結果

```sh
python3 -m py_compile tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py
python3 tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py
```

The witness exits successfully only when all referenced evidence files and typed checks are present. It writes this JSON and report without changing production source or PNG tuning.

## 変更ファイル

- `tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py`
- `refs/conformance/olmdistancegradation_alpha_store_residual_20260716.json`
- `refs/conformance/olmdistancegradation_alpha_store_residual_20260716.md`
