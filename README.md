# OLM for Mac

OLM Tools の Windows 版 After Effects plug-in を、現行 macOS / Apple
Silicon / After Effects 向けに移植するための作業リポジトリです。

この repo では、単に「似た出力」を作るのではなく、Windows AE の
Software render を基準にして、Mac AE 上で同じ入力・同じパラメータ・同じ
bit depth の出力が一致することを目標にしています。

## 目標

最終完了は `AE exact` のみです。

- Windows AE Software render の参照 PNG と Mac AE render が `max_diff=0`
- 8bpc を固めてから、16bpc、32bpc へ広げる
- PNG 差分だけで合わせ込まず、Ghidra / objdump / runtime trace で
  定数・分岐・丸め・境界処理を説明する
- 実装だけでなく、binary-grounded IR と conformance suite も残す

`CLI exact` は強い中間証拠ですが、最終完了ではありません。
`off-by-1`、tolerance gate、guarded、known-red probe も完了扱いしません。

## 現状

Mac plug-in project は 10 本あります。

- `ColorKeep`
- `OLMBlur`
- `OLMColorKey`
- `OLMDirectionalBlur`
- `OLMRadialBlur`
- `OLMKiraKira`
- `OLMToonDilate`
- `OLMDistanceGradation`
- `OLMSmoother`
- `OLMSmoother2`

現在の大まかな状態です。ここでの `AE exact` は、packaged 8bpc
AE-host validation で Mac AE 出力が Windows AE Software 参照に
`max_diff=0` で一致した、という意味です。全bit depth完了や全機能完了を
意味しません。

| 範囲 | 状態 |
| --- | --- |
| Mac plug-in project | 10 本とも Debug universal bundle としてビルド可能 |
| OLMBlur | 8bpc packaged slice は Mac AE exact。16bpc Mac AE は 0/7 exact で、現在は sparse high-amplitude residual を調査中。残る CLI `max=1` は runtime trace で binary-grounding 中 |
| OLMToonDilate | 8bpc packaged slice は Mac AE exact |
| OLMDistanceGradation | basic / extended / blur の 8bpc packaged slice は Mac AE exact。16bpc Mac AE は Inside/all-opaque no-source 修正後 9/29 exact で、Render Mode / background / interpolation 系を調査中 |
| OLMColorKey | core / Edge Thin / Edge Blur の normalized 8bpc packaged slice は Mac AE exact。16bpc Mac AE は Force Lower Precision epsilon 修正後 8/9 exact。残りは `case_0009` の Edge Thin / border path 寄り。古い 20260604 Edge Blur 残差は reference-generation split として扱う |
| OLMSmoother2 | no-key grid は 8bpc Mac AE exact。legacy current-AEX recapture 済み。key/gamma は Smooth Range threshold 昇格で大幅改善、残る局所残差を調査中 |
| OLMSmoother v1 | 960x540 再検証で 8bpc Mac AE exact。v2 互換扱いへ寄せる判断は別途 |
| OLMDirectionalBlur | 参照は多いが、まだ blocked。2026-06-25 witness plan で angle-0 と diagonal の2系統に分け、PNG-only tuning は止めて asm/runtime evidence 待ち |
| OLMRadialBlur | Zoom は alpha normalization 残差、tiny Rotation は sampler/validity 残差。Inner は typed `FUN_180001c90` per-cell witness 待ち |
| OLMKiraKira | BT.709 seed、OpenCV 4.5.5 AVX2、ray-helper、`FUN_18114fd90` aggregation まで grounding 済み。2026-06-25 再取込でも fd90 は確認済み。残りは merge-mode compose / pre-writeback / final quantization |

詳しい台帳は `notes/CONFORMANCE_LEDGER.md`、IR の入口は
`notes/IR_INDEX_20260621.md`、用語定義は
`notes/AE_EXACT_CONFORMANCE.md` にあります。

packaged 8bpc AE-host validation の最小M0集計は機械生成します。
現在の manifest は `refs/conformance/packaged_8bpc_manifest.json` です。
summary は `python3 scripts/generate_conformance_summary.py` で
`refs/reports/conformance_summary_packaged_8bpc.md` にローカル生成します。
この集計では 70 ケースを `reference_kind` / `runner_kind` /
`result_status` に分け、`AE exact` と known-red / residual を混ぜません。
OLMBlur の 8bpc 判断は `refs/conformance/olmblur_8bpc_decision.md` に固定し、
`preserve-normalized-ae-exact` として扱います。
OLMColorKey Edge の 8bpc 判断は
`refs/conformance/olmcolorkey_edge_8bpc_decision.md` に固定し、
古い 20260604 Edge Blur 残差は `reference-generation split` として扱います。
OLMDistanceGradation の 8bpc 判断は
`refs/conformance/olmdistancegradation_8bpc_decision.md` に固定し、
normalized 8bpc 29/29 exact と古い参照だけの drift を分けて扱います。
RadialBlur / KiraKira / DirectionalBlur の 8bpc 判断は、それぞれ
`refs/conformance/olmradialblur_8bpc_decision.md`、
`refs/conformance/olmkirakira_8bpc_decision.md`、
`refs/conformance/olmdirectionalblur_8bpc_decision.md` に固定し、広い
PNG tuning ではなく narrow proof 待ちとして扱います。

