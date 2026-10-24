# Support and verification

[日本語](BETA_SUPPORT.md) (Japanese is the primary version; this is a translation)

This document explains how we check that the Mac version matches the Windows version.

## What we compare against

- The reference is **the original Windows plugin (`.aex`) itself**.
- Windows programs cannot run directly on a Mac, so we run it in an emulator that reproduces it instruction by instruction.
- Both versions get the same input and settings, and we compare the outputs byte by byte. We also compare the output area (which region was drawn).
- A test passes only if not a single bit differs. No tolerance is allowed.

## What we test

Test conditions are generated randomly.

- **Footage**: ordinary images, plus semi-transparent pixels and 32 bpc over-range or special values (such as NaN)
- **Settings**: each plugin's parameters, drawn from the ranges the UI allows
- **Bit depth**: 8 / 16 / 32 bpc
- **Size**: 1×1 up to 1920×1080. Width and height are each odd or even with equal probability, including 1-pixel-wide strips
- **How AE asks for the render**:
  - preview resolution (Full, 1/2, 1/3, 1/4, 1/8, and different horizontal and vertical factors)
  - rendering only part of the image (zoomed-in views, or when only part of the frame is visible)
  - enlarged output when a plugin asks for extra margin
  - padded memory rows

Every mismatch found is automatically shrunk to the smallest example that reproduces it and saved. All saved examples are replayed after every change.

## Results

These results are for the render path AE normally uses (Smart Render). OLMSmoother is compared on the other, classic path.

- In 3,000 tests focused on odd and even sizes and 1,000 tests focused on partial rendering, the outputs matched in every case the Windows version could render.
  - Every mismatch found along the way has been fixed.
- Cases where the Windows version itself fails, or does not finish in time in the emulator, cannot be compared and are not counted.

## Checks in the real After Effects

- In After Effects 2026 for macOS, all 10 plugins load, apply and render.
- At real sizes (1920×1080 and 3840×2160), we ran the actual plugins, measured refusals and render times, and fixed the problems found.

## What we do not compare

- We do not compare against output rendered in Windows After Effects itself. We compare against the original plugin code running in the emulator.
- The emulator handles sizes up to 1920×1080. For larger sizes, we rely on the same processing holding for larger images.
- GPU rendering, AE color management, and differences in footage import or export are out of scope.

See [Known limitations](../KNOWN_LIMITATIONS.en.md) for the list of limitations.
