# OLMRadialBlur case0009 PF32 Mac-AE control replay

The portable test regenerates the AE disabled-control words from the pinned
PNG through a compact 256-entry byte-to-float mapping, reorders them into
`PF_PixelFloat` ARGB memory, and runs production case0009 `RenderWorld`. Its
semantic output hash is pinned to `a0fe5f150e686aea4623ee22adc46898e7668639c0825b94390dfcc54437e510`.
Applying the recorded Output Module transformation—float32 `RGB *= alpha` with
alpha unchanged—then reproduces the effect EXR semantic hash exactly:
`d66dc120c1f67ea8631dc0fe43f877c51f8e6b5554eafd1c4cb34901ee7525f8`.

The mapping was derived from the preserved control EXR after proving that all
256 source byte values occur in each of R, G, and B, and that every occurrence
of a byte maps to one identical float32 word across all three channels.

Reproduction:

```sh
python3 tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py

# Optional provenance and retained effect-residual verification:
python3 tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py \
  --source-run /path/to/ae-run --capture-dir /path/to/world-capture
```

The comparison determines whether AE's observed source quantization is
sufficient to reproduce the effect EXR without changing the RadialBlur
algorithm. It does not prove that the disabled-control EXR words are identical
to the checked-out input world; that requires an in-plugin same-run capture.
It also makes no Windows-AE exact claim.

The diagnostic same-run capture establishes the complete boundary: checked-out
input equals the control EXR and compact byte mapping at every word; captured
output equals the local `RenderWorld` replay at every word. Before Output Module
premultiplication, `80,625` RGB words differ by at most `3` ULP and alpha is
exact. After float32 `RGB *= alpha`, all `8,294,400` semantic words equal the
effect EXR. The first divergence from raw plug-in output is therefore the
configured Output Module `Color: Premultiplied (Matted)` transformation, not AE
checkout or RadialBlur.
