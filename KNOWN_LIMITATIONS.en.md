# Known limitations

[日本語](KNOWN_LIMITATIONS.md) (Japanese is the primary version; this is a translation)

Known limitations of the Public Beta.

## General

- **Not signed or notarized.** The plugins are not signed with an Apple Developer ID or notarized (this costs money, so there are no plans to), so macOS Gatekeeper may block plugins you downloaded. See [the installation guide](docs/INSTALL_EN.md#if-macos-blocks-the-plugins).
- **Mainly tested with After Effects 2026 (26.3).** Other versions may load the plugins, but they have not been tested.
- **GPU rendering is not supported.** Use CPU rendering.
- **Final files may not match Windows.** Even when the plugin computes the same result as on Windows, AE color management, footage import and export formats can behave differently on Windows and macOS.
- **Very large sizes or very heavy settings may fail.** Memory and workload limits apply. Sizes up to 3840×2160 have been tested.
- **The custom Effect Controls UI is not ported.** The Windows version's custom preview drawing, click interactions and dynamic labels are not available. Parameter types, names, defaults and ranges match the Windows version.

## Settings where the Windows version fails

With some settings, the Windows version itself fails, or reads memory outside its own data.

- These cases cannot be compared, so we do not know whether the Mac output matches.
- The Mac version may not render either.

## Per plugin

- **OLMSmoother**: no 32 bpc support (the same as the Windows version). In a 32 bpc comp, AE converts the bit depth for it.
- **OLMRadialBlur**: rotation mode at high quality (for example Quality 50) can take over a minute per 1080p frame, because it does the same amount of work as the Windows version.
- **OLMDirectionalBlur**: at 32 bpc, pixels with negative alpha combined with Back Alpha Fade do not match the Windows version. In this case the Windows version reads memory whose contents are undefined. Ordinary footage never has negative alpha.

## A render path AE does not normally use

After Effects effects have two render paths.

- **Smart Render**: the path AE normally uses. This is where the Mac version matches Windows.
- **Classic path**: not normally used. Here the Windows version may draw nothing or a broken image. The Mac version renders the same result as Smart Render instead.

OLMSmoother is the exception: the Windows version only has the classic path, so that is the path the Mac version matches.
