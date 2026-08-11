# OLMKiraKira Mode 4 natural full-frame boundary（2026-08-11）

Status: **fail-closed pending same-run source binding**

actual AEX `FUN_18114f4a0` の 5×3 multi-row fixture は、Mode 4 directional
rayを自然生成し、5層aggregate入口まで到達した。既存probeにはMatの先頭行だけを
pixel列として扱う欠陥があり、4×1 Highlight fixtureでは見えなかった。この欠陥は
full row-major flattenへ修正し、既存4×1 Highlight→aggregate→PF8/PF16/PF32の
raw-exact gateが維持されることを確認した。

ただし、この試走だけではfull caller内のvtable-owned seed生成とdirection/rotation
配列をMac productionの入力へ同一実行で結べない。したがって5×3 directionalの
natural full-frame raw exactは宣言せず、現行productionのgeometry-general admissionも
既存17 actual-AEX helper-chain fixtureの境界を越えて拡張しない。

再開に必要な最小witnessは、同じfull caller実行から次を採取する1ケースである。

- vtable seed出力の全5×3 FLOAT32 words
- 選択されたdirection slot、length、rotation
- aggregate入口の該当ray全5×3 FLOAT32 words

この3点があれば、既存のMode 4 portable chain、5-case compose matrix、typed writerへ
連結し、PF8/PF16/PF32のbounded natural full-frame gateを推測なしで閉じられる。

Verification:

```sh
python3 -m unittest \
  tests.test_olmkirakira_mode4_fullcaller_multiline_fixture_20260811 \
  tests.test_olmkirakira_mode4_fullcaller_hostless_exact_20260807 \
  tests.test_olmkirakira_mode4_compose_matrix_actual_aex_20260811
python3 tools/emulation/test_olmkirakira_mode4_canonical_angles_actual_aex_20260810.py
```
