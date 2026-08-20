# OLM for Mac

Windows版のAfter Effectsプラグイン「OLM Tools」を、macOS向けのUniversalプラグインとして移植する非公式プロジェクトです。

> [!WARNING]
> 現在はPublic Betaです。重要なプロジェクトでは必ず複製を作り、出力を確認してから使用してください。

## 対応プラグイン

- ColorKeep
- OLMBlur
- OLMColorKey
- OLMDirectionalBlur
- OLMDistanceGradation
- OLMKiraKira
- OLMRadialBlur
- OLMSmoother
- OLMSmoother2
- OLMToonDilate

## 対応環境

- macOS（Apple Silicon／Intel Universal）
- Adobe After Effects 26.3で主に検証
- CPU Softwareレンダー

GPUレンダーや他のAfter Effectsバージョンについては、現在の互換性保証に含まれません。

## インストール

After Effectsを終了し、配布ZIP内の `.plugin` を次のフォルダーへコピーします。

```text
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

詳しい手順は[インストールガイド](docs/INSTALL_JA.md)を参照してください。

## 現在の制限

Windows版の全入力・全設定に対する完全互換を保証するものではありません。未検証の条件では、処理を安全に停止する場合があります。

現在のバイナリはDeveloper ID署名およびAppleのnotarizationを行っていないため、Gatekeeperに拒否される可能性があります。

詳しくは[既知の制限](KNOWN_LIMITATIONS.md)を参照してください。

## 不具合報告

[Issues](https://github.com/onmokoworks/OLM-for-mac/issues)から、次の情報を添えて報告してください。

- macOSとAfter Effectsのバージョン
- Apple SiliconまたはIntel
- プラグイン名、色深度、フレームサイズ
- エフェクトの設定値
- 再現手順、警告文またはクラッシュログ
- 共有可能な最小プロジェクトと素材

## ライセンスと権利表記

本プロジェクトはOLM Digitalによる提携・承認を受けたものではありません。名称、商標および原著作物に関する権利は、それぞれの権利者に帰属します。

収録コードの利用条件は[Apache License 2.0](LICENSE)を参照してください。このライセンスは、本家の名称、商標、バイナリ、素材などに別途の権利を付与するものではありません。
