# OLMKiraKira Mode 3 — 9×7 length family（2026-08-10）

Mode 3 の回転後scalar geometryを9×7に固定し、公開Lengthの代表的な奇数値
3、5、7、9を一つのfamilyとして閉じた。

各値についてhash `f7b08b…50f78` のWindows AEX内Gaussian本体を実行し、callerへ
戻った直後の63個のfloat32 wordを取得した。Mac productionと同じ
`HorizontalGaussian::prepare_actual_aex_nonfused`経路は、各fixtureに対して
63/63 word完全一致する。4出力のSHA-256は相互に異なり、Lengthが実際に処理へ
反映されていることも確認した。

この証拠でproduction admissionへ追加するのは `(rw, rh) = (9, 7)` かつ
`Length ∈ {3, 5, 7, 9}` のみである。別geometry、偶数Length、11以上、実用解像度、
およびnative AE全体の出力へは一般化しない。未証明tupleは引き続きidentityで
fail-closeする。

検証:

```sh
python3 tools/emulation/test_olmkirakira_mode3_9x7_length_family_actual_aex_20260810.py
python3 tools/emulation/test_olmkirakira_mode3_nonwhitelist_production_20260806.py
```
