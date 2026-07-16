# OLMSmoother2 case0012 post-leaf polygon boundary - 2026-07-16

- Verdict: `PASS_MAC_CASE0012_POST_LEAF_BOUNDARY`
- Case: `legacy_case_0012_gamma5_red_blue_current_aex`
- Descriptor: `92,841,1,92,842,2`
- Key: `20` (`0x14`)
- AEX: `aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`
- AEX SHA-256: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`

## FACT

- This is a bounded Mac-only comparison of checked-in actual-AEX Unicorn CPU
  emulation and the current portable `f270`/`f130` leaf path.
- The local fixture produces `e170 c=7`; the portable path produces the same
  value. The `df30` predicate is `0` in both paths.
- Direct `f270` returns low byte `1` and leaves polygon count `1`.
- The first snapshot is taken immediately after `f270` and before `f130`:
  - source RGBA: `(0.1844750345, 0.1844750345, 0.1844750345, 0.6823529601)`
  - weight: `0.3922413588`
- Direct unconditional `f130` returns low byte `1` and leaves polygon count
  `2`. The second snapshot is taken immediately after it and before `cce0`:
  - appended source RGBA: `(0.125, 0.25, 0.75, 0.625)`
  - weight: `0.1767241210`
- All descriptor, return, count, vertex payload, and weight comparisons pass at
  `1e-6`. Neither side calls `cce0`.

## INFERENCE

- For this bounded synthetic realization of the accepted descriptor and `c=7`
  predicate state, the post-`f270` and post-unconditional-`f130` polygon
  states are portable-path compatible before the composite stage.
- This local result does not identify the complete live Windows polygon state;
  it only establishes the checked-in AEX direct-call behavior for the stated
  fixture and the corresponding portable behavior.

## Reproduction

```sh
tmp=$(mktemp -d)
clang++ -std=c++17 -O2 \
  -I cli/OLMSmoother2/shim -I mac/OLMSmoother2 \
  tools/emulation/olmsmoother2_case0012_post_leaf_20260716.cpp \
  -o "$tmp/post_leaf"
python3 tools/emulation/test_olmsmoother2_case0012_post_leaf_20260716.py \
  --adapter "$tmp/post_leaf" \
  --output refs/conformance/olmsmoother2_case0012_post_leaf_20260716.json
```

## Claims Not Made

- No After Effects host execution or exact host ABI claim.
- No live Windows post-`f130` polygon capture.
- No `AE exact` claim.
- No production, descriptor-scanner, leaf-math, or PNG-tuning change.
