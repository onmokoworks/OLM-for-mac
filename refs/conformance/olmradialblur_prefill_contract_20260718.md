# OLMRadialBlur Prefill Focused Contract - 2026-07-18

## Decision

This is internal/CLI evidence only. It does not support an AE exactness claim
and does not support production promotion. The complete internal PF32 frame is
exact against the retained actual-AEX continuation oracle. AE exact is NOT
established; Mac AE versus Windows AE Software remains unresolved.

## FACT

- Current source under test: `mac/OLMRadialBlur/OLMRadialBlur.cpp`
  `7d949919ba9bb1351969274f6f49cc1c6aceb088585043c1f7b128daeea11f38`
- Pinned AEX: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
  `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- Pinned checkpoint for prefill comparison:
  `<temporary>/olmradialblur_a9d0_boundary_nway_20260718/nway_merged_at_normalization_20260718.aexcp`
  `480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909`

- Focused sampler contract still passes against the pinned actual-AEX oracle
  `refs/conformance/olmradialblur_border_sampler_semantics_actual_aex_20260716.json`
  (`7fa8b8e50148e24a08102c26424e54d7c1eaf68f84508479609e038d2b4134e1`).
  Exact vectors:
  - `left_loose_window:non_repeat` eligible `1`, words
    `0x3e6147ae,0x3ea3d70b,0x3ed70a3e,0x3f000000`
  - `left_loose_window:repeat_border` eligible `1`, words
    `0x3e6147b0,0x3ea3d70c,0x3ed70a40,0x3effffff`
  - `top_loose_window:non_repeat` eligible `1`, words
    `0x3e124925,0x3e78af8a,0x3eaf8af8,0x3f333334`
  - `top_loose_window:repeat_border` eligible `1`, words
    `0x3e124924,0x3e78af8a,0x3eaf8af8,0x3f333334`
  - `interior_control:non_repeat` eligible `1`, words
    `0x3eb5c290,0x3ed9999a,0x3efd70a4,0x3f000000`
  - `interior_control:repeat_border` eligible `1`, words
    `0x3eb5c290,0x3ed9999a,0x3efd70a4,0x3f000000`

- Focused Zoom weight contract still passes on both `arm64` and `x86_64`.
  For `ZoomGaussianWeights(1717)`, both architectures emitted count `1717`
  and SHA-256
  `82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8`.
  For `ZoomGaussianWeights(1)`, both emitted `0x3f800000`.

- A direct temporary production-helper probe against the current source and the
  pinned AEX helper verified AEX-compatible scalar paired sincos at
  `0/3600` words.
  - Angles: `1800`
  - Compared words: `3600`
  - Word mismatches: `0`
  - Sin mismatches: `0`
  - Cos mismatches: `0`
  - Packed sin/cos SHA-256:
    `c03fc7912a15288b0c650f8b4d1dffa662248d58da5508c68c2cf5c2a97faa98`
  - `step_rad_f32_word`: `0x3b64c388`

- The focused AEX-sincos prefill candidate confirms the old two-byte
  eligibility miss was solely trig-backend-related.
  - AEX-trig candidate mask SHA-256:
    `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`
  - AEX-trig candidate differing bytes vs retained checkpoint mask:
    `0/1,987,200`
  - Native helper mask SHA-256:
    `75ecbe770a3ee9036bbe60d0da9c1ed43f2ab908a26d04fb38f6fc53a9c29b33`
  - Native helper differing bytes vs retained checkpoint mask:
    `2/1,987,200`
  - Native-only differing cells were the prior
    `(angle900,r962)` and `(angle1350,r542)` offsets.

- Focused production prefill comparison now passes exact.
  - Eligibility SHA-256 expected/actual:
    `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`
  - Eligibility counts expected/actual:
    `0=565113`, `1=1422087`
  - Eligibility differing bytes:
    `0/1,987,200`
-  Preblur SHA-256 expected/actual:
    `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`
  - Preblur differing bytes:
    `0/31,795,200`

- Newly proven production exact chain for `case_0009`:
  - Eligibility SHA-256: `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`
  - Preblur SHA-256: `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`
  - `+0x40` span SHA-256: `2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f`
  - `+0x50` source scalar SHA-256: `13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce`
  - 1717-entry Zoom weight SHA-256: `82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8`
  - Normalized postblur SHA-256: `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
  - Final internal PF32 frame SHA-256: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
  - Final internal PF32 comparison: `0/33,177,600` differing bytes,
    `0` differing float words, `0` differing pixels.
  - Eligibility, preblur, span, source scalar, normalized postblur, and final frame all
    compare with zero differing bytes at their established geometries.

- The last residual localized to `FUN_18000A850` negative-angle wrapping. The
  AEX adds its embedded double constant `0x1.921fb53c8d4f1p+2`
  (`6.2831853`), not a correctly rounded mathematical `2*pi`. Binding that
  exact constant closed the final `144,584` differing bytes.

- The focused prefill test now writes PF32 input by multiplying RGBA with the
  rounded float32 `1/255` constant before ARGB reorder. The test comment
  records that float division differs by one ULP for values such as `58` and
  `62`.

## INFERENCE

- The PF32 source-harness correction from float division to
  multiply-by-rounded-`1/255` is consistent with the previously reported
  `32,005`-byte / `1`-ULP preblur residual no longer appearing once the trig
  helper is AEX-compatible.
- The focused prefill gates are now closed: sampler vectors, Zoom weights,
  paired sincos, eligibility mask, and preblur plane are all exact under the
  current local source and pinned checkpoint/AEX identities.
- The exact internal chain now reaches the complete PF32 frame after final
  inverse sampling. The remaining boundary is Mac AE host output versus the
  Windows AE Software reference; AE exact is NOT established.

## Next Gate

Mac AE host render versus the Windows AE Software reference.

## Commands

```sh
python3 tools/emulation/test_olmradialblur_sampler_contract_20260718.py
python3 tools/emulation/test_olmradialblur_zoom_weights_contract_20260718.py
python3 tools/emulation/test_olmradialblur_prefill_eligibility_20260718.py
python3 tools/emulation/test_olmradialblur_case0009_pf32_residual_1313.py
python3 tools/emulation/test_olmradialblur_prefill_aex_sincos_candidate_20260718.py
python3 - <<'PY'  # temporary production-helper vs AEX paired-sincos word probe
...
PY
```

Observed exit codes:

- sampler contract: `0`
- zoom weights contract: `0`
- prefill eligibility contract: `0`
- PF32 residual localizer: `0`
- AEX-sincos prefill candidate: `0`
- temporary production-helper sincos word probe: `0`

## Claims Not Made

- AE exact is NOT established.
- No production promotion.
- No claim that Mac AE host output matches Windows AE Software yet.