## 未解決点

各 plug-in の主な未解決点です。

| Plug-in | 未解決 | 理由 | 解決方法 |
| --- | --- | --- | --- |
| ColorKeep | 実参照が薄い | synthetic/helper 扱いが中心 | 必要なら Windows Software 実参照を作る |
| OLMBlur | CLI に `max=1` 残差 | AE exact は出ているが、丸め・蓄積・Legacy border の説明が未完 | Blur runtime trace で writeback と border state を確定 |
| OLMColorKey | 16bpc 未一致、32bpc 未検証 | normalized 8bpc packaged slice は通った。16bpc Mac AE は Force Lower Precision epsilon 修正後 8/9 exact | 残る `olmcolorkey__case_0009` の Edge Thin / border path を binary/runtime evidence で確認 |
| OLMToonDilate | 16/32bpc 未検証 | 8bpc packaged slice は通ったが bit depth 展開がまだ | 16bpc/32bpc Windows Software 参照を追加 |
| OLMDistanceGradation | 16bpc 未一致、CLI 仕様説明が未完 | 8bpc Mac AE exact はあるが、16bpc では Render Mode=2、Use Background Color=1、In/Out=3 などの分岐で大きくズレる。field prep / OpenCV args の説明も不足 | まず Mac AE parameter replay / 16bpc color path を確認し、その後 field world、distanceTransform、blur 引数を runtime trace で確定 |
| OLMSmoother v1 | 8bpc AE exact | 960x540 再検証で `case_0001..0003` が exact | v2 互換扱いへ寄せるか、v1 独立維持かを明示する |
| OLMSmoother2 | Legacy key / gamma | current-AEX recapture 12ケースを取り込み済み。case 0002/0003 はAE保存before入力でCLI exact。0004 は Smooth Range threshold で target final writer float と一致。0012 は `cardinal6 key=50 -> f270/e170/e3a0` まで局所化 | 0012 `(91,841)` の scanner/emit 中間値と 0004 polygon/no-polygon path を binary/runtime evidence で確定 |
| OLMDirectionalBlur | blocked | PNG tuning だけで進めると誤実装になりやすい。angle-0 と diagonal では見るべき証拠が違う | `case_0001 (465,169)` 系の rowdriver/valid-alpha と、`case_0005 (507,367)` 系の rotate/validity を別々に runtime/asm evidence で確定 |
| OLMRadialBlur | Zoom / Rotation / Inner | Zoom は final byte packing ではなく alpha/sample accumulation、tiny Rotation は sampler validity、Inner は global toggle 不採用まで局所化 | `rb_inner_only_strength_large` と `rb_inner_quality_1` の typed `FUN_180001c90` witness を取る |
| OLMKiraKira | compose / pre-writeback / final quantization | BT.709 seed、boxFilter、ray-helper、`FUN_18114fd90` は確定寄り。global compose gain 変更は悪化。2026-06-25 取込では内部compose floatは未分離 | merge-mode-1 compose float/writeback または residual hotspot の narrow trace を取る |

## 方針

作業は以下の流れで進めます。

1. Windows AEX を Ghidra / objdump / runtime trace で読む
2. 画像処理仕様を binary-grounded IR に落とす
3. AE なし CLI で Windows 参照 PNG と比較する
4. Mac AE plug-in に反映する
5. Windows Software 参照と Mac AE 出力を比較する
6. 差分が残ったら、PNG だけで調整せず IR / asm / trace に戻る

公開時は、互換実装だけでなく次も同梱する想定です。

- binary-grounded IR
- Windows reference manifest
- AE なし CLI 比較ツール
- AE-host validation 手順
- bit depth 別 conformance suite

## ディレクトリ

| Path | 内容 |
| --- | --- |
| `mac/` | Mac After Effects plug-in project |
| `cli/` | AE なし検証用のアルゴリズム CLI |
| `refs/scripts/` | smoke test、参照比較、dashboard 生成など |
| `refs/reference_requests/` | Windows 側で追加取得する参照 request |
| `refs/ae_pixel_validation_packages/` | Mac AE exact 検証用 request zip |
| `refs/upstream_official/` | 公式 README / site / manual text の控え |
| `notes/` | IR、逆解析メモ、進捗台帳、作業方針 |
| `scripts/` | handoff、runtime trace、AE-host 検証、packaging |

