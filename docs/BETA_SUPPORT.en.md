# How we verify

[日本語](BETA_SUPPORT.md) (Japanese is the primary version; this is a translation)

## How we compare

We compare against the original Windows plugin (`.aex`) itself. The original plugin runs in an emulator that reproduces it instruction by instruction.

Both versions get the same footage and settings, and we compare the resulting images byte by byte. If anything differs by even one bit, including the area that was drawn, the test fails.

## What we test

Footage, settings, sizes and so on are combined at random.

- Footage: ordinary images, plus semi-transparent pixels and 32 bpc over-range or special values (such as NaN)
- Settings: each parameter is drawn at random from the range the UI allows
- Bit depth: 8 / 16 / 32 bpc
- Size: 1×1 to 1920×1080. Width and height are each odd or even with equal probability, including 1-pixel-wide strips
- How AE asks for a render:
  - preview resolution (Full to 1/8, including different horizontal and vertical factors)
  - drawing only part of the image, such as when zoomed in
  - when a plugin needs extra margin around the image
  - when memory rows have padding at the end

When a mismatch is found, it is automatically shrunk to the smallest example that still reproduces it and saved. After every fix, all saved examples are run again.

## Results

We compare on the render path AE normally uses (Smart Render). OLMSmoother is compared on the older path, which is the one its Windows version supports.

- In 3,000 tests focused on odd and even sizes and 1,000 tests focused on partial rendering, the outputs matched in every case the Windows version could render. Every mismatch found along the way has been fixed.
- Cases where the Windows version itself fails, or does not finish in time in the emulator, cannot be compared and are not counted.

## Checks in the real After Effects

- In After Effects 2026 for macOS, all 10 plugins load, apply and render.
- We also ran the actual plugins at real sizes (1920×1080 and 3840×2160), looked for cases that failed to render and measured render times, and fixed the problems we found.

## What we do not compare

- We do not compare against images rendered by Windows After Effects itself. We compare against the original plugin running in the emulator.
- The emulator handles sizes up to 1920×1080. For larger sizes, we assume the same processing applies unchanged.
- GPU rendering, AE color management, and differences in footage import or export are out of scope.

See [Known limitations](../KNOWN_LIMITATIONS.en.md) for other limitations.
