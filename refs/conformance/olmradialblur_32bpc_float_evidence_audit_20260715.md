# OLMRadialBlur 32bpc FLOAT Evidence Audit

The imported Windows set contains 10 paired before/effect OpenEXR files from AE `26.3x87`, Software, 32bpc, 1920x1080 at 24 fps. `file` reports OpenEXR v2 scanline, uncompressed, with the expected data window; the intake manifest records the set as float-preserving. This is Windows reference evidence, not Mac exactness.

## Family coverage

- Zoom: cases 01, 03, 05, 07, 09 (`Blur Type=1`).
- Rotation: cases 02, 04, 06, 08, 10 (`Blur Type=2`).
- Inner: all 10 have nonzero inner strength.
- Variation: all 10 have nonzero Size Variation.
- Noise: all 10 have nonzero Noise Variation with pinned Noise Type and Seed.
- Edge: all 10 bind outer/inner Edge Fade and Repeat Border.

## Smallest candidate

Use cases **01 (Zoom)** and **02 (Rotation)**. Two cases is the minimum set that covers both blur types while retaining active Inner, variation, noise, and edge inputs. Their complete parameter bindings are in the Windows manifest and their four EXR SHA-256 values are recorded in the JSON audit.

This is a **candidate for Mac FLOAT EXR validation only**. It is not an exactness result. The existing RadialBlur 8bpc Zoom, Rotation, and Inner lanes remain unresolved, and no RadialBlur-specific Mac no-effect control has been accepted.

## Evidence boundary

Do not retune production source, infer 8bpc semantics from these 32bpc files, or claim exactness from visual similarity, PNGs, or a Mac effect render without a passing same-case no-effect control and bound plugin identity.
