# OLMKiraKira Mode 4 compose交差matrix（2026-08-11）

Status: **exact**

Mode 4のactual AEX directional ray（radius 1／5）とHighlight rayを、recover済みの
Merge 1／Merge 2 aggregate、ramp sampler、PF8／PF16／PF32 compose・writerへ接続した。
全5代表ケースでaggregate 320 bytes、typed output 560 bytesがportable ownerとraw exact、
最大ULPは0だった。

代表matrixは、Length 1、通常色／非default色、Directional＋Highlight、Diagonal2＋Highlight、
半透明・HDR source、Merge 1／2、ramp off／1本／2本を含む。既存のgeometry・angle・length
17ケースおよびramp補間7ケースと重なる全直積は増やしていない。

この交差監査で次のproduction差分を修正した。

- Mode 3／4の非identityなLength 1を、共通の早期returnでidentity化していた。
- actual full callerはDirectional 4本の後にHighlightを加算するが、productionは
  HighlightをDiagonal2より先に加算していた。float32加算順をactualへ合わせた。

境界は、チェックイン済みWindows AEXをMac上のUnicornで実行したhostless証拠であり、
Windows AE実機レンダーの一般一致主張ではない。極小geometryおよび証明外入力の
fail-closeは維持する。

Verification:

```sh
python3 -m unittest tests.test_olmkirakira_mode4_compose_matrix_actual_aex_20260811
```
