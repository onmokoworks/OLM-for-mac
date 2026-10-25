# OLM for Mac

[English](README.en.md)

Windows版のAfter Effectsプラグイン「OLM Tools」を、macOS（Apple Silicon／Intel）で使えるように移植する非公式プロジェクトです。

> [!WARNING]
> 現在はPublic Betaです。大切なプロジェクトで使う前に、必ず複製を作って出力を確かめてください。

## 対応プラグイン

| プラグイン | 色深度 | 注意点 |
|---|---|---|
| ColorKeep | 8／16／32 bpc | |
| OLMBlur | 8／16／32 bpc | |
| OLMColorKey | 8／16／32 bpc | |
| OLMDirectionalBlur | 8／16／32 bpc | |
| OLMDistanceGradation | 8／16／32 bpc | |
| OLMKiraKira | 8／16／32 bpc | |
| OLMRadialBlur | 8／16／32 bpc | 回転モードを高品質で使うと、1080pで1フレームに1分以上かかることがあります |
| OLMSmoother | 8／16 bpc | Windows版も32 bpcには対応していません。32 bpcのコンポでは、AEが色深度を変換して渡します |
| OLMSmoother2 | 8／16／32 bpc | |
| OLMToonDilate | 8／16／32 bpc | |

## Windows版との互換性

目指しているのは、**同じ素材・同じ設定なら、Windows版と1ビットも違わない出力**です。

- 元のWindows版プラグイン（`.aex`）をエミュレーター上で動かし、その出力とMac版の出力をバイト単位で比べています。
- 素材、設定値、コンポのサイズ（奇数・偶数）、プレビュー解像度（フル〜1/8）、拡大表示などの部分的な描画をランダムに組み合わせ、数千件を試しています。Windows版が描画できる条件では、すべて一致しています。
- Windows版自身がエラーになる設定では、Mac版も描画しないことがあります。

検証の方法と結果は[対応範囲と検証](docs/BETA_SUPPORT.md)、わかっている制限は[既知の制限](KNOWN_LIMITATIONS.md)にまとめています。

## 動作環境

- macOS 11以降（Apple Silicon／Intel）
- Adobe After Effects 2026（26.3）で主に確認しています
- CPUレンダー（GPUレンダーは対象外です）

## インストール

After Effectsを終了し、配布ZIPに入っている10個の `.plugin` を次のフォルダーへコピーします。

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

同じ名前の古いプラグインが残っていると、AEが重複のエラーを出します。くわしくは[インストールガイド](docs/INSTALL_JA.md)を見てください。

> [!NOTE]
> 今のプラグインは、Appleの開発者署名と公証（notarization）を受けていません。ダウンロードしたプラグインを、macOSのGatekeeperが止めることがあります。

## 不具合の報告

[Issues](https://github.com/onmokoworks/OLM-for-mac/issues)から、次の情報をつけて報告してください。

- macOSとAfter Effectsのバージョン、Apple SiliconかIntelか
- プラグイン名、色深度、コンポのサイズ、プレビュー解像度
- エフェクトの設定値
- 再現する手順と、警告文またはクラッシュログ
- できれば、共有できる最小のプロジェクトと素材

「Windows版と見た目が違う」という報告では、同じ素材・同じ設定でのWindows版の出力があると、原因を探しやすくなります。

## ライセンスと権利

- これは**非公式の移植**です。元のプラグインを制作したOLM Digitalとは関係がなく、許可や承認も受けていません。
- 「OLM」などの名前やロゴ、元のWindows版プラグインの権利は、OLM Digitalなど、元の権利者のものです。
- このリポジトリのコードは、[Apache License 2.0](LICENSE)で公開しています。ライセンスの条件を守れば、使う・直す・配ることができます。
- ただし、このライセンスで使えるのは**このリポジトリのコードだけ**です。OLMの名前やロゴ、元のWindows版プラグインを自由に使ってよいという意味ではありません。
