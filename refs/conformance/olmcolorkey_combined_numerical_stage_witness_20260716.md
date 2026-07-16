# OLMColorKey Combined Numerical-Stage Witness 20260716

- Status: **pass**
- Scope: Mac-local execution of the hash-pinned checked-in Windows binary under Unicorn versus an independent portable oracle; never AE exact.
- First divergence: `null`

## Fixture

A deterministic 5x5 RGBA8 fixture uses opaque green everywhere, an opaque red keyed center, and an opaque blue replacement center. The actual binary adapter packs those pixels as PF_Pixel8 A,R,G,B bytes. Thin is amount 1/type 3; Blur is amount 2/type 3, Direction 1 (Inside).

## Captures

- Replacement output: `[255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0]`
- Thin matte first channel: `[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- Thin boundary seed first channel: `[255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]`
- Type-3 first-channel float32 words: `['0x44344fee', '0x440e8ca1', '0x43ff0000', '0x440e8ca1', '0x44344fee', '0x440e8ca1', '0x43b44fee', '0x437f0000', '0x43b44fee', '0x440e8ca1', '0x43ff0000', '0x437f0000', '0x00000000', '0x437f0000', '0x43ff0000', '0x440e8ca1', '0x43b44fee', '0x437f0000', '0x43b44fee', '0x440e8ca1', '0x44344fee', '0x440e8ca1', '0x43ff0000', '0x440e8ca1', '0x44344fee']`
- Destination before Blur Apply: `[255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0, 255, 0]`
- Destination after Blur Apply: `[0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 0, 255, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 0]`

## Fail-Closed Gates

`{"all_stage_outputs_match": true, "hash_match": true, "imports_complete": true, "normal_returns": true, "replacement_not_pass_through": true, "replacement_write_observed": true, "suite_lifecycle_complete": true, "world_contracts_valid": true}`

Returns: `{"blur_apply": "0x0", "replacement": "0x0", "thin_boundary": "0x0", "type3_distance": "0x0"}`. Instructions: `{"blur_apply": 2642, "replacement": 178, "thin_boundary": 1045, "type3_distance": 6850}`.
The probe does not tune after a mismatch: stage comparisons are ordered replacement, Thin boundary, type-3 distance, destination-before, and destination-after, and the report retains only the first divergence classification.
