# OLM for Mac release notes

October 2026 · Beta

[日本語](RELEASE_NOTES_JA.md)

This is an unofficial Mac port of OLM Tools, the Windows After Effects plugins. Each Universal binary contains Apple Silicon and Intel code and supports macOS 11 or later. Real AE checks used After Effects 2026.

## Included plugins

The package contains ten plugins: ColorKeep, OLMBlur, OLMColorKey, OLMDirectionalBlur, OLMDistanceGradation, OLMKiraKira, OLMRadialBlur, OLMSmoother, OLMSmoother2, and OLMToonDilate.

OLMSmoother supports 8/16 bpc. The other nine support 8/16/32 bpc.

## Changes since the August beta

- Fixed render refusals that produced black frames at reduced preview resolutions or when rendering part of an image. Image bounds, origins, and blur widths now follow the original Windows behavior. OLMBlur's bounds checks matched in 200 cases; four cropped-image DirectionalBlur cases changed from refusals to bit-exact matches (P02h, P04b2). Black images are not always bugs: some settings still produce transparent or black output.
- Fixed KiraKira gradient editing and the controls that become hidden or disabled depending on settings. Comparisons with the original matched 159 editing and related dispatches and 2,642 control-state/reconstruction checks (U02b, U04). Appearance in real AE and saved-project reloads are not yet fully verified.
- Sped up expensive processing. A heavy DirectionalBlur setting at 1080p fell from 17.75–18.32 seconds to 1.38–1.43 seconds. KiraKira's default setting ran 1.59–1.73 times as fast (P05a, P07a). These measurements used a Mac test host; they do not guarantee AE timings or speedups for every setting.

## Verification

We run the original Windows `.aex` in the Unicorn emulator and compare pixels and render bounds for identical inputs and settings. A one-bit difference fails the comparison. The following measurements come from merged reports. They are not a complete rerun against this ZIP.

- Original-plugin comparison: in V01, the Intel binary matched pixels and bounds in 1,854 of 2,000 cases. The original did not render in the other 146 cases, so they could not be compared: 70 unsupported OLMSmoother 32 bpc cases and 76 original-plugin or emulator execution failures.
- Apple Silicon versus Intel: across 3,560 V01 cases, 8,171 rendered pairs matched, as did 373 refusal pairs. There were zero pixel or bounds differences. This included 60 heavy cases at 1080p/4K and 8/16/32 bpc. Intel code ran under Rosetta, not on a physical Intel Mac.
- Real AE renders: all ten plugins were checked at Full/Half/Third/Quarter resolution. The 8 bpc campaign summarized by A02h produced 132 outputs; the 16/32 bpc campaign produced 176. Among images with effects, 107 of 120 and 136 of 160 respectively matched the original plugin. Reduced-resolution comparisons use no-effect exports as input proxies.

The remaining real-AE comparisons include loss of RGB under transparent pixels during export, unavailable OLMSmoother 32 bpc references, and a two-sample difference in a 4K image. ColorKeep at 8 bpc matched at all four resolutions when exported to PNG preserving hidden RGB. A separate real-AE Smoother2 refusal has a source fix, but the real-AE retest is still incomplete (A02h, S01, S02). Equality for every input, or with files exported by Windows AE, has not been established.

## Limitations and installation

GPU rendering is unsupported. Some settings remain slow, including high-quality RadialBlur rotation. See [known limitations](../KNOWN_LIMITATIONS.en.md).

Quit AE, then copy the ten `.plugin` bundles from the ZIP into MediaCore. The [installation guide](INSTALL_EN.md) covers the steps and Gatekeeper. Binaries are ad-hoc signed, without Apple Developer ID signing or notarization.

## License

The port inherits the original OLM plugins' Apache License 2.0. See [LICENSE](../LICENSE). This is an unofficial port, unaffiliated with OLM Digital.
