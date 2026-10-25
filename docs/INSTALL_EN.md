# Installation guide

[日本語](INSTALL_JA.md) (Japanese is the primary version; this is a translation)

## Requirements

- macOS 11 or later (Apple Silicon or Intel)
- Mainly tested with Adobe After Effects 2026 (26.3)
- CPU rendering (GPU rendering is not supported)

> [!NOTE]
> The plugins are not signed with an Apple Developer ID or notarized (this costs money, so there are no plans to). macOS Gatekeeper may block plugins you downloaded. See [If macOS blocks the plugins](#if-macos-blocks-the-plugins) below.

## Installing

1. Quit After Effects.
2. Unzip the release ZIP.
3. Copy the 10 `.plugin` files inside into:

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

4. Check that no older plugin or backup with the same name is left in `MediaCore` or any folder inside it.
   - Move backups outside `MediaCore`.
5. Start After Effects and check that the OLM plugins appear in the Effect menu.

### Installing from the repository

From the development repository, quit After Effects and run the following. Plugins already installed are moved to a backup folder inside the repository.

```sh
scripts/install_mac_plugins_to_mediacore.sh --package /path/to/OLM_Mac_Plugins.zip
```

To check for duplicates only:

```sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
```

## If macOS blocks the plugins

macOS marks downloaded files as "from the internet". When an unsigned plugin carries this mark, AE may show a message such as "cannot be opened" or "the developer cannot be verified" at launch, and the plugin is not loaded.

If you trust this project, you can remove the mark:

1. Quit After Effects.
2. Open Terminal, paste the following and press Return:

   ```sh
   xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
   ```

3. Start After Effects again.

Only remove the mark from these 10 plugins. If they still do not load, report the message you saw and your macOS version.

## First checks

- At the bit depth you actually use (8 / 16 / 32 bpc), render a representative frame and compare it with the Windows version or earlier output
- Switch the preview resolution and check that the result looks the same

## If you see a warning

- **Duplicate plugin**: look for plugins with the same name in `MediaCore`, including the folders inside it, and keep only one set. Move backups outside `MediaCore`.
- **Preview control warning**: note the plugin name and the warning text, then quit AE. Check for leftover settings from the Windows version's custom UI, or an older plugin that is still installed.

## Uninstalling

Quit After Effects and move the 10 OLM plugins out of `MediaCore`.

## Reporting problems

Please include:

- macOS and After Effects versions, and whether your Mac is Apple Silicon or Intel
- The plugin name
- Bit depth, comp size and preview resolution
- All parameter values
- Any warning text or crash log
- If possible, the smallest project and footage you can share

See [Known limitations](../KNOWN_LIMITATIONS.en.md) for what is known not to work.
