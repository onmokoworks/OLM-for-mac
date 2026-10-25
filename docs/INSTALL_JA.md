# インストールガイド

[English](INSTALL_EN.md)

## 動作環境

- macOS 11以降（Apple Silicon／Intel）
- Adobe After Effects 2026（26.3）で主に確認しています
- CPUレンダー（GPUレンダーは対象外です）

> [!NOTE]
> このプラグインはAppleの開発者署名と公証（notarization）を受けていません（有料のため、予定はありません）。ダウンロードしたプラグインをmacOSのGatekeeperが止めることがあります。対処は下の「[macOSに止められたとき](#macosに止められたとき)」を見てください。

## インストール

1. After Effectsを終了します。
2. 配布ZIPを展開します。
3. 中に入っている10個の `.plugin` を、次のフォルダーへコピーします。

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

4. `MediaCore` とその中のフォルダーに、同じ名前の古いプラグインやバックアップが残っていないか確かめます。
   - バックアップは `MediaCore` の外へ移してください。
5. After Effectsを起動し、エフェクトメニューにOLMのプラグインがあるか確かめます。

### リポジトリから入れる場合

開発用リポジトリから入れるときは、After Effectsを終了してから次を実行します。今入っているプラグインはリポジトリ内の退避用フォルダーへ移されます。

```sh
scripts/install_mac_plugins_to_mediacore.sh --package /path/to/OLM_Mac_Plugins.zip
```

重複があるかどうかだけ調べるときは、次を実行します。

```sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
```

## macOSに止められたとき

ダウンロードしたファイルには、macOSが「インターネットから来たもの」という印を付けます。署名のないプラグインにこの印が付いていると、AEの起動時に「開けません」「開発元を検証できません」などと表示され、読み込まれないことがあります。

このプロジェクトを信頼できる場合は、次の手順で印を外せます。

1. After Effectsを終了します。
2. 「ターミナル」を開き、次を貼り付けて実行します。

   ```sh
   xattr -dr com.apple.quarantine ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLM*.plugin ~/Library/Application\ Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin
   ```

3. After Effectsを起動し直します。

印を外すのはこの10個のプラグインだけにしてください。それでも読み込まれない場合は、表示された文言とmacOSのバージョンを添えて報告してください。

## 最初に確かめること

- 実際に使う色深度（8／16／32 bpc）で、代表的なフレームをレンダーし、Windows版や以前の出力と比べる
- プレビュー解像度を切り替えても、見た目が変わらないか確かめる

## 警告が出たとき

- プラグインの重複：`MediaCore` の中のフォルダーも含めて同じ名前のプラグインを探し、1組だけ残します。バックアップは `MediaCore` の外へ移します。
- プレビュー制御の警告：プラグイン名と警告文を記録して、AEを終了します。Windows版の独自UIの設定や、古いプラグインが残っていないか確かめます。

## アンインストール

After Effectsを終了し、`MediaCore` から10個のOLMプラグインを別の場所へ移します。

## 不具合の報告

次の情報をつけて報告してください。

- macOSとAfter Effectsのバージョン、Apple SiliconかIntelか
- プラグイン名
- 色深度、コンポのサイズ、プレビュー解像度
- すべてのパラメーターの値
- 警告文またはクラッシュログ
- できれば、共有できる最小のプロジェクトと素材

わかっている制限は[既知の制限](../KNOWN_LIMITATIONS.md)を見てください。