大きいローカル生成物は git に入れません。

- Ghidra project DB
- decompiler dump / raw disassembly dump
- build 済み `.aex` / `.plugin`
- Windows / Mac の render 出力
- handoff zip
- runtime trace package
- report 出力

## ビルド

全 Mac plug-in をビルドします。

```sh
scripts/build_all_mac_plugins.sh
```

単体ビルド例です。

```sh
xcodebuild -project mac/OLMBlur/Mac/OLMBlur.xcodeproj -configuration Debug build
```

Mac AE 実機へ渡す zip を作ります。

```sh
scripts/package_mac_plugins.sh
```

## 検証

AE なしの主要 smoke です。

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
python3 refs/scripts/smoke_all_algorithm_clis.py --profile nonhard
```

Blur / KiraKira の現在の重点 smoke です。

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile blur-kirakira --timeout 180
```

次に Windows 側へ送るものを確認します。

```sh
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

packaged 8bpc conformance summary を更新します。

```sh
python3 scripts/generate_conformance_summary.py
```

runtime trace の返却を取り込みます。

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_smoother2_legacy_cce0_internals_trace_20260621_011845.zip
```

summary / comparison index は `refs/reports/` に日付時刻付きで自動保存されます。

AE-host / AE pixel validation の返却を取り込みます。

```sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host_or_pixel.zip \
  --require-all-pixel-requests
```

## 現在の次アクション

`scripts/print_next_olm_action.py` の現在判定は
`investigate-16bpc-mac-ae-residuals` です。16bpc の normalized exact
Windows Software 参照は返却・取込済みで、Mac AE 2026 で45件を実行し、
native 16bit 比較まで済んでいます。ColorKey Force Lower Precision と
DistanceGradation Inside/all-opaque no-source 修正後の現在値は 17/45 exact なので、これは
完了ではありません。

送付済みzip:
`handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`

内容は OLMBlur 7件、OLMColorKey 9件、OLMDistanceGradation 29件です。
8bpc で normalized AE exact になっている範囲だけを、次の bit depth に
広げるための参照取得です。

Mac AE validation 用zip:
`handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/`

内容は次の5本です。

- `bitdepth16_olmblur_exact.zip`
- `bitdepth16_olmcolorkey_exact.zip`
- `bitdepth16_olmdistancegradation_basic_exact.zip`
- `bitdepth16_olmdistancegradation_extended_exact.zip`
- `bitdepth16_olmdistancegradation_blur_exact.zip`

まとめて渡す場合のbundle:
`handoffs/ae_host_validation/20260625_222505_20260625_16bpc_mac_ae_validation_bundle/olm_ae_pixel_validation_20260625_16bpc_mac_ae_validation_20260625_222505.zip`

候補確認:

```sh
python3 scripts/list_olm_return_candidates.py \
  handoffs/ae_host_validation/20260625_222505_20260625_16bpc_mac_ae_validation_bundle
```

Mac AE 実行結果は次に記録しています。

- `refs/conformance/bitdepth_16bpc_mac_ae_validation_20260626_distancegradation_inside_no_source.md`
- `refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.md`

16bpc の現状は `AE exact` ではなく `not-ae-exact` です。
失敗28件の分類は `full-scale-mismatch` 13件、
`large-structured-mismatch` 8件、OLMBlur の
`16bpc-writeback-quantization` 6件、OLMBlur legacy の
`border-plus-quantization` 1件です。古い 2026-06-25 結果は
`path_full` 非対応でパラメータが再生されていなかったため、現在の残差
baseline には使いません。ColorKey は AEX 由来の Force Lower Precision
epsilon 規則を反映して `olmcolorkey__case_0008` が exact になり、残りは
`olmcolorkey__case_0009` です。このケースは `Edge Blur` ではなく
`Lab76 + Force Lower Precision=3 + Edge Thin Amount=25 (Distance Type=2)` の
残差で、Windows 参照は透明化する画素を Mac 側が input のまま保持しています。
Focused diagnostic:
`refs/conformance/olmcolorkey_16bpc_case_0009_analysis.md`
には、単純な `Lab76 + dilate 25` 再現や `32768` 正規化では説明できないことを
記録しています。さらに seed/border/distance の素朴な派生モデル総当たりでも
最良 `80592px` 差にしかならず、実際の Mac AE 残差 `12597px` はそれよりずっと
Windows に近いです。
DistanceGradation は all-opaque input の
Inside/no-source rule で `olmdistancegradation_basic__case_0002` が exact になりました。
OLMBlur 16bpc は kernel tuning ではなく、まず 16bpc writeback / PNG scaling
規則を確認する段階です。

5本まとめて検証する場合は、次のコマンドで一括比較できます。

