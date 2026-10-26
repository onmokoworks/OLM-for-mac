# インストールガイド

[English](INSTALL_EN.md)

## 動作環境

- macOS 11以降（Apple Silicon／Intel）
- After Effects 2026（26.3）で確認しています
- CPUレンダーのみ（GPUレンダーには非対応）

## インストール

1. After Effectsを終了します。
2. 配布ZIPを展開します。
3. 中の10個の `.plugin` を、次のフォルダーにコピーします。

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

4. `MediaCore` の中（サブフォルダーも含む）に、同じ名前の古いプラグインやバックアップが残っていないか確かめます。バックアップは `MediaCore` の外に移してください。
5. After Effectsを起動して、エフェクトメニューにOLMのプラグインが出ていれば完了です。

### リポジトリから入れる場合

開発用リポジトリから入れるときは、After Effectsを終了してから次を実行します。入っていたプラグインは、リポジトリ内の退避用フォルダーに移されます。

```sh
scripts/install_mac_plugins_to_mediacore.sh --package /path/to/OLM_Mac_Plugins.zip
```

重複があるかどうかだけ調べるときは、次を実行します。

```sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
```

## macOSにブロックされたとき

このプラグインは、Appleの署名と公証を受けていません。署名と公証には有料のAppleの開発者登録が必要なため、今のところ予定はありません。そのため、ダウンロードしたプラグインは、AEの起動時にmacOSのGatekeeperから警告のダイアログが表示され、読み込みがブロックされることがあります。

このプロジェクトを信頼できるなら、次の手順で解除できます。

1. After Effectsを終了します。
2. 「ターミナル」を開いて、次を貼り付けて実行します。

   ```sh
   xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
   ```

3. After Effectsを起動し直します。

解除するのは、この10個のプラグインだけにしてください。それでも読み込まれないときは、表示された文言とmacOSのバージョンを添えて報告してください。

## 最初に確かめること

- 実際に使う色深度（8／16／32 bpc）で代表的なフレームをレンダーして、Windows版や以前の出力と比べる
- プレビュー解像度を切り替えても、見た目が変わらないか確かめる

## 警告が出たとき

- プラグインの重複：`MediaCore` の中（サブフォルダーも含む）で同じ名前のプラグインを探して、1組だけ残します。
- プレビュー制御の警告：プラグイン名と警告文をメモして、AEを終了します。Windows版の独自UIの設定や、古いプラグインが残っていないか確かめてください。

## アンインストール

After Effectsを終了して、`MediaCore` から10個のOLMプラグインを別の場所に移します。

## 不具合の報告

次の情報があると助かります。

- macOSとAfter Effectsのバージョン、MacがApple SiliconかIntelか
- プラグイン名
- 色深度、コンポのサイズ、プレビュー解像度
- すべてのパラメーターの値
- 警告文やクラッシュログ
- 共有できるなら、最小限のプロジェクトと素材

わかっている制限は[既知の制限](../KNOWN_LIMITATIONS.md)を見てください。
