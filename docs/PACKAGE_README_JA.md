# OLM for Mac

Windows版のAfter Effectsプラグイン「OLM Tools」をMacで使えるようにした、非公式の移植版です（Beta版）。大事な作業に使う前に、必ずプロジェクトのバックアップを取ってください。

English: README.en.md

## インストール

1. After Effectsを終了します。
2. このフォルダーの中の10個の `.plugin` を、次のフォルダーにコピーします。

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

3. After Effectsを起動して、エフェクトメニューにOLMのプラグインが出ていれば完了です。

## macOSにブロックされたとき

Appleの署名と公証を受けていないため、macOSのGatekeeperから警告のダイアログが表示され、読み込みがブロックされることがあります。このプロジェクトを信頼できるなら、After Effectsを終了してから「ターミナル」で次を実行し、After Effectsを起動し直してください。

```sh
xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
```

## 動作環境

- macOS 11以降（Apple Silicon／Intel）
- After Effects 2026（26.3）で確認しています
- CPUレンダーのみ（GPUレンダーには非対応）
- OLMSmootherは8／16 bpcのみ、ほかの9本は8／16／32 bpcに対応しています

## くわしい情報

- インストールガイド：https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.1/docs/INSTALL_JA.md
- 既知の制限：https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.1/KNOWN_LIMITATIONS.md
- 検証の方法と結果：https://github.com/onmokoworks/OLM-for-mac/blob/v0.2.0-beta.1/docs/BETA_SUPPORT.md
- 不具合の報告：https://github.com/onmokoworks/OLM-for-mac/issues

## ライセンス

元のOLMプラグインのライセンス（OLM DigitalによるApache License 2.0）を継承しています。本文は同じフォルダーのLICENSEにあります。これは非公式の移植で、OLM Digitalとは関係なく、許可や承認は受けていません。