```sh
python3 scripts/verify_ae_pixel_validation_batch.py \
  handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation \
  path/to/mac_ae_16bpc_returns \
  --run-dir /tmp/olm_ae_pixel_16bpc_batch
```

返却物の取り込みルーター経由でも同じ検証ができます。

```sh
python3 scripts/intake_olm_return.py path/to/mac_ae_16bpc_returns \
  --kind ae-pixel-validation \
  --ae-pixel-requests-dir handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation \
  --run-dir /tmp/olm_ae_pixel_16bpc_batch
```

Smoother2 については
`refs/conformance/olmsmoother2_current_aex_8bpc_decision.md`
で、次に必要な証拠を writer-anchor から順番に固定しました。
送付済み focused runtime trace package は
`refs/runtime_trace_packages/olm_runtime_trace_smoother2_current_aex_neighborhood_witness_20260624_235610.zip`
です。2026-06-25 の返却で final writer は両 witness とも確認できましたが、
`OLMSmoother2+0x350b` exact-XY 内部 predicate は未ヒットなので、内部
branch の分類はまだ未解決です。

Smoother2 は `0004 (1903,519)` と `0012 (91,841)` が逆向きの局所残差に
分かれています。`0004` は Windows が半透明出力を足し、Mac 側は透明
passthrough になりやすい。`0012` は逆に Mac 側が半透明出力を足し、
Windows は透明に寄ります。次は broad PNG ではなく、`0004` の final
writer / `cce0` / `c280` polygon と、`0012` の final transparent writer /
cardinal6 / `d3b0/da50/e170/f270/e3a0` を狭く見る段階です。global
transparent-center fallback と global `f270` suppression は採用しません。

RadialBlur Inner は 2026-06-25 の witness plan で、次に見る代表ケースを
`rb_inner_only_strength_large` と `rb_inner_quality_1` に固定しました。
`rb_inner_edgefade_only` は Edge Fade prepass 用の fallback です。
`loop-minus-one`、`circular-wrap`、`table-span-minus-one` は localization
probe であり、global rule としては採用しません。

KiraKira は 2026-06-24 の aggregation / compose trace を 2026-06-25 に
再取込済みです。`kirakira_aggregation_compose_bt709_20260624` は
`answered` / `answered_partial` として検証でき、BT.709 seed、OpenCV
boxFilter、ray-helper、`FUN_18114fd90` は説明できています。内部
merge-mode-1 compose float / pre-writeback はまだ未分離なので、次に欲しい
のは広いPNGではなく、その一点か residual hotspot の narrow trace です。

DirectionalBlur は 2026-06-25 の witness plan で、次に取る証拠を
2系統に分けました。angle-0 は `case_0001 (465,169)` と
`(487..494,169)` の横一列で rowdriver / valid-alpha を確認します。
diagonal は `case_0005 (507,367)` と反対方向の `(423,187)` で
rotate sampler / validity / denominator を確認します。片方だけの結果や
広いPNG平均から実装を決めない方針です。

bit depth 展開については、2026-06-25 時点の normalized 8bpc exact
グループから 16bpc 参照 request を生成しました。現在の対象は
OLMBlur 7件、OLMColorKey 9件、OLMDistanceGradation 29件の合計45件です。
ローカルレポート:
`refs/reports/bit_depth_expansion_plan_20260625/bit_depth_plan.md`

16bpc 参照の受領記録:
`refs/conformance/bitdepth_16bpc_reference_return_20260625.md`

16bpc Mac AE 検証結果:
`refs/conformance/bitdepth_16bpc_mac_ae_validation_20260626_distancegradation_inside_no_source.md`

16bpc 残差分類:
`refs/conformance/bitdepth_16bpc_mac_ae_residual_classes_20260626_distancegradation_inside_no_source.md`

Windows へ送った project-local zip:
`handoffs/windows_batch/olm_windows_reference_request_20260625_16bpc_normalized_exact.zip`

取り込み手順と優先順位は
`notes/WINDOWS_RETURN_INTAKE_PLAYBOOK_20260619.md` にあります。

## 主要メモ

```txt
notes/CONFORMANCE_LEDGER.md
notes/AE_EXACT_CONFORMANCE.md
notes/IR_INDEX_20260621.md
notes/BINARY_GROUNDED_IR_TEMPLATE.md
notes/BIT_DEPTH_REFERENCE_STRATEGY.md
notes/PORTING_BOARD.md
notes/WINDOWS_RETURN_INTAKE_PLAYBOOK_20260619.md
```

## English

This is a private working repository for porting OLM Tools After Effects
plug-ins from Windows AEX binaries to modern macOS / Apple Silicon. The final
compatibility bar is Mac AE output matching Windows AE Software-rendered
references exactly for the declared bit depth.
