# OLMDistanceGradation raw-threshold contract

- Status: `implemented`; focused regression `pass`.
- Scope: Mac `dt_to_normalized` threshold ownership plus hash-pinned Windows helper callsites.
- Explicit limitation: **no AE-exact or full-render parity claim**. Blur output is out of scope.

## FACT

- The pinned `DistanceGradation.aex` SHA-256 is `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- At all nine checked `FUN_181174760` callsites in the three render families, `R9D` is loaded directly from config `+0xb8` or `+0xbc`; width and height are staged separately as stack arguments.
- Mac `dt_to_normalized` now passes `(float)threshold` directly to `distance_to_normalized_u8` and no longer accepts `ds_scale`.
- A compiled arm64 helper fixture using raw threshold `4` produces byte-identical float fields for caller scenarios labelled `ds_scale=1` and `ds_scale=0.5`.
- The same fixture differs when threshold `2` is supplied, proving the regression would detect reintroduced `threshold * 0.5` behavior.
- `ds` remains present in `build_distance_field` for scaled blur-size calculation. The regression checks that source ownership only; it does not exercise or classify blur output.

## INFERENCE

- Removing `ds_scale` from the private threshold-helper interface reduces the chance that downsample geometry will regain threshold ownership.
- The helper-level invariance is consistent with the pinned AEX caller contract, but it does not establish AE host staging, mask, compose, blur, writeback, or rendered-output exactness.

## Commands

```sh
tools/emulation/.venv/bin/python tools/emulation/test_dg_raw_threshold_contract_20260716.py
clang++ -std=c++17 -O2 -arch arm64 -Icore core/olmdistancegradation_fieldgen.cpp tools/emulation/test_dg_core_distance_stage.cpp -o /tmp/dg_raw_threshold_20260716_core/test_dg_core_distance_stage
/tmp/dg_raw_threshold_20260716_core/test_dg_core_distance_stage
xcodebuild -project mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj -scheme OLMDistanceGradation -configuration Debug -arch arm64 -derivedDataPath /tmp/dg_raw_threshold_20260716_DerivedData CODE_SIGNING_ALLOWED=NO build
```

## Results

- Focused source/binary/helper regression: `pass`.
- Existing arm64 DG core distance-stage test: `pass` (`286` values).
- Isolated arm64 Xcode plugin build: `BUILD SUCCEEDED`; warnings were outside the corrected helper lines.
