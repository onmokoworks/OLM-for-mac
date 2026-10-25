# Installation guide

[日本語](INSTALL_JA.md) (Japanese is the primary version; this is a translation)

## Requirements

- macOS 11 or later (Apple Silicon or Intel)
- Tested with After Effects 2026 (26.3)
- CPU rendering only (GPU rendering is not supported)

## Installing

1. Quit After Effects.
2. Unzip the release ZIP.
3. Copy the 10 `.plugin` files inside into:

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

4. Check that no older plugin or backup with the same name is left in `MediaCore`, including its subfolders. Move backups outside `MediaCore`.
5. Start After Effects. If the OLM plugins appear in the Effect menu, you are done.

### Installing from the repository

From the development repository, quit After Effects and run the following. Plugins already installed are moved to a backup folder inside the repository.

```sh
scripts/install_mac_plugins_to_mediacore.sh --package /path/to/OLM_Mac_Plugins.zip
```

To check for duplicates only, run:

```sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
```

## If macOS blocks the plugins

These plugins are not signed or notarized by Apple (Apple's check of who made the software and what is inside). Signing requires a paid Apple developer membership, so there are no plans for it at the moment. As a result, macOS may block plugins you downloaded: AE shows a message such as "cannot be opened" or "the developer cannot be verified" at launch, and the plugin is not loaded.

If you trust this project, you can unblock them:

1. Quit After Effects.
2. Open Terminal, paste the following and press Return:

   ```sh
   xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
   ```

3. Start After Effects again.

Only unblock these 10 plugins. If they still do not load, report the message you saw and your macOS version.

## First checks

- At the bit depth you actually use (8 / 16 / 32 bpc), render a representative frame and compare it with the Windows version or earlier output
- Switch the preview resolution and check that the result looks the same

## If you see a warning

- Duplicate plugin: look for plugins with the same name in `MediaCore`, including its subfolders, and keep only one set.
- Preview control warning: note the plugin name and the warning text, then quit AE. Check for leftover settings from the Windows version's custom UI, or an older plugin that is still installed.

## Uninstalling

Quit After Effects and move the 10 OLM plugins out of `MediaCore`.

## Reporting problems

This information helps:

- macOS and After Effects versions, and whether your Mac is Apple Silicon or Intel
- The plugin name
- Bit depth, comp size and preview resolution
- All parameter values
- Any warning text or crash log
- If you can share them, the smallest project and footage that show the problem

See [Known limitations](../KNOWN_LIMITATIONS.en.md) for what is known not to work.
