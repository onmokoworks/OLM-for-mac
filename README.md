# OLM for Mac

[English](README.en.md)

Windows版のAfter Effectsプラグイン「OLM Tools」をMacで使えるようにした、非公式の移植版です。Apple SiliconとIntelのどちらのMacでも動きます。

> [!WARNING]
> Beta版です。仕事や制作で使う前に、必ずバックアップを取るなどして、データ破損などのリスクに備えてください。

## 対応プラグイン

| プラグイン | 色深度 | 注意点 |
|---|---|---|
| ColorKeep | 8／16／32 bpc | |
| OLMBlur | 8／16／32 bpc | |
| OLMColorKey | 8／16／32 bpc | |
| OLMDirectionalBlur | 8／16／32 bpc | |
| OLMDistanceGradation | 8／16／32 bpc | |
| OLMKiraKira | 8／16／32 bpc | |
| OLMRadialBlur | 8／16／32 bpc | 回転モードを高品質で使うと重く、1080pで1フレーム1分以上かかることがあります |
| OLMSmoother | 8／16 bpc | 32 bpcには非対応です（Windows版も同じ）。32 bpcのコンポでは、AEが色深度を変換して渡します |
| OLMSmoother2 | 8／16／32 bpc | |
| OLMToonDilate | 8／16／32 bpc | |

## Windows版との互換性

同じ素材・同じ設定なら**Windows版と1ビットも変わらない出力**になるよう、元のプラグインを解析しながら開発しています。

元のプラグインをエミュレーターで動かした結果とMac版の結果を、ランダムに選んだ素材・設定・サイズ・プレビュー解像度で数千通り比べていて、Windows版が描画できる条件ではすべて一致しています。くわしくは[検証の方法と結果](docs/BETA_SUPPORT.md)を、わかっている制限は[既知の制限](KNOWN_LIMITATIONS.md)を見てください。

## 動作環境

- macOS 11以降
- After Effects 2026（26.3）で確認しています。ほかのバージョンは未確認です
- CPUレンダーのみ（GPUレンダーには非対応）

## インストール

After Effectsを終了してから、配布ZIPの中の10個の `.plugin` を次のフォルダーにコピーしてください。

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

> [!NOTE]
> Appleの署名と公証を受けていないので、macOSに止められることがあります。受けるには有料のAppleの開発者登録が必要なため、今のところ予定はありません。止められたときの対処や、くわしい手順は[インストールガイド](docs/INSTALL_JA.md)を見てください。

## 不具合の報告

[Issues](https://github.com/onmokoworks/OLM-for-mac/issues)から報告してください。次の情報があると助かります。

- macOSとAfter Effectsのバージョン、MacがApple SiliconかIntelか
- プラグイン名、色深度、コンポのサイズ、プレビュー解像度
- エフェクトの設定値
- 再現手順と、警告文やクラッシュログ
- 共有できるなら、最小限のプロジェクトと素材

Windows版と見た目が違うときは、同じ素材・同じ設定で書き出したWindows版の画像も添えてもらえると、原因を探しやすくなります。

## ライセンス

- 元のOLMプラグインは、OLM DigitalがApache License 2.0で公開しているものです。この移植版も同じ[Apache License 2.0](LICENSE)です。
- これは非公式の移植で、OLM Digitalとは関係がなく、許可や承認も受けていません。
