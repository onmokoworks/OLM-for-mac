# OLMRadialBlur case0009 PF32 Mac-AE control replay

The portable test regenerates the AE disabled-control words from the pinned
PNG through a compact 256-entry byte-to-float mapping, reorders them into
`PF_PixelFloat` ARGB memory, and runs production case0009 `RenderWorld`. Its
semantic output hash is pinned to `a0fe5f150e686aea4623ee22adc46898e7668639c0825b94390dfcc54437e510`.

The mapping was derived from the preserved control EXR after proving that all
256 source byte values occur in each of R, G, and B, and that every occurrence
of a byte maps to one identical float32 word across all three channels.

Reproduction:

```sh
python3 tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py

# Optional provenance and retained effect-residual verification:
python3 tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py \
  --source-run /tmp/olmradialblur_pf32_20260806.8xa7UB
```

The comparison determines whether AE's observed source quantization is
sufficient to reproduce the effect EXR without changing the RadialBlur
algorithm. It does not prove that the disabled-control EXR words are identical
to the checked-out input world; that requires an in-plugin same-run capture.
It also makes no Windows-AE exact claim.

When optional retained artifacts are available, the control replay is close
but not exact: `80,625` of `8,294,400`
semantic RGBA float words differ from the preserved effect EXR, with a maximum
raw positive-float word distance of `3` ULP. Therefore AE's visible half-range
source quantization explains the broad shift away from the PNG `/255` oracle,
but the disabled-control EXR is not a byte-exact substitute for the actual
checked-out input world. The remaining first divergent boundary is still
between checkout input and the output module; a same-run in-plugin input/output
world capture is required to separate it further.
