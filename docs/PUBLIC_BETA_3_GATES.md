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
| ColorKeep | 通過 | 限定 | 限定 | baselineに加え、count 100＋100番目の色をSmart HD/4K×8/16/32 native AEで6/6通過。Windows実AEXのcount 5/100末尾色境界は3深度hostless exact。Classic native AEと全1–100色の数値一致は未完 |
| OLMBlur | 通過 | 限定 | 限定 | baselineに加えRepeat 10＋Legacy onをSmart HD/4K×8/16/32 native AEで6/6通過。同tupleはWindows実AEX→Mac Smartで3深度exact。Classic 32 bpcは非対応 |
| OLMColorKey | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。Thin＋Blur同時指定を既知差分として維持 |
| OLMDirectionalBlur | 通過 | 限定 | 限定 | baseline HD/4K×8 bpcを2/2、別の主要操作Dual profileをHD/4K×8/16/32で6/6 native AE通過。generic DualのWindows代表確認は未完 |
| OLMDistanceGradation | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。PF32 Power/Bilateralは既知差分 |
| OLMKiraKira | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。generic Mode 3の代表Windows確認は未完 |
| OLMRadialBlur | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。一般topologyの代表Windows確認は未完 |
| OLMSmoother | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16を4/4 native AE通過。PF16 Windows実用代表は現行Classic/Smart exact |
| OLMSmoother2 | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。classifier近似を既知差分として維持 |
| OLMToonDilate | 通過 | 限定 | 限定 | 現行binaryのSmart HD/4K×8/16/32を6/6 native AE通過。3深度Windows corner-seed代表は現行core exact |

詳細な対応範囲は [BETA_SUPPORT.md](BETA_SUPPORT.md) をauthorityとする。この表は
進捗を一目で判断する索引であり、個別テストが増えても行・列・完了基準を増やさない。
宣言済みnative AE matrixは2026-08-23時点で54/54成功し、全publication commitをconsumer-timeで
再検証済み。集約証拠は
[`olm_native_ae_declared_matrix_54_20260823.json`](../refs/conformance/olm_native_ae_declared_matrix_54_20260823.json)。
