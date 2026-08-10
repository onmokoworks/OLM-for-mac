# OLMKiraKira Mode 3 geometry-general contract（2026-08-10）

Mode 3のhard legal Length `1..1000`について、rotated leafが最低`9×7`
以上ならgeometry-generalとしてproductionへ接続した。

Windows AEX hash `60997c…99f7`をprocess attachし、50件のCRT initializerを
実行した上で、次のleafをactual `FUN_181150790`の最後まで実行した。

- source 32×18由来: 36×22、39×30、39×39
- source 64×36由来: 68×40、74×74、75×57
- angle: 0°、45°、-45°、非標準17°
- Length: 1、2、3、5、7、9、11、25、50、100、200、300、301、1000

66ケースのforward warp、Gaussian return、inverse warp、合計497,250個の
float32 wordがportable productionと完全一致した。幅36/39/68/74/75により
奇数・偶数と複数の剰余class、正方形・非正方形を含む。productionの
actual-AEX profileはgeometry別の分岐を持たず、同じreflect101 scalar loopを使う。

UI slider上限は300だがhard上限は1000であり、301と1000もactual exactである。
Length 0は公開zero-ray skip、Length 1は専用five-tap SIMD丸め、Length 2..1000は
generic non-fused経路を使う。

一般contract外のLength 1001以上、leaf 9×7未満、および既存の個別fixtureにも含まれない
tupleは引き続き明示predicateでfail-closeし、Mode 2へ置換しない。PF8/PF16/PF32
writerへの公開routeは回帰で固定するが、native AE最終renderの一致はこの証拠に
含めない。

検証:

```sh
python3 tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py
python3 tools/emulation/test_olmkirakira_mode3_nonwhitelist_production_20260806.py
```
