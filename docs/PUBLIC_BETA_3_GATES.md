# Public Beta 3ゲート

Public Betaの判断基準は、全10プラグインで次の3つに固定する。個別fixture、SHA、
geometry、parameter cellは各ゲートを支える証拠であり、新しい完了基準ではない。

1. **安全性** — 任意の画素内容、合法rowbytes、宣言geometryで範囲外アクセスや部分commitがない。
2. **主要操作** — 対応表に記載した深度、Classic/Smart経路、主要パラメータが一般入力で動く。
3. **互換性・実機** — Windows代表oracleとの差が管理され、macOS After EffectsでRC artifactを確認する。

`通過`は現行ソースの証拠が揃った状態、`限定`は公開可能な明記済み範囲がある状態、
`未完`はPublic Beta RCまでに追加証拠または明示的な既知差分判断が必要な状態を表す。

| プラグイン | 安全性 | 主要操作 | 互換性・実機 | RCまでの残件 |
|---|---|---|---|---|
| ColorKeep | 通過 | 限定 | 限定 | 3深度Windows 5色worker代表は現行callback exact。現行RC native AE |
| OLMBlur | 通過 | 限定 | 限定 | 現行RC native AE。Classic 32 bpcは非対応 |
| OLMColorKey | 通過 | 限定 | 限定 | Thin＋Blur同時指定を既知差分として維持。現行RC native AE |
| OLMDirectionalBlur | 通過 | 限定 | 限定 | generic DualのWindows代表確認と現行RC native AE |
| OLMDistanceGradation | 通過 | 限定 | 限定 | PF32 Power/Bilateralは既知差分。現行RC native AE |
| OLMKiraKira | 通過 | 限定 | 限定 | generic Mode 3の代表Windows確認と現行RC native AE |
| OLMRadialBlur | 通過 | 限定 | 限定 | 一般topologyの代表Windows確認と現行RC native AE |
| OLMSmoother | 通過 | 限定 | 限定 | PF16 Windows実用代表は現行Classic/Smart exact。現行RC native AE |
| OLMSmoother2 | 通過 | 限定 | 限定 | classifier近似を既知差分として維持。現行RC native AE |
| OLMToonDilate | 通過 | 限定 | 限定 | 3深度Windows corner-seed代表は現行core exact。現行RC native AE |

詳細な対応範囲は [BETA_SUPPORT.md](BETA_SUPPORT.md) をauthorityとする。この表は
進捗を一目で判断する索引であり、個別テストが増えても行・列・完了基準を増やさない。
