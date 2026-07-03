# OLMBlur Current Word Baseline

- Date: `2026-06-29`
- Purpose: freeze the current Mac-side witness values as historical baseline context for later OLMBlur closeout and provenance/export decisions.

## Reading

- `olmblur__case_0006` is the active non-Legacy sign-mixed one-word family.
- `olmblur__case_0007` 16bpc is the surviving Legacy one-word half-step witness after the carry-prev fix retired the old `(0,0)` blocker.
- old normalized 8bpc `case_0007` is the companion half-step witness from the live CLI binary.

## olmblur__case_0006 (16bpc)

- Family: `nonlegacy_sign_mixed_one_word`
- Candidate: `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png`
- max: `2`
- mean: `8.342978395061729e-05`
- nonzero_px: `283`
- bbox: `[29, 14, 1889, 1079]`
- max witness: `{'x': 314, 'y': 14, 'channel': 0, 'reference': [2201, 2201, 2201, 65535], 'candidate': [2199, 2199, 2199, 65535], 'delta': [-2, -2, -2, 0]}`
- Current live Mac AE non-Legacy writer is still the nearbyint/ties-to-even family at the active witnesses.
- The remaining exported residual is sign-mixed, which still forbids a blind global writer swap without Windows pre-store float evidence.

| Point | reference | candidate | witness |
| --- | --- | --- | --- |
| `(314,14)` | `[2201, 2201, 2201, 65535]` | `[2199, 2199, 2199, 65535]` | `{'x': 314, 'y': 14, 'raw': ['1100.5', '1100.5', '1100.5'], 'raw_hex': ['0x1.132p+10', '0x1.132p+10', '0x1.132p+10'], 'floor05': ['1101', '1101', '1101'], 'nearby': ['1100', '1100', '1100'], 'rounded': ['1100', '1100', '1100'], 'clamped': ['1100', '1100', '1100'], 'stored': ['1100', '1100', '1100'], 'line': 'OLMBLUR_DEBUG_POINT x=314 y=14 raw=(1100.5,1100.5,1100.5) raw_hex=(0x1.132p+10,0x1.132p+10,0x1.132p+10) floor05=(1101,1101,1101) nearby=(1100,1100,1100) rounded=(1100,1100,1100) clamped=(1100,1100,1100) stored=(1100,1100,1100)'}` |
| `(29,71)` | `[725, 725, 725, 65535]` | `[727, 727, 727, 65535]` | `{'x': 29, 'y': 71, 'raw': ['363.5', '363.5', '363.5'], 'raw_hex': ['0x1.6b8p+8', '0x1.6b8p+8', '0x1.6b8p+8'], 'floor05': ['364', '364', '364'], 'nearby': ['364', '364', '364'], 'rounded': ['364', '364', '364'], 'clamped': ['364', '364', '364'], 'stored': ['364', '364', '364'], 'line': 'OLMBLUR_DEBUG_POINT x=29 y=71 raw=(363.5,363.5,363.5) raw_hex=(0x1.6b8p+8,0x1.6b8p+8,0x1.6b8p+8) floor05=(364,364,364) nearby=(364,364,364) rounded=(364,364,364) clamped=(364,364,364) stored=(364,364,364)'}` |

## olmblur__case_0007 (16bpc)

- Family: `legacy_last_pixel_half_step`
- Candidate: `refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/olmblur__case_0007/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0007.png`
- max: `2`
- mean: `8.969907407407407e-05`
- nonzero_px: `306`
- bbox: `[10, 7, 1859, 1060]`
- max witness: `{'x': 951, 'y': 7, 'channel': 0, 'reference': [101, 101, 101, 65535], 'candidate': [103, 103, 103, 65535], 'delta': [2, 2, 2, 0]}`
- The old Legacy (0,0) spill is retired in the current port.
- The remaining 16bpc Legacy witness is a one-word half-step split at blue raw=12544.5.

