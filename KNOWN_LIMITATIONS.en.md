# Known limitations

[日本語](KNOWN_LIMITATIONS.md) (Japanese is the primary version; this is a translation)

## General

### Not signed or notarized by Apple

The plugins are not signed or notarized by Apple. When downloaded plugins are loaded, macOS Gatekeeper may show a warning dialog and block them. Signing requires an Apple developer membership with an annual fee, so there are no plans for it at the moment. See the [installation guide](docs/INSTALL_EN.md#if-macos-blocks-the-plugins) for what to do.

### Tested AE version

Only After Effects 2026 (26.3) has been tested. Other versions are untested.

### GPU rendering

GPU rendering is not supported.

### Rendered files and Windows

Rendered files may not match Windows. Even when the plugin computes the same result, AE color management and footage import and export can behave differently on Windows and macOS.

### Extremely large sizes or heavy settings

Extremely large sizes or very heavy settings can fail, because memory and workload limits apply. Sizes up to 3840×2160 have been tested.

### The Effect Controls panel

The look in a real AE has not been fully checked yet. KiraKira's gradient editor and the way some settings hide or grey out other controls have been checked against recordings of the Windows version's behaviour and match. Their look and feel in a real AE still have to be checked.

## Settings where the Windows version fails

With some settings, the Windows version itself fails, or reads memory outside its own data. These cases cannot be compared, so we do not know whether the Mac result matches. The Mac version may not render either.

## Per plugin

- OLMSmoother: no 32 bpc support (the same as the Windows version). In a 32 bpc comp, AE converts the bit depth for it.
- OLMRadialBlur: rotation mode at high quality (for example Quality 50) can take over a minute per 1080p frame, because it does the same amount of work as the Windows version.
- OLMDirectionalBlur: when 32 bpc footage has pixels with negative alpha and Back Alpha Fade is used, the result does not match the Windows version. In this case the Windows version reads memory whose contents are undefined. Ordinary footage never has negative alpha.

## A render path AE does not normally use

After Effects effects have two ways to render.

- Smart Render: the one AE normally uses. This is where the Mac version matches Windows.
- The older path (Classic): not normally used. Here the Windows version may draw nothing or a broken image. The Mac version renders the same way as Smart Render.

OLMSmoother is the exception: its Windows version only supports the older path, so that is where the Mac version matches it.
