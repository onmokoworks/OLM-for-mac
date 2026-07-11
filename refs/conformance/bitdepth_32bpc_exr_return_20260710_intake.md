# 32bpc EXR Return Intake - 2026-07-10

Source return:
`20260710_101500__olm_32bpc_colorkey_toondilate_float_partial_windows.zip`.

## Classification

`invalid-for-32bpc-exact`.

The return is useful only as evidence that the Windows runner can emit an EXR
container. It must not enter a 32bpc comparison or change a conformance state.

## Facts

- The imported `reference_manifest.json` declares project
  `bits_per_channel: 8`, despite case `render_set_id` values named
  `software_32bpc`.
- The examined ColorKey output EXR has channel sample type `1` for all
  `A/B/G/R` channels. In OpenEXR this is `HALF`, not required FLOAT (`2`).
- That EXR has compression code `4`, whereas the current exact-candidate path
  requires uncompressed scanlines unless an independent decoder is supplied.
- The manifest contains a superset 48-case request while this partial zip
  physically contains only the ColorKey and ToonDilate EXR assets. Generic
  intake therefore also reports the absent Blur/DistanceGradation outputs.

## Required Windows Preflight

Before rendering the staged 98-case bundle, render one throwaway frame with
the intended Output Module and verify all of:

1. project `bitsPerChannel` is `32` in the return manifest;
2. EXR channel sample type is `2` (`FLOAT`) for A/B/G/R, not `1` (`HALF`);
3. the chosen compression is recorded; use `None` for the current local
   fail-closed verifier;
4. the actual render-set metadata records `SOFTWARE`.

Only after that preflight passes should the batch be rendered. PNG companions
and an EXR container alone are not float-preserving 32bpc evidence.
