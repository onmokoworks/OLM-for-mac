# OLM for Mac Public Beta インストールガイド

## 対応環境

- macOS（Apple Silicon／IntelのUniversal bundle）
- Adobe After Effects 26.3x87で主に検証
- CPU Softwareレンダーを基準に検証

他のAfter EffectsバージョンやGPU経路でもロードできる可能性はありますが、現在の
互換性主張には含まれません。

現在のPublic Beta候補はad-hoc署名を検証していますが、Developer ID署名／Appleの
notarizationは未実施です。別のMacへダウンロードしたbundleがGatekeeperに拒否される
可能性があります。警告を無理に回避せず、表示された文言とmacOSバージョンを報告して
ください。

## インストール

1. After Effectsを終了します。
2. 配布ZIPを展開します。
3. ZIP内の10個の`.plugin` bundleを次のフォルダーへコピーします。

   ```text
   ~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
   ```

4. MediaCore内やそのサブフォルダーに、同名プラグインの旧版やバックアップが残って
   いないことを確認します。After Effectsはサブフォルダーも検索するため、バックアップ
   はMediaCoreの外へ移してください。
5. After Effectsを起動し、エフェクトメニューでOLMプラグインを確認します。

開発用リポジトリから安全にインストールする場合は、After Effectsを終了してから次を
実行します。既存bundleはリポジトリ内の無視対象フォルダーへ退避されます。

```sh
scripts/install_mac_plugins_to_mediacore.sh --package /path/to/OLM_Mac_Plugins.zip
```

重複だけを確認する場合：

```sh
scripts/install_mac_plugins_to_mediacore.sh --audit-only
```

## 初回確認

- プロジェクトを複製して開く
- 8／16／32 bpcのうち、実際に使用する色深度を確認する
- 代表フレームをSoftwareレンダーしてWindows版または既存出力と比較する
- 「プラグイン重複」「サポートされていないプレビュー制御」「プロジェクト設定と
  色深度が異なる」などの警告が出た場合は、そのまま制作を続けず記録する

## アンインストール

After Effectsを終了し、MediaCoreから対象の10個のOLM `.plugin` bundleを別の場所へ
移動してください。削除しなくても、MediaCoreの外へ移せばAEの検索対象から外れます。

## 問題報告に必要な情報

- macOS／After Effectsのバージョン
- Apple SiliconまたはIntel
- プラグイン名
- プロジェクト色深度とフレームサイズ
- 全パラメーター値
- 警告文またはクラッシュログ
- 再現可能なら最小AEPと素材（共有可能なものに限る）

既知の制限は[KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md)を確認してください。