| Point | reference | candidate | witness |
| --- | --- | --- | --- |
| `(345,672)` | `[1247, 0, 25087, 65535]` | `[1247, 0, 25089, 65535]` | `{'x': 345, 'y': 672, 'raw': ['624.429565', '1.26167242e-05', '12544.5'], 'raw_hex': ['0x1.3836fcp+9', '0x1.a758d6p-17', '0x1.8804p+13'], 'floor05': ['624', '0', '12545'], 'nearby': ['624', '0', '12544'], 'rounded': ['624', '0', '12545'], 'clamped': ['624', '0', '12545'], 'stored': ['624', '0', '12545'], 'line': 'OLMBLUR_DEBUG_POINT x=345 y=672 raw=(624.429565,1.26167242e-05,12544.5) raw_hex=(0x1.3836fcp+9,0x1.a758d6p-17,0x1.8804p+13) floor05=(624,0,12545) nearby=(624,0,12544) rounded=(624,0,12545) clamped=(624,0,12545) stored=(624,0,12545)'}` |
| `(0,0)` | `[0, 0, 0, 65535]` | `[0, 0, 0, 65535]` | `{'x': 0, 'y': 0, 'raw': ['0', '0', '0'], 'raw_hex': ['0x0p+0', '0x0p+0', '0x0p+0'], 'floor05': ['0', '0', '0'], 'nearby': ['0', '0', '0'], 'rounded': ['0', '0', '0'], 'clamped': ['0', '0', '0'], 'stored': ['0', '0', '0'], 'line': 'OLMBLUR_DEBUG_POINT x=0 y=0 raw=(0,0,0) raw_hex=(0x0p+0,0x0p+0,0x0p+0) floor05=(0,0,0) nearby=(0,0,0) rounded=(0,0,0) clamped=(0,0,0) stored=(0,0,0)'}` |

## case_0007 (8bpc-old-normalized)

- Family: `legacy_last_pixel_half_step`
- Candidate: `current cli rerun via cli/OLMBlur/olmblur_cli`
- max: `1`
- mean: `1.2056327160493827e-07`
- nonzero_px: `1`
- bbox: `[488, 941, 488, 941]`
- max witness: `{'x': 488, 'y': 941, 'channel': 0, 'reference': [251, 0, 0, 255], 'candidate': [250, 0, 0, 255], 'delta': [-1, 0, 0, 0]}`
- This is the current CLI rerun from the live workspace binary, not a copied historical log.
- The pair of neighbors straddle the half-step boundary cleanly, which supports the pre-store-float-delta hypothesis over a broad structural mismatch.

| Point | reference | candidate | witness |
| --- | --- | --- | --- |
| `(488,941)` | `[251, 0, 0, 255]` | `[250, 0, 0, 255]` | `OLMBLUR_TRACE x=488 y=941 rgb=(250.499985,0.00161030458,0.00161030458) rgb_hex=(0x1.f4fffep+7,0x1.a621b6p-10,0x1.a621b6p-10) floor05=(250,0,0) nearby=(250,0,0) legacy=1 repeat=10` |
| `(488,942)` | `[251, 0, 0, 255]` | `[251, 0, 0, 255]` | `OLMBLUR_TRACE x=488 y=942 rgb=(250.500015,0.00162608409,0.00162608409) rgb_hex=(0x1.f50002p+7,0x1.aa44a8p-10,0x1.aa44a8p-10) floor05=(251,0,0) nearby=(251,0,0) legacy=1 repeat=10` |

## Next Evidence Boundary

- The pending Windows proof must capture pre-store float(s), helper/clamp output if present, and final internal word(s) at these exact witnesses.
- If Windows lands slightly below the half-step where current Mac is exactly on or slightly above it, the remaining gap is a narrow pre-store float/state difference rather than a justification for a blind global writer rewrite.
- If Windows instead shows the same pre-store float but different helper/store behavior, only then does a writer-rule change become evidence-backed.
