# OLM for Mac リリースノート

2026年11月版（v1.0.0）

[English](RELEASE_NOTES_EN.md)

Windows版のAfter Effectsプラグイン「OLM Tools」をMacに移植した非公式版です。Apple SiliconとIntelの両方で動作するUniversalバイナリで、macOS 11以降に対応しています。

## 同梱プラグイン

ColorKeep、OLMBlur、OLMColorKey、OLMDirectionalBlur、OLMDistanceGradation、OLMKiraKira、OLMRadialBlur、OLMSmoother、OLMSmoother2、OLMToonDilateの10本です。

OLMSmootherは8／16 bpc、その他の9本は8／16／32 bpcに対応しています。

## 検証結果

元のWindows版プラグインと出力を1ビット単位で比較しています。比較方法の詳細は[検証の方法と結果](BETA_SUPPORT.md)をご覧ください。

- Windowsで作成したテスト用プロジェクト（10本、8／16／32 bpc）をMacのAfter Effects 2026で開くと、すべての項目の値がWindowsと一致しました。
- 実際のAfter Effectsで書き出す際に、プラグインがAEから受け取った画像と返した画像を保存し、同じ画像を元のWindows版プラグインに通して比較しました。ずれが生じていた6本の18件すべてで、1ビットの違いもありませんでした。
- 書き出したファイルをWindowsと比較すると、8 bpcでは色の値が最大1ずれることがあります。OLMのエフェクトをすべてオフにしても同様のずれが生じるため、OLMではなくAE側の差異です。16 bpcと32 bpcは一致しました。
- 保存している約3,000件のテストケースのうち、After Effects 2026が使用する描画方式（SmartFX）で元のプラグインと一致しなかったのは2件のみでした。どちらも、元のプラグインが初期化されていないメモリに書き込みを行う不具合によるものです。

## 制限とインストール

GPUレンダーには対応していません。

OLMRadialBlurのNoise TypeをType 3にすると、Mac版は描画せずにエラーになります。元のWindows版はこの設定で未初期化のメモリに書き込む不具合があり、After Effectsごと強制終了することがあるため、Mac版ではこの設定を描画しないようにしています。OLMDirectionalBlurのType 3は描画できますが、元のWindows版は同じ条件でも書き出すたびに結果が変わるため、Windowsと同一の描画結果になるとは限りません。

その他の制限は[既知の制限](../KNOWN_LIMITATIONS.md)にまとめています。

インストールの手順は[インストールガイド](INSTALL_JA.md)をご覧ください。AppleのDeveloper ID署名と公証を受けていないため、Gatekeeperへの対処方法もそちらに記載しています。

## ライセンス

元のOLMプラグインのライセンス（OLM DigitalによるApache License 2.0）を継承しています。本文は[LICENSE](../LICENSE)にあります。これは非公式の移植であり、OLM Digitalとは関係がなく、許可や承認は受けていません。
