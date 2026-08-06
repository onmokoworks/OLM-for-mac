# OLMDistanceGradation classic PF8 Outside/Sphere/no-bg exact

The PF8 branch is independently executed through actual `FUN_181170870`; it
does not reuse PF16 staging or word quantization. Both invert states use 187
actual callback invocations over 17x11 pixels.

- Input/output rowbytes: 75/79 (active row 68 bytes).
- All `0xA5` padding remains unchanged.
- Actual field SHA-256:
  `f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229`.
- Invert-off active byte SHA-256:
  `2a5da60c5858360fe2bb6cd34e275eab368e73eebc6d0d0dc8afb34105392d19`.
- Invert-on active byte SHA-256:
  `5523ca4d6859e4c008a0c1479640f2530090fb60fd5d04b844c06bb3a7fa1c77`.
- Production comparison: 869/869 bytes including padding, zero mismatches for
  each invert state.

The discriminator proved that PF8 Outside/RGB/no-bg also clears hidden RGB
when source ownership is zero. The production fix extends only that ownership
condition to PF8; PF8 field conversion and output storage remain byte-native.
No PF32 Smart path is claimed.
