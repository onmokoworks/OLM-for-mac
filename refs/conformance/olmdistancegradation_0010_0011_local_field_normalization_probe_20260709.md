# OLMDistanceGradation 0010/0011 local field-normalization probe

Date: 2026-07-09

## Decision

Local evidence does not justify a Mac source change for `case_0010/0011`.
The Mac distance transform and the repository's OpenCV-compatible native
`cvDistTransform(DIST_L2, DIST_MASK_PRECISE)` agree bit-for-bit at the checked
witness fields. The remaining one-word alpha-store differences sit exactly on
floating/packing half-boundaries, and candidate field-pack/store models are not
safe to apply globally from local evidence alone.

The next useful proof is a two-point Windows same-run witness: one point where
Mac stores one word low and one point where Mac stores one word high.

## Witness Stability

The AE debug single-case outputs are byte-identical to the canonical batch
candidate for both target cases:

```text
0010 single-vs-batch max 0 nz 0 mean 0.0
0010 single-vs-ref   max 2 nz 351 mean 0.00016927083333333334
0011 single-vs-batch max 0 nz 0 mean 0.0
0011 single-vs-ref   max 2 nz 501 mean 0.0002416087962962963
```

## Local OpenCV/EDT Check

Using the request input PNG and the current depth-gated source mask, the Mac
Meijster implementation and `tools/emulation/opencv_impls.py` produce identical
raw distance values for the representative fields:

```text
CASE 0010
inside  raw bits equal True
  (901,394) raw_inside=44.0113639831543 norm=0.6985930800437927
outside raw bits equal True
  (6,40) raw_outside=41.0 norm=0.9002838730812073

CASE 0011
inside  raw bits equal True
  (915,392) raw_inside=46.81879806518555 norm=0.1345367729663849
outside raw bits equal True
```

These values reproduce the current Mac store boundary, not the Windows reference
word, so the problem is not a simple replacement of Mac EDT with the current
OpenCV detour implementation.

## Half-Boundary Shape

The checked stores land on exact half-boundaries:

| case | xy | Mac out/store | implied Windows store | boundary reading |
| --- | --- | ---: | ---: | --- |
| 0010 | `(6,40)` | `3267.498... -> 3267` | `3268` | Mac one word low |
| 0010 | `(901,394)` | `9876.501... -> 9877` | `9876` | Mac one word high |
| 0011 | `(915,392)` | `28359.5... -> 28360` | `28359` | Mac one word high |

The sign flip rejects a global `clamp16()` rounding change.

## Rejected Local-Only Shortcut

A whole-frame simulation of field quantization/readback candidates
(`none`, `round32768`, `trunc32768`, `round65535`, `trunc65535`, combined with
round/trunc store) does not safely classify the family:

```text
CASE 0010 best local candidate among tested models still has max=1440 and
thousands of nonzero pixels against the Windows reference.

CASE 0011 best local candidate among tested models still has max=65347 and
thousands of nonzero pixels against the Windows reference.
```

This does not prove the field-pack hypothesis false, because the simple
simulation does not fully model AE's 16bpc world/export behavior. It does prove
that no broad local field-pack/store toggle should be adopted from this probe.

## Required Windows Witness

Package a narrow runtime request for:

- `case_0010 (6,40)` Mac-low / Windows-high witness.
- `case_0010 (901,394)` Mac-high / Windows-low witness.
- Optional `case_0011 (915,392)` duplicate Mac-high witness.

For each point, capture in the same Windows run:

- raw inside/outside distance values before threshold/normalize,
- normalized field world value actually consumed by `FUN_181170480`,
- field-world stored word if a PF16/byte field world exists,
- compose `out_a` before PF16 store,
- final `PF_Pixel16` output store word,
- exported PNG/TIFF/EXR sample if available.

Do not send a broad PNG batch for this family; the proof needs the exact
half-boundary word path.
