# OLM corrected linear-input返却の判定（2026-08-06）

## 結論

修正版fixtureのchannel bindingは正常になった。Windows/Mac、ColorKeep/Kira、
PF8/PF16/PF32の全6行でeffect-off alphaは2,073,600 pixelすべて`1.0`である。
初版にあったR planeのalpha誤bindは解消した。

ただしcross-host raw exactな行はまだ0件である。全6行のeffect-offはalphaが一致し、
RGBは各2,073,600値、合計6,220,800値が異なる。Mac PF32 effect-offはfixtureとraw
exactで、Windows側RGBはMac値に対する単一の約`x^2.4`写像になった。
各深度139入力値について写像競合は0、実効指数中央値は2.3999937前後である。
設定readbackは両hostで同一なので、これは修正版EXRのchannel欠陥ではなく、
Windows/Mac AEの素材／プロジェクト／FLOAT書き出し境界に残るhost変換である。

## ColorKeep

PF8/PF16/PF32すべてで次がexactだった。

- keep maskのhost差: 0 pixel
- 保持: 307,500 pixel
- 棄却: 1,766,100 pixel
- 各host内で保持pixelはeffect-off RGBAをraw維持
- 各host内で棄却pixelはRGBAすべて`+0.0f`
- cross-host effect-on差922,500値は、保持pixelのcontrol RGB差だけで全数説明
- 説明不能差: 0

従ってこの代表ケースではColorKeepの選択・保持・棄却関係を3深度でexactとする。
最終EXR raw exactとはしない。

## OLMKiraKira

effect-onは全深度でRGB各2,073,600値、合計6,220,800値が異なり、alphaだけ一致した。
Mac effect-onの同じraw値が複数のWindows raw値へ対応するため、effect-offで観測した
単一component gamma写像では正規化できない。

追加で、各Windows effect-off EXRを同深度のMac入力にして再実行した。PF32では
Mac controlとWindows controlがraw exactになったが、effect-on RGBは依然として
6,220,800値すべて不一致だった。PF8/PF16は再量子化によりcontrol自体が一致しない。
従ってこの観測からKira演算exactを主張しない。Kiraのoperation exact depthは0件、
追加のinternal-input境界またはhost色変換前のtyped fixtureが必要である。

## 証拠境界

- corrected Windows return SHA-256:
  `517b341eb9a3798bc863d021cde11c5b2e9911f714b2978088f27178e150d5b6`
- corrected Mac return SHA-256:
  `e20eabf453cbf732d5479d2a7bc870645f446c8fae04f627c0836f905396819c`
- 機械可読audit:
  `refs/conformance/olm_crosshost_corrected_return_audit_20260806.json`
- Kira normalized Mac AE replay:
  `refs/conformance/olmkirakira_crosshost_normalized_mac_ae_20260806.json`
- fail-closed bounded verifier:
  `scripts/verify_olm_crosshost_corrected_relation_20260806.py`

この証拠は指定fixture・代表case・AE 26.3x87・Software・PF8/PF16/PF32だけを閉じる。
ColorKeep relation exactを最終pixel exactへ、Kira mismatchを別modeへ一般化しない。
