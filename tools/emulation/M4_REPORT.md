## M4到達点
- `FUN_180008690 -> FUN_180007520 -> FUN_180004640` を case_0010 実入力 `1920x1080` で emulation 実行した。
- 実行モードは `fast=True`。壁時計は 909.91s。
- reader provenance は 21 call を捕捉し、`param_2` は実バイナリの `FUN_180008690` 本体に構築させた。
- `FUN_180004640` 入口の実引数は `param_1=0xf0c25c0`, `param_2=0x400003c0`。
- `param_1[0]` = 0.200000003 -> `iVar29=1800`。
- witness buffers: `f250=0x268e4800`, `f252=0x28737000`, `+0xe=0x28ecba00`。
- output witness `(1614,6)` ARGB bytes `(0, 0, 0, 0)`, RGBA `(0, 0, 0, 0)`。
- direct inverse sample `(1614,6)`: radius=844.317504883, angle=5.598455906, angle_scale=286.478912354, radius_base=0, sample=(1603.839558785, 844.317504883), `+0xe` RGBA float=(-0.004081939, -0.004081939, -0.004081939, 1.0), u8=(0, 0, 0, 255).

## ビット照合結果
- Summary: exact `2/4`, <=1 ULP RGB with alpha exact `4/4`.
- row844 col1603: 乖離 (+0xe got `bc70f44c bc70f44c bc70f44c 3f800000` vs win RGB=`bc70f44b` A=`3f800000`; f250=(-0.02561707, -0.02561707, -0.02561707, 1.741865993), f250.rgb/f250.a=(-0.014706683, -0.014706683, -0.014706683, 1.0), f252_raw=(0.0, 0.0, 0.0, 1.0), rgb_ulps=(1, 1, 1), alpha_ulp=0; 乖離開始段: FUN_180004640 / downstream scatter-gather)
- row845 col1603: 一致 (+0xe RGBA bits `bd46d045 bd46d045 bd46d045 3f800000`; RGB=`bd46d045`, A=`3f800000`; f250=(-0.084547505, -0.084547505, -0.084547505, 1.741865993), f250.rgb/f250.a=(-0.048538467, -0.048538467, -0.048538467, 1.0), f252_raw=(0.0, 0.0, 0.0, 1.0), rgb_ulps=(0, 0, 0), alpha_ulp=0)
- row843 col1601: 一致 (+0xe RGBA bits `3dd69702 3dd69702 3dd69702 3f800000`; RGB=`3dd69702`, A=`3f800000`; f250=(0.168332621, 0.168332621, 0.168332621, 1.606530666), f250.rgb/f250.a=(0.104780211, 0.104780211, 0.104780211, 1.0), f252_raw=(0.0, 0.0, 0.0, 1.0), rgb_ulps=(0, 0, 0), alpha_ulp=0)
- row843 col1602: 乖離 (+0xe got `3de119cf 3de119cf 3de119cf 3f800000` vs win RGB=`3de119ce` A=`3f800000`; f250=(0.191452861, 0.191452861, 0.191452861, 1.741865993), f250.rgb/f250.a=(0.109912509, 0.109912509, 0.109912509, 1.0), f252_raw=(0.0, 0.0, 0.0, 1.0), rgb_ulps=(1, 1, 1), alpha_ulp=0; 乖離開始段: FUN_180004640 / downstream scatter-gather)

## Extra +0xe Dump Cells
- row844 col1604: +0xe bits `00000000 00000000 00000000 3f800000`, f250=(0.0, 0.0, 0.0, 1.741865993)
- row845 col1604: +0xe bits `00000000 00000000 00000000 3f800000`, f250=(0.0, 0.0, 0.0, 1.741865993)

## promotion 機序
- Windows typed cells とローカル emulation は全セル <=1 ULP まで一致した。scatter entry 観測: `0x180002780` rcx=0xf0c25c0 rdx=0x28ecba00 r8=0x2b4b2c00 r9=0x2bc47600 stack5=0x708, `0x1800024c0` rcx=0xf0c25c0 rdx=0x28ecba00 r8=0x2b4b2c00 r9=0x2ad1e200 stack5=0x2c3dc000
- 残る 1 ULP は libm / FMA / fast-math 系の丸め差候補で、promotion 機序の判定には十分な ground truth として扱える。
- ただし本 run では `FUN_180002780 / FUN_1800024c0` 内の witness-angle promotion 条件分岐までは未分解で、bright lobe が col1604 へ届く具体条件の確定には追加の段階 dump が残る。

## Mac 港への含意
- AEX の座標変換と `+0xe` direct sampler は witness `(1614,6)` を黒として返す。これは 20260604 PNG 参照の白とは一致しない。
- よって、この witness だけを根拠に Mac 側 scatter を白へ寄せる変更は危険。まず Windows PNG が CPU AEX Software 経路そのものか、またはGPU/旧AEX/manifest混入かを分離する必要がある。

## 残課題
- case_0010 witness `(1614,6)` は `reference-path-split suspected` として扱う。PNG白へ合わせ込む前に、同一AEX/Software/EXRまたはCPU writeback witnessで参照経路を確定する。
- 追加解析する場合は、`FUN_180001b10 -> FUN_180001000(+0xe)` の direct sample 黒を起点に、PNG参照生成時のAEXバージョン/レンダー経路/入力manifestを監査する。
