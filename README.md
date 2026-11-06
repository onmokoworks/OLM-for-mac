# OLM for Mac

[English](README.en.md)

Windows版After Effectsプラグイン「OLM Tools」をMacで利用できるようにした非公式の移植版です。Apple SiliconとIntelのどちらのMacでも動作します。

> [!WARNING]
> 重要な作業に使用する前に、必ずプロジェクトのバックアップを作成してください。

## 対応プラグイン

| プラグイン | 色深度 | 注意点 |
|---|---|---|
| ColorKeep | 8／16／32 bpc | |
| OLMBlur | 8／16／32 bpc | |
| OLMColorKey | 8／16／32 bpc | |
| OLMDirectionalBlur | 8／16／32 bpc | |
| OLMDistanceGradation | 8／16／32 bpc | |
| OLMKiraKira | 8／16／32 bpc | |
| OLMRadialBlur | 8／16／32 bpc | 回転モードを高品質で使用すると処理負荷が高くなり、1080pでは1フレームあたり1分以上かかることがあります |
| OLMSmoother | 8／16 bpc | 32 bpcには非対応です（Windows版も同様です）。32 bpcのコンポジションでは、After Effectsが色深度を変換して渡します |
| OLMSmoother2 | 8／16／32 bpc | |
| OLMToonDilate | 8／16／32 bpc | |

## Windows版との互換性

同一の素材および設定であればWindows版と1ビットの差異もない出力となるよう、元のプラグインを解析しながら開発しています。

エミュレーター上で動作させた元のプラグインの結果とMac版の結果を、ランダムに選んだ素材、設定、サイズ、プレビュー解像度の組み合わせで数千通り比較しています。Windows版で描画できる条件では、すべて一致しています。詳細については[検証の方法と結果](docs/BETA_SUPPORT.md)を、判明している制限については[既知の制限](KNOWN_LIMITATIONS.md)をご確認ください。

## 動作環境

- macOS 11以降に対応しています。
- After Effects 2026（26.3）で動作を確認しています。その他のバージョンは未確認です。
- CPUレンダーのみに対応しています（GPUレンダーには非対応です）。

## インストール

After Effectsを終了してから、配布ZIPファイル内の10個の `.plugin` を次のフォルダーにコピーしてください。

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

> [!NOTE]
> Appleによる署名と公証を受けていないため、macOSのGatekeeperから警告ダイアログが表示され、プラグインの読み込みがブロックされることがあります。署名と公証には有料のApple開発者登録が必要なため、現在のところ予定はありません。ブロックされた場合の対処法や詳しい手順については、[インストールガイド](docs/INSTALL_JA.md)をご確認ください。

## 不具合の報告

[Issues](https://github.com/onmokoworks/OLM-for-mac/issues)からご報告ください。以下の情報をお知らせいただけますと助かります。

- macOSとAfter Effectsのバージョン、MacがApple SiliconかIntelか
- プラグイン名、色深度、コンポジションのサイズ、プレビュー解像度
- エフェクトの設定値
- 再現手順、警告メッセージやクラッシュログ
- 共有可能な場合は、最小限のプロジェクトと素材

Windows版と見た目が異なる場合は、同一の素材・同一の設定で書き出したWindows版の画像も添えていただけますと、原因を特定しやすくなります。

## ライセンス

- 本移植版は、元のOLMプラグインのライセンス（OLM DigitalによるApache License 2.0）を継承しています。ライセンス本文は[LICENSE](LICENSE)に記載されています。
- 本プラグインは非公式の移植版であり、OLM Digitalとは関係がなく、許可や承認を受けたものではありません。
