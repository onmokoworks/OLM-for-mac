# OLMRadialBlur current Mac AE supported lanes (2026-08-06)

The installed `OLMRadialBlur` binary was attested in the sole running After Effects 26.3x87 process before both runs.

- PF8 case0010, Software, 1920x1080: the disabled control matched the source and the enabled render matched the retained Windows PNG at every RGBA8 pixel.
- PF32 case0009, Software, 1920x1080: AE produced finite FLOAT32 RGBA output, but the semantic hash was `d66dc120...7525f8`, not the pinned internal hash `7de7d970...62010`.

Therefore the current exact claim is limited to canonical PF8 case0010. PF32 case0009 remains an observed residual and is not Windows-AE-exact evidence.
