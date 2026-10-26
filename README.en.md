# OLM for Mac

[日本語](README.md) (Japanese is the primary version; this is a translation)

An unofficial port that lets you use the "OLM Tools" After Effects plugins, originally for Windows, on a Mac. It runs on both Apple Silicon and Intel Macs.

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
| OLMRadialBlur | 8 / 16 / 32 bpc | Rotation mode at high quality is heavy and can take over a minute per 1080p frame |
| OLMSmoother | 8 / 16 bpc | No 32 bpc support (same as the Windows version). In a 32 bpc comp, AE converts the bit depth for it |
| OLMSmoother2 | 8 / 16 / 32 bpc | |
| OLMToonDilate | 8 / 16 / 32 bpc | |

## Compatibility with the Windows version

We develop this port by analyzing the original plugins, aiming for **output that is bit-for-bit identical to the Windows version** for the same footage and settings.

We compare the original plugin, running in an emulator, with the Mac version across thousands of random combinations of footage, settings, sizes and preview resolutions. In every case the Windows version can render, the outputs match. See [How we verify](docs/BETA_SUPPORT.en.md) for details and [Known limitations](KNOWN_LIMITATIONS.en.md) for what is known not to work.

## Requirements

- macOS 11 or later
- Tested with After Effects 2026 (26.3). Other versions are untested
- CPU rendering only (GPU rendering is not supported)

## Installation

Quit After Effects, then copy the 10 `.plugin` files from the release ZIP into:

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

> [!NOTE]
> The plugins are not signed or notarized by Apple, so macOS Gatekeeper may show a warning dialog and block them from loading. Signing requires a paid Apple developer membership, so there are no plans for it at the moment. See the [installation guide](docs/INSTALL_EN.md) for what to do if macOS blocks them, and for detailed steps.

## Reporting problems

Please report problems via [Issues](https://github.com/onmokoworks/OLM-for-mac/issues). This information helps:

- macOS and After Effects versions, and whether your Mac is Apple Silicon or Intel
- Plugin name, bit depth, comp size and preview resolution
- The effect settings
- Steps to reproduce, and any warning text or crash log
- If you can share them, the smallest project and footage that show the problem

If the result looks different from the Windows version, please also attach an image rendered by the Windows version with the same footage and settings. It makes the cause much easier to find.

## License

- This port inherits the original OLM plugins' license (Apache License 2.0, by OLM Digital). The license text is in [LICENSE](LICENSE).
- This is an unofficial port. It has no connection with OLM Digital and is not authorized or endorsed by them.
