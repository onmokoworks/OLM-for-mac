# OLM for Mac

[日本語](README.md) (the Japanese documents are the primary version; this is a translation)

An unofficial port of the "OLM Tools" After Effects plugins from Windows to macOS (Apple Silicon and Intel).

> [!WARNING]
> This is a beta. Before using it for work or production, make backups and take other precautions against risks such as data loss.

## Plugins

| Plugin | Bit depth | Notes |
|---|---|---|
| ColorKeep | 8 / 16 / 32 bpc | |
| OLMBlur | 8 / 16 / 32 bpc | |
| OLMColorKey | 8 / 16 / 32 bpc | |
| OLMDirectionalBlur | 8 / 16 / 32 bpc | |
| OLMDistanceGradation | 8 / 16 / 32 bpc | |
| OLMKiraKira | 8 / 16 / 32 bpc | |
| OLMRadialBlur | 8 / 16 / 32 bpc | Rotation mode at high quality can take over a minute per 1080p frame |
| OLMSmoother | 8 / 16 bpc | The Windows version does not support 32 bpc either. In a 32 bpc comp, AE converts the bit depth for it |
| OLMSmoother2 | 8 / 16 / 32 bpc | |
| OLMToonDilate | 8 / 16 / 32 bpc | |

## Compatibility with the Windows version

We develop this port by analyzing the original plugins, aiming for **output that is bit-for-bit identical to the Windows version** for the same footage and settings.

- We run the original Windows plugin (`.aex`) in an emulator and compare its output with the Mac output byte by byte.
- We test thousands of random combinations of footage, settings, comp size (odd and even), preview resolution (Full to 1/8), and partial rendering such as zoomed-in views. In every case the Windows version can render, the outputs match.
- Where the Windows version itself fails on a setting, the Mac version may not render either.

See [Support and verification](docs/BETA_SUPPORT.en.md) for how this is tested, and [Known limitations](KNOWN_LIMITATIONS.en.md) for what is known not to work.

## Requirements

- macOS 11 or later (Apple Silicon or Intel)
- Mainly tested with Adobe After Effects 2026 (26.3)
- CPU rendering (GPU rendering is not supported)

## Installation

Quit After Effects, then copy the 10 `.plugin` files from the release ZIP into:

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

See the [installation guide](docs/INSTALL_EN.md) for details.

> [!NOTE]
> The plugins are not signed with an Apple Developer ID or notarized (this costs money, so there are no plans to). If macOS blocks them, see [the installation guide](docs/INSTALL_EN.md#if-macos-blocks-the-plugins).

## Reporting problems

Please open an [issue](https://github.com/onmokoworks/OLM-for-mac/issues) and include:

- macOS and After Effects versions, and whether your Mac is Apple Silicon or Intel
- Plugin name, bit depth, comp size and preview resolution
- The effect settings
- Steps to reproduce, and any warning text or crash log
- If possible, the smallest project and footage you can share

If the result looks different from the Windows version, the Windows output for the same footage and settings helps a lot.

## License and rights

- This is an **unofficial port**. It has no connection with OLM Digital, who created the original plugins, and is not authorized or endorsed by them.
- Names and logos such as "OLM", and the rights to the original Windows plugins, belong to OLM Digital and the other original rights holders.
- The code in this repository is released under the [Apache License 2.0](LICENSE). As long as you follow its terms, you may use, modify and redistribute it.
- The license covers **only the code in this repository**. It does not give you the right to use the OLM name or logo, or the original Windows plugins.
