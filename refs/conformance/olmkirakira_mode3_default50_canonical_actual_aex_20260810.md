# OLMKiraKira Mode 3 — UI-default Length 50 canonical rays（2026-08-10）

Mode 3の公開UI既定Length `50`を、source work geometry `5×3`、Glow
Rotation `0°`の標準4方向について閉じた。回転後leafはHorizontal `0°`が
`9×7`、Diagonal `45°`、Diagonal 2 `-45°`、Vertical `90°`が`9×9`となる。

hash `60997c…99f7`のWindows AEXをprocess attachし、50件のCRT initializerを
実行した上で`FUN_181150790`を最後まで実行した。各角度についてforward warp、
Gaussian return、inverse warpを取得し、portable productionと全word一致した。

- 9×7: 各段階63/63 float32 words exact
- 9×9: 各段階81/81 float32 words exact
- 4ケース×3段階: max ULP 0
- 4ケースの最終出力は相互に異なる

Production admissionへ追加するのは`(rw,rh,length)=(9,7,50)`と
`(9,9,50)`だけである。公開経路については4 rayの単独配線、同時集約のMerge 1/
Merge 2呼び出し、PF8/PF16/PF32 writer選択までをソース回帰で固定した。
actual AEXとのraw exact主張はscalar complete chainまでであり、native AEの4 ray
同時最終レンダーや実用解像度へは拡張しない。Length 49/51、9×9 Length 5、
その他geometryは引き続きidentityでfail-closeする。

検証:

```sh
python3 tools/emulation/test_olmkirakira_mode3_default50_canonical_actual_aex_20260810.py
python3 tools/emulation/test_olmkirakira_mode3_nonwhitelist_production_20260806.py
```
