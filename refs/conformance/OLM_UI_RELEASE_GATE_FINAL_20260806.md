# OLM Mac UI・統合ゲート最終記録（2026-08-06）

## 結果

最新の `main` とインストール済み10プラグインに対し、総合リリースゲートは
`release_gate_pass`（`releasable: true`）となった。

- 固定fixture回帰: 10 / 10（423.84秒）
- Universal・署名・単一bundle・受理済みSHA: 10 / 10
- Windows AEX由来のparameter UI登録ゲート: 10 / 10
- 現行Mac AEの代表ロード／レンダー証拠: 10 / 10
- AE 26.3でのfresh PNG smoke: 10 / 10

機械可読な結果は
[`olm_release_gate_status_20260806.json`](olm_release_gate_status_20260806.json)、
UI登録面の詳細と証拠境界は
[`OLM_PARAMETER_UI_PARITY_NOTES_20260806.md`](OLM_PARAMETER_UI_PARITY_NOTES_20260806.md)
を参照する。

## 今回閉じた問題

- OLM Color Keyはactual AEXの全223 parameter行とGLOBAL_SETUPへ正規化後0差分。
- OLM RadialBlurの不正なプレビュー制御表示を解消し、公開parameter面をactual AEXへ一致。
- OLM Kira Kiraのpopup・Ramp登録値をactual AEXへ一致。
- OLM DirectionalBlurはactual defaultの`Noise Layer=None`を正しく扱い、fresh host renderを復旧。
- 各テストに散在していた旧installed SHA直書きを廃止し、受理済みidentity manifestへ統一。
- 最小AE smokeは既存PNGを成功扱いしないよう、各レンダー前のstale出力削除を必須化。

## 完全一致を主張しない境界

このPASSは、manifestと各証拠に列挙したAEバージョン、Softwareレンダー、bit-depth、
geometry、入力、parameter tupleに限る。未列挙の組合せへ一般化しない。

parameter UI登録ゲートのうち、次は明示的なbounded証拠である。

- ColorKeep: hostless AEX実行では各行の表示名bindingを観測できない。
- OLM Kira Kira: 展開後RampのDrawbot描画・操作をMac AEで網羅していない。
- OLM RadialBlur: Windowsのcustom UI event lifecycle自体は未移植。

したがって、raw登録面の一致とMac AE上の全視覚・全操作の一致は同一の主張ではない。
