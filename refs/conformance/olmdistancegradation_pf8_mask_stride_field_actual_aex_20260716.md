# OLMDistanceGradation PF8 mask/stride/field differential

- Status: `pass`
- Scope: **PF8 alpha-to-mask, row-stride, and field-helper compatibility only; not AE exact**.
- Fixture: `17x11`, PF8 input/output rowbytes `80`, zero alpha at `(0,5)`, `(8,5)`, `(16,5)`.
- Parameters: raw threshold `4`, `param8=0`, `ds_scale=0.5`; field threshold remains raw `4`.

## Results

- Visible mask matched all `187` samples: `True`.
- Mac source-linked field vs hash-pinned actual-AEX: `187/187` float32 words exact.
- Mac source-linked field vs independent OpenCV 4.5.5: `187/187` float32 words exact.
- Actual-AEX vs independent OpenCV 4.5.5: `187/187` float32 words exact.
- Actual-AEX detours: `['resize', 'resize', 'normalize']`; callback counts: `{"PFHandle.dispose": 8, "PFHandle.lock": 8, "PFHandle.new": 8, "PFHandle.unlock": 8, "SPBasic.AcquireSuite": 16, "SPBasic.ReleaseSuite": 16, "cv::dist_transform": 1, "cv::normalize_minmax": 1, "cv::resize_same_shape": 2, "cv::threshold": 1}`; import counts: `{"VCRUNTIME140.dll!memset": 16}`.
- Padding mutations: input `0/132` (`0xA5`), mask `0/33` (`0xB6`), output `0/132` (`0xCD`); unchanged: `True`.
- Undersized input, mask, and output row layouts all rejected: `True`.
- All fail-closed guards: `{"all_187_fields_exact": true, "callbacks_match": true, "detours_match": true, "identity_match": true, "imports_match": true, "input_padding_unchanged": true, "input_unchanged": true, "invalid_layouts_rejected": true, "layout_match": true, "mask_match": true, "mask_padding_unchanged": true, "output_not_identity_sentinel": true, "output_padding_unchanged": true}`.

## Boundaries

- The harness reads current PF8 mask semantics and source-links the current portable field core. It does not enter compose, pixel store, EDT investigation, blur, SmartRender, or an After Effects process.
- The actual-AEX result is a direct `FUN_181174760` emulation-path helper witness using the existing detours. It is not a full AE render claim.
- The JSON records the full visible mask, all 187 three-way float32 samples, anchor samples, identities, execution counts, and sentinel gates.

## Direct Test

- Command: `tools/emulation/.venv/bin/python tools/emulation/test_dg_pf8_mask_stride_field_actual_aex_20260716.py`
- Result: `pass`.
