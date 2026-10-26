# OLM for Mac リリースノート

2026年10月版・Beta

[English](RELEASE_NOTES_EN.md)

Windows版のAfter Effectsプラグイン「OLM Tools」をMacに移植した非公式版です。Apple SiliconとIntelの両方で動くUniversalバイナリで、macOS 11以降に対応しています。

## 同梱プラグイン

ColorKeep、OLMBlur、OLMColorKey、OLMDirectionalBlur、OLMDistanceGradation、OLMKiraKira、OLMRadialBlur、OLMSmoother、OLMSmoother2、OLMToonDilateの10本です。

OLMSmootherは8／16 bpc、ほかの9本は8／16／32 bpcに対応しています。

## v0.2.0-beta.1 からの変更

出力は変わっていません。特定の入力だけに合わせた古い処理を消して、コードを約5,000行減らしました。

## 8月のBeta版からの変更

- プレビュー解像度を下げたときや、画像の一部だけを描くときに、黒いフレームになる問題を直しました。
- OLMKiraKiraのグラデーション編集と、設定に応じて項目を隠したり無効にしたりする動きを、元のプラグインと同じにしました。
- 重い設定の処理を速くしました。OLMDirectionalBlurの重い設定では、1080pで1フレーム約18秒かかっていたのが約1.4秒になりました。

## 検証結果

元のWindows版プラグインと出力を1ビット単位で比べています。比べ方の詳細は[検証の方法と結果](BETA_SUPPORT.md)を見てください。

- 元のプラグインと比べた2,000件のうち、元のプラグインが描画できた1,854件はすべて一致しました。
- Apple Silicon用とIntel用で、出力の差は0件でした。Intel用はRosettaで動かしたもので、Intel Macの実機では確かめていません。
- After Effects 2026で、10本ともフル〜1/4解像度で描画できることを確かめました。

## 制限とインストール

GPUレンダーには対応していません。ほかの制限は[既知の制限](../KNOWN_LIMITATIONS.md)にまとめています。

インストールの手順は[インストールガイド](INSTALL_JA.md)を見てください。AppleのDeveloper ID署名と公証はしていないので、Gatekeeperへの対処もそこに書いています。

## ライセンス

元のOLMプラグインのライセンス（OLM DigitalによるApache License 2.0）を継承しています。本文は[LICENSE](../LICENSE)にあります。これは非公式の移植で、OLM Digitalとは関係なく、許可や承認は受けていません。
