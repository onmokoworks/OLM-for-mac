# OLM for Mac release notes

November 2026 (v1.0.0)

[日本語](RELEASE_NOTES_JA.md)

This is an unofficial Mac port of the Windows After Effects plugin suite "OLM Tools". It is a Universal binary that runs on both Apple Silicon and Intel, supporting macOS 11 and later.

## Bundled plugins

Includes 10 plugins: ColorKeep, OLMBlur, OLMColorKey, OLMDirectionalBlur, OLMDistanceGradation, OLMKiraKira, OLMRadialBlur, OLMSmoother, OLMSmoother2, and OLMToonDilate.

OLMSmoother supports 8 and 16 bpc, while the other 9 plugins support 8, 16, and 32 bpc.

## Changes since v0.2.0-beta.2

We verified opening and exporting projects created on Windows on Mac, and fixed two issues that were found.

- OLMKiraKira: Opening projects created on Windows caused the Glow Rotation value to become 0. This was because the Mac version had declared this parameter as a numerical slider instead of an angle. It has been corrected to an angle so that Windows values can be loaded as-is.
- OLMDirectionalBlur: When a layer using the same source footage as the layer with the effect applied was specified as the Noise Layer, export stopped with an error. The original plugin only uses Noise Layer when Noise Type is set to Type 3. The Mac version loading behavior was changed to match, enabling export.
- OLMRadialBlur: Clarified the handling of reading beyond image boundaries to match analysis of the original plugin. There is no change to output.

### Notes on updating (OLMKiraKira)

Due to the fix above, the parameter type for Glow Rotation has changed. Consequently, opening projects saved in Mac version beta.2 or earlier in v1.0.0 will reset the Glow Rotation value to 0 and lose its keyframes. This change was made to prioritize compatibility with projects created on Windows. For projects created in beta.2 or earlier, please save a separate copy to record the Glow Rotation values and keyframes before updating, and reapply them after updating.

## Verification results

Output was compared bit-by-bit against the original Windows plugins. For details on the comparison method, see [Verification methods and results](BETA_SUPPORT.en.md).

- When test projects created on Windows (10 plugins, 8 / 16 / 32 bpc) were opened in After Effects 2026 on Mac, all parameter values matched Windows.
- During actual export in After Effects, images received by the plugin from AE and images returned by the plugin were saved, and those same images were processed through the original Windows plugins for comparison. Across all 18 cases in 6 plugins where discrepancies had occurred, there was not a single bit of difference.
- When comparing exported files against Windows, color values can differ by up to 1 in 8 bpc. Because the same difference occurs even with all OLM effects disabled, this is a discrepancy in AE itself, not OLM. 16 bpc and 32 bpc matched.
- Out of approximately 3,000 archived test cases, only 2 cases failed to match the original plugin under the rendering pipeline used by After Effects 2026 (SmartFX). Both were due to a bug in the original plugin where it writes to uninitialized memory.

## Limitations and installation

GPU rendering is not supported.

Setting Noise Type to Type 3 in OLMRadialBlur results in an error without rendering on the Mac version. This is because on the original Windows version, this setting crashes After Effects entirely. Type 3 in OLMDirectionalBlur can render, but because the original Windows version produces different results on every export even under identical conditions, the rendering results are not guaranteed to match Windows.

Other limitations are documented in [known limitations](../KNOWN_LIMITATIONS.en.md).

For installation instructions, see the [installation guide](INSTALL_EN.md). Because this build is not signed with an Apple Developer ID or notarized, instructions for handling Gatekeeper are also included there.

## License

Inherits the license of the original OLM plugins (Apache License 2.0 by OLM Digital). The full text is available in [LICENSE](../LICENSE). This is an unofficial port and is not affiliated with, authorized, or approved by OLM Digital.
