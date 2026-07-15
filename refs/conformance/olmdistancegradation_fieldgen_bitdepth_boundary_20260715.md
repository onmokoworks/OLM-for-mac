# OLMDistanceGradation Field-Generation Bit-Depth Boundary

Question: Does Mac field generation itself branch on pixel depth before normalization?

## FACT

- Mac `dt_to_normalized` calls the shared core field generator `1` time(s); its body has no `pixel_size` branch.
- Mac depth dispatch exists at render entry (`[['', '16'], ['', '8'], ['8', ''], ['', '8'], ['16', ''], ['', '16'], ['', 'Float']]`), outside the field builder. The field builder does apply `threshold * ds_scale`.
- The decompiled Windows `FUN_181174760` pipeline contains distance, convert, threshold, and output-normalize stages, with no explicit 8/16/32bpc token in that function body.
- The active 8bpc typed request returned `exact_bind_failure` because `AE result missing for case_0001`; missing fields: `['ae_result_case_0001.json']`.
- The active 16bpc case-0026 typed request returned `exact_bind_failure` because `CDB did not complete for olmdistancegradation_extended__case_0026`; no raw field words are present in the local livefield manifest.
- Current Mac 16bpc residuals remain max-2 for cases 0012/0014/0024/0026 and max-3080 for case 0028.
- 32bpc DG evidence contains `174` rendered reference artifacts and zero typed field-callback artifacts.

## INFERENCE

- **Decision:** `mac_field_generation_shared_before_depth_specific_mask_and_compose`.
- The Mac field builder is shared across RenderBits dispatches; observed depth branches are outside dt_to_normalized, in source-mask selection, compose, and PF16 handling.
- The 16bpc max-2 and outlier families are not proven to originate in field generation by current evidence. The missing Windows raw field words and failed typed requests leave upstream-vs-boundary ownership open.
- The 32bpc artifacts establish rendered-reference presence only; they do not establish a typed field-generation boundary.

## Guardrails

- No PNG or EXR pixels are converted into field values.
- Windows typed-request failures are recorded as missing evidence, not as numeric facts.
- No production plugin algorithm was changed because no byte-exact field-generation defect is proven.
