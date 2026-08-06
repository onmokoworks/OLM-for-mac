# OLMDirectionalBlur PF16 Noise Type 3 exact lane — 2026-08-06

The frozen release-matrix Type 3 hole is closed for this bounded tuple:

- actual Windows AEX under the local Unicorn host fixture;
- PF16 ARGB64, 16x16, input rowbytes 144, Layer rowbytes 152;
- angle 45, brightness 1, front strength 8, back strength 0;
- size/fade/tail 0, Noise Variation 100, Type 3 Layer, scale 1;
- Layer pixels equal the input fixture, with independent row padding.

The actual AEX output and the production typed core are byte-identical for all
1024 words. The output SHA-256 is
`d536acfe42daac18c06ab91b6a78eebec15b68c9cc42540a1592575868391f8a`.
The actual-AEX rotated field SHA-256 is
`7ba4c0d31dd81cf34b7593862c85f400f0a526e56588d5624f0f566b745f1072`.
The source-included public production dispatcher independently proves that a
valid same-size PF16 Layer reaches this typed route and preserves output
padding. A missing or dimension-mismatched Layer and all other unproved PF16
Type 3 tuples remain fail-closed.

Reproduce:

```sh
python3 tools/emulation/test_olmdirectionalblur_pf16_noise_type3_production_20260806.py
python3 tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py
```
