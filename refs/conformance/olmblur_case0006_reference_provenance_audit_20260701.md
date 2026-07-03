# OLMBlur case_0006 Reference Provenance Audit

- Scope: `OLMBlur` non-Legacy 16bpc `case_0006`
- Outcome: `current-aex-export-missing`
- Reason: No same-run Windows current-AEX exported PNG is present, so the lane remains a provenance/export question rather than a reopened implementation bug.
- Recommended action: Keep OLMBlur case_0006 frozen on the Mac side and request only the precise same-run Windows current-AEX export artifact if this lane must advance.

## File Identity

| Role | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| canonical_ref | `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |
| handoff_expected | `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |
| mac_single_export | `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485331` | `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` |
| mac_batch_export | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/candidate/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485333` | `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974` |
| handoff_results_export | `handoff/ae_pixel_validation_20260618/results/bitdepth16_olmblur_exact/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485331` | `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` |
| archive_results_export | `handoff/archive/ae_pixel_validation_20260618_before_rerun_20260626_204944/results/bitdepth16_olmblur_exact/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485333` | `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974` |

- Canonical ref and handoff expected identical: `True`

## Alias Groups

- `['canonical_ref', 'handoff_expected']` share SHA `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` (2485242 bytes)
- `['handoff_results_export', 'mac_single_export']` share SHA `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` (2485331 bytes)
- `['archive_results_export', 'mac_batch_export']` share SHA `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974` (2485333 bytes)

## Result Metadata

- `handoff_result_json`: request_id=`ae_pixel_bitdepth16_olmblur_exact_20260625`, effect=`OLM Blur`, rendered_count=`6`, errors=`['olmblur__case_0003: PNG was not written']`
- `archive_result_json`: request_id=`ae_pixel_bitdepth16_olmblur_exact_20260625`, effect=`OLM Blur`, rendered_count=`6`, errors=`['olmblur__case_0003: PNG was not written']`

## Witness Points

| XY | canonical ref | Mac single export | Mac batch export | Windows current export |
| --- | --- | --- | --- | --- |
| `(29,71)` | `[725, 725, 725, 65535]` | `[727, 727, 727, 65535]` | `[727, 727, 727, 65535]` | `-` |
| `(314,14)` | `[2201, 2201, 2201, 65535]` | `[2199, 2199, 2199, 65535]` | `[2201, 2201, 2201, 65535]` | `-` |
| `(378,487)` | `[64767, 35, 35, 65535]` | `[64767, 35, 35, 65535]` | `[64769, 35, 35, 65535]` | `-` |
| `(601,598)` | `[4609, 4609, 4637, 65535]` | `[4607, 4607, 4637, 65535]` | `[4609, 4609, 4637, 65535]` | `-` |

## Point-Role Matrix

| XY | match roles | single-canonical | batch-canonical |
| --- | --- | --- | --- |
| `(29,71)` | `['mac_single_matches_mac_batch']` | `[2, 2, 2, 0]` | `[2, 2, 2, 0]` |
| `(314,14)` | `['mac_batch_matches_canonical']` | `[-2, -2, -2, 0]` | `[0, 0, 0, 0]` |
| `(378,487)` | `['mac_single_matches_canonical']` | `[0, 0, 0, 0]` | `[2, 0, 0, 0]` |
| `(601,598)` | `['mac_batch_matches_canonical']` | `[-2, -2, 0, 0]` | `[0, 0, 0, 0]` |

- overall counts: `{'mac_single_matches_canonical': 1, 'mac_batch_matches_canonical': 2, 'mac_single_matches_mac_batch': 1, 'all_split': 0}`
- witness pattern: `{'29,71': ['mac_single_matches_mac_batch'], '314,14': ['mac_batch_matches_canonical']}`
- reading: No single export artifact dominates all sampled points: batch and single-case exports each match canonical at some points and disagree at others, while the original witness pair also splits by point.

## Reading

- The canonical Windows Software reference path is fixed if the canonical and handoff files are byte-identical.
- If Windows and Mac internal witness values already agree, but exported PNG artifacts still split by path, treat the lane as provenance/export work until a same-run Windows current-AEX export exists.
- Do not reopen `mac/OLMBlur/OLMBlur.cpp` from this lane alone.

