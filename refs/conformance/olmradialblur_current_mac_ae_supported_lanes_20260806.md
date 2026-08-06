# OLMRadialBlur current Mac AE supported lanes (2026-08-06)

The installed `OLMRadialBlur` binary was attested in the sole running After Effects 26.3x87 process before both runs.

- PF8 case0010, Software, 1920x1080: the disabled control matched the source and the enabled render matched the retained Windows PNG at every RGBA8 pixel.
- PF32 case0009, Software, 1920x1080: a hash-attested diagnostic run proved that the checked-out input equals the disabled control, and the plug-in output equals local production `RenderWorld`, at every FLOAT32 word. The final EXR hash `d66dc120...7525f8` is reproduced exactly by the configured Output Module transformation `RGB=float32(RGB*alpha)` with alpha unchanged.

Therefore canonical PF8 case0010 is Mac/Windows PNG exact, while PF32 case0009 is exact across the current Mac checkout, plug-in, and configured Output Module boundary. PF32 remains outside the Windows-AE-exact claim because the retained internal `/255` oracle does not establish the Windows AE checkout/output-module contract.
