# OLM for Mac

An unofficial Mac port of the Windows After Effects plugins "OLM Tools" (Beta). Back up your projects before using it for important work.

日本語: README.md

## Install

1. Quit After Effects.
2. Copy the 10 `.plugin` bundles in this folder to:

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

3. Start After Effects. The OLM plugins should appear in the Effect menu.

## If macOS blocks the plugins

The plugins are not signed or notarized by Apple. macOS Gatekeeper may show a warning and block them. If you trust this project, quit After Effects, run the following in Terminal, then start After Effects again.

```sh
xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
```

## Requirements

- macOS 11 or later (Apple Silicon / Intel)
- Tested with After Effects 2026 (26.3)
- CPU rendering only (GPU rendering is not supported)
- OLMSmoother supports 8/16 bpc; the other nine support 8/16/32 bpc

## More information

- Installation guide: https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.2/docs/INSTALL_EN.md
- Known limitations: https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.2/KNOWN_LIMITATIONS.en.md
- How we verify: https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.2/docs/BETA_SUPPORT.en.md
- Bug reports: https://github.com/onmokoworks/OLM-for-mac/issues

## License

This port inherits the license of the original OLM plugins (Apache License 2.0 by OLM Digital). The full text is in LICENSE in this folder. This is an unofficial port, not affiliated with OLM Digital, and has not been permitted or endorsed by them.
