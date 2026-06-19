# OLM Official ZIP Snapshot - 2026-06-19

This folder is a project-local snapshot of the official OLM OpenTools ZIP files
that were present in `~/Downloads` on 2026-06-19. The files are kept here so the
porting work can cite a stable local copy instead of relying on browser download
state.

## Contents

- `zips/`: original ZIP files copied without modification.
- `extracted/`: extracted ZIP trees for inspection.
- `listings/`: `unzip -l` output for each ZIP.
- `pdf_text/`: extracted text from the bundled English/Japanese PDF manuals.
- `SHA256SUMS.txt`: SHA-256 hash for each original ZIP.

## ZIPs

| ZIP | Official page | Main bundled docs |
| --- | --- | --- |
| `OLMBlur.zip` | https://www.olm.co.jp/post/olm-blur | `OLMBlurUserManual.pdf`, `OLMBlurUserManualEN.pdf` |
| `OLMColorKeep.zip` | https://www.olm.co.jp/post/color-keep | `ColorKeepUserManual.pdf`, `ColorKeepUserManualEN.pdf` |
| `OLMColorKey.zip` | https://www.olm.co.jp/post/olm-color-key | `OLMColorKeyUserManual.pdf`, `OLMColorKeyUserManualEN.pdf` |
| `OLMDirectionalBlur.zip` | https://www.olm.co.jp/post/olm-directional-blur | `OLMDirectionalBlurUserManual.pdf`, `OLMDirectionalBlurUserManualEN.pdf` |
| `OLMDistanceGradation.zip` | https://www.olm.co.jp/post/distance-gradation | `DistanceGradationUserManual.pdf`, `DistanceGradationUserManualEN.pdf` |
| `OLMKiraKira.zip` | https://www.olm.co.jp/post/olm-kirakira | `OLMKiraKiraUserManual.pdf`, `OLMKiraKiraUserManualEN.pdf` |
| `OLMRadialBlur.zip` | https://www.olm.co.jp/post/olm-radial-blur | `OLMRadialBlurUserManual.pdf`, `OLMRadialBlurUserManualEN.pdf` |
| `OLMSmootherAE.zip` | https://www.olm.co.jp/post/olm-smoother | `OLMSmootherUserManual.pdf`, `OLMSmootherUserManualEN.pdf` |
| `OLMSmoother2AE.zip` | https://www.olm.co.jp/post/olm-smoother-v2 | `OLM Smoother v2 AE Manual EN.pdf`, `OLM Smoother v2 AE Manual JP.pdf` |
| `OLMToonDilate.zip` | https://www.olm.co.jp/post/olm-toon-dilate | `OLM Toon Dilate Manual EN.pdf`, `OLM Toon Dilate Manual JP.pdf` |

## Notes For Porting

- The official PDF manuals are useful as intent/parameter evidence, not as an
  exact implementation proof.
- The manuals frequently name algorithmic structure directly:
  - OLM Blur applies blur only to pixels with `alpha > 0`.
  - Directional/Radial Blur ignore fully transparent pixels and vary strength by
    opaque pixel groups.
  - KiraKira composes glow from alpha/luminance/RGB/brightness highlights using
    vertical, horizontal, and diagonal blur passes.
  - Distance Gradation generates inside/outside alpha-mask distance gradations.
  - Toon Dilate expands non-transparent regions into transparent borders.
- Use these notes to choose IR feature slices before reading Ghidra/objdump.
  Exactness still requires binary-grounded constants, rounding, loop bounds,
  boundary behavior, and AE Software reference comparison.
