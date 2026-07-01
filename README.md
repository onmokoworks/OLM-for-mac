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

また、`AE exact` と「AE で手で触って意味がある段階か」は別です。
判断は `correctness_status` / `host_status` / `work_lane` の3軸で行います。
一次情報は `notes/CONFORMANCE_LEDGER.md` に集約しています。

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
| OLMBlur | 8bpc packaged slice は Mac AE exact。16bpc Mac AE はまだ未exactだが、`case_0006` は 2026-07-01 の current-AEX witness で Windows/Mac の pre-store float と内部 word 一致まで到達し、主疑点は writer/helper から reference/export provenance へ移動。`case_0007` は Legacy境界/seed異常に分離済み |
| OLMToonDilate | 8bpc packaged slice は Mac AE exact |
| OLMDistanceGradation | basic / extended / blur の 8bpc packaged slice は Mac AE exact。16bpc は未exact。AE自動実行は復旧済み。`case_0026` の Power param 誤読と Constant 専用 binary threshold を修正し、Constant/background系は大幅改善 |
| OLMColorKey | core / Edge Thin / Edge Blur の normalized 8bpc packaged slice は Mac AE exact。16bpc covered slice も full batch 9/9 exact。次は32bpc方針と参照展開 |
| OLMSmoother2 | no-key grid は 8bpc Mac AE exact。legacy current-AEX recapture 済み。key/gamma は Smooth Range threshold 昇格で大幅改善、残る局所残差を調査中 |
| OLMSmoother v1 | 960x540 再検証で 8bpc Mac AE exact。v2 互換扱いへ寄せる判断は別途 |
| OLMDirectionalBlur | 参照は多いが、まだ blocked。2026-06-25 witness plan で angle-0 と diagonal の2系統に分け、PNG-only tuning は止めて asm/runtime evidence 待ち |
| OLMRadialBlur | Zoom は caller-collapse alpha 残差、tiny Rotation は polar RGB / substitute-path 残差。2026-07-01 の propagated-validity probe で「validity plane を同カーネルで伝播させるだけ」では動かないことも確認。Inner は typed `FUN_180001c90` per-cell witness 待ち |
| OLMKiraKira | BT.709 seed、OpenCV 4.5.5 AVX2、ray-helper、`FUN_18114fd90` aggregation まで grounding 済み。2026-07-01 の hotspot runtime return 取り込み後も、残差は broad compose/gain ではなく hotspot `(934,118)` 専用の追加 attenuate/branch before writeback まで狭い。加えて current Mac source は `Merge Mode`, `Approximated Input`, `Fade Out`, `Highlight Radius`, ramp 系など未消化 control が残る |

AE 実機を触る前の短い目安です。詳細な理由と次アクションは
`notes/CONFORMANCE_LEDGER.md` の Current Decision Matrix を見ます。

| Plug-in | host status | work_lane | いま AE で手で触る意味 |
| --- | --- | --- | --- |
| OLMColorKey | `host-stable` | `bitdepth-expand` | 回帰確認と32bpc展開向き |
| OLMBlur | `host-visual-tuning-ready` | `binary-proof` | 16bpc残差は分類済み。`case_0006` は writer/helper より reference/export provenance 側の確認が先。`case_0007` は Legacy境界証拠を維持 |
| OLMToonDilate | `host-stable` | `bitdepth-expand` | 回帰確認とbit depth展開向き |
| OLMDistanceGradation | `host-debuggable` | `binary-proof` | witness単位の16bpc確認と回帰確認だけ有益 |
| OLMSmoother v1 | `host-stable` | `ae-validate` | v1/v2方針確認向き |
| OLMSmoother2 legacy | `host-debuggable` | `binary-proof` | witness単位の確認だけ有益 |
| OLMDirectionalBlur | `host-debuggable` | `binary-proof` | witness単位の確認だけ有益 |
| OLMRadialBlur | `host-debuggable` | `binary-proof` | witness単位の確認だけ有益。いまは Zoom の caller-collapse と tiny Rotation の polar RGB 分岐を別々に追う段階 |
| OLMKiraKira | `host-smoke` | `binary-proof` | host統合確認まで |

つまり、`RadialBlur` や `KiraKira` を AE 上で見た目だけで詰める段階ではまだ
ありません。先に asm / runtime trace / CLI で、どの出力を信用してよいかを
固めます。

詳しい台帳は `notes/CONFORMANCE_LEDGER.md`、IR の入口は
`notes/IR_INDEX_20260621.md`、用語定義は
`notes/AE_EXACT_CONFORMANCE.md` にあります。

UI パラメータ定義の一次情報は別で固定しています。
`PF_ADD_*` から機械抽出した source-backed report が
`refs/reports/mac_plugin_param_schema_20260629.md` と
`refs/reports/mac_plugin_param_schema_20260629.json` です。
ここで確定するのは初期値・最小最大・UIレンジ・型・popup choices で、
内部アルゴリズムの効き方そのものは確定しません。

さらに、Windows 参照 manifest / request との名前・構成差分は
`refs/reports/param_schema_windows_ref_audit_20260629.md` に分けています。
2026-06-30 時点では `OLMKiraKira` の Windows 側 UI との差はかなり縮み、
`Channel`, `Blur Mode`, `Strength Multiplier`, `Glow Opacity` は fresh
capture 基準で揃いました。残りは `Brightness Gain`, `Fade Out`,
`Highlight Radius`, および ramp 系の host drift です。
`OLMRadialBlur` は 2026-06-29 host-fix pass で grouped `Outer/Inner Blur`,
per-section `Edge Fade`, separate inner offset controls, `Noise Type`,
`Noise Layer`, `Seed`, `Thickness` を追加し、visible parameter set の差は
かなり閉じました。したがって RadialBlur の残課題は主に UI 面ではなく
sampler / prepass / writeback の binary-proof です。
`OLMDirectionalBlur` も同日の host-fix pass で grouped Front/Back labels,
`Noise Type`, `Noise Layer`, `Seed`, `Offset`, `Thickness` を追加し、残課題
は主に angle-0 rowdriver/valid-alpha と diagonal rotate/validity の
binary-proof に寄っています。

さらに、「Mac source 上の現在の default」ではなく「元の Windows AEX を AE に
追加した瞬間の cold-start default」を固定するための request も追加しました。
Windows 実測の fresh-instance default は
`refs/reference_requests/olm_fresh_instance_defaults_20260629.json` で取得し、
source-backed schema との役割分担は
`notes/PARAMETER_SOURCE_OF_TRUTH.md` に固定しています。

linked replay request は `scripts/materialize_linked_request_params.py` で
`params_full` を自動展開できます。`source_case_id` がある再現便は、参照
manifest を土台に visible params を明示化してから Windows に渡す運用に
固定していきます。`refs/scripts/package_reference_requests.py` も package 作成時に
この materialize を一時コピーへ自動適用します。

packaged 8bpc AE-host validation の最小M0集計は機械生成します。
現在の manifest は `refs/conformance/packaged_8bpc_manifest.json` です。
summary は `python3 scripts/generate_conformance_summary.py` で
`refs/reports/conformance_summary_packaged_8bpc.md` にローカル生成します。
この集計では `AE exact` と known-red / residual を混ぜません。

## 未解決点

各 plug-in の主な未解決点です。

| Plug-in | 未解決 | 理由 | 解決方法 |
| --- | --- | --- | --- |
| ColorKeep | 実参照が薄い | synthetic/helper 扱いが中心 | 必要なら Windows Software 実参照を作る |
| OLMBlur | 16bpc Mac AE が未exact | 8bpc AE exact は維持。`case_0006` は 2026-07-01 imported current-AEX witness で Windows/Mac の pre-store float と internal word 一致が確認され、残る差分は reference/export provenance 疑いへ移動。`case_0007` は Legacy境界/seed family のまま | `case_0006` は current-AEX exported PNG と canonical 16bpc reference の provenance を確認し、`case_0007` は Legacy border/all-same state を binary/runtime evidence で確定 |
| OLMColorKey | 32bpc 未検証 | normalized 8bpc packaged slice と16bpc covered slice は通った。16bpc full batch は9/9 `max=0` | 32bpc比較ポリシーと参照取得を決める |
| OLMToonDilate | 16/32bpc 未検証 | 8bpc packaged slice は通ったが bit depth 展開がまだ | 16bpc/32bpc Windows Software 参照を追加 |
| OLMDistanceGradation | 16bpc 未一致 | 2026-06-29 Windows trace とMac plug-in debug dumpで `case_0026` のfield rampは一致。`PF_ADD_FLOAT_SLIDERX` の Power に `FIX_2_FLOAT` をかけていた誤読を修正。さらに `FUN_181174760` の Constant 専用 `THRESH_BINARY` を反映し、`case_0020 1001->1`、`case_0021 1002->1`、`case_0022 9347->192`、`case_0023 1388->73` changed pixels まで改善。残るConstant差分は全てしきい値1px以内。direct Layer/no-bg unpremultiply は悪化したので棄却。extended 16bpc はまだ 1/16 exact | Power / Constant fixes を維持し、Constant境界witness、Layer/no-bg source ownership、Sphere/Power boundary quantization を binary/runtime evidence でfamily別に詰める |
| OLMSmoother v1 | 8bpc AE exact | 960x540 再検証で `case_0001..0003` が exact | v2 互換扱いへ寄せるか、v1 独立維持かを明示する |
| OLMSmoother2 | Legacy key / gamma | current-AEX recapture 12ケースを取り込み済み。case 0002/0003 はAE保存before入力でCLI exact。0004 は Smooth Range threshold で target final writer float と一致。0012 は `cardinal6 key=50 -> f270/e170/e3a0` まで局所化 | 0012 `(91,841)` の scanner/emit 中間値と 0004 polygon/no-polygon path を binary/runtime evidence で確定 |
| OLMDirectionalBlur | blocked | PNG tuning だけで進めると誤実装になりやすい。angle-0 と diagonal では見るべき証拠が違う | `case_0001 (465,169)` 系の rowdriver/valid-alpha と、`case_0005 (507,367)` 系の rotate/validity を別々に runtime/asm evidence で確定 |
| OLMRadialBlur | Zoom / Rotation / Inner | Zoom は final byte packing ではなく caller-collapse alpha/sample accumulation、tiny Rotation は validity alpha ではなく polar RGB / substitute path、Inner は global toggle 不採用まで局所化 | Zoom は `+0xf252 -> +0xf250 -> +0xe` の caller-collapse chain、tiny Rotation は bright-lobe を落としている upstream RGB population、Inner は `rb_inner_only_strength_large` / `rb_inner_quality_1` の typed `FUN_180001c90` witness を詰める |
| OLMKiraKira | compose / pre-writeback / final quantization | BT.709 seed、boxFilter、ray-helper、`FUN_18114fd90` は確定寄り。global compose gain 変更は悪化。2026-07-01 hotspot runtime return を取り込んでも、残る差分は hotspot `(934,118)` の追加 attenuate/branch before writeback にさらに狭いまま | merge-mode-1 compose float/writeback または residual hotspot の narrow trace を取る |

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
| `refs/reports/mac_plugin_param_schema_20260629.{md,json}` | Mac plug-in UI parameter schema の source-backed 抜き出し |
| `refs/reports/param_schema_windows_ref_audit_20260629.{md,json}` | Windows manifest / request と Mac UI schema の差分監査 |
| `notes/PARAMETER_SOURCE_OF_TRUTH.md` | default/range は source、ケース値は Windows manifest、fresh default は Windows cold-start capture とするルール |

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

`refs/scripts/generate_port_dashboard.py` と
`refs/scripts/generate_diff_gallery.py` の既定出力先は repo 外です。
現在は `/tmp/olm_reports/` 配下へ生成し、作業ツリーを生成HTMLやassetsで
太らせないようにしています。repo 内に明示的に出したいときだけ
`--output-dir` を指定してください。

AE-host / AE pixel validation の返却を取り込みます。

```sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host_or_pixel.zip \
  --require-all-pixel-requests
```

## 現在の次アクション

README 上の current summary は次の通りです。

- packaged 8bpc machine summary は `AE exact=62`, `reference-generation split=1`,
  `known-red=7`
- 16bpc は `OLMColorKey` が covered slice 9/9 exact、`OLMBlur` /
  `OLMDistanceGradation` が witness-led binary-proof 継続中
- いま Windows runtime queue に残っている pending は 2 件だけです
  - `OLMRadialBlur` caller-collapse follow-up
  - `OLMDistanceGradation` 16bpc Constant `case_0023` witness

priority は `notes/CONFORMANCE_LEDGER.md` を正にしますが、ざっくり言うと
次の順です。

1. `OLMBlur` 16bpc narrow proof
2. `OLMRadialBlur` Zoom / tiny Rotation narrow proof
3. `OLMDirectionalBlur` angle-0 / diagonal witness
4. 強い plug-in の bit depth expansion
5. `OLMDistanceGradation` / `OLMSmoother2 legacy`
6. `OLMKiraKira`

## 共有フォルダ運用

Windows 実機との往復は共有フォルダ `/Volumes/onmk/olm_pr/` を使います。

- `new/`
  - Mac 側が最新 request zip を置く
  - Windows 側が実行後の `*_return_windows.zip` を置く
- `old/`
  - 処理済み zip の退避先

候補確認:

```sh
python3 scripts/list_olm_return_candidates.py /Volumes/onmk/olm_pr/new /Volumes/onmk/olm_pr/old
```

最新返却の自動取込:

```sh
python3 scripts/intake_latest_windows_return_from_share.py --share-root /Volumes/onmk/olm_pr
```

必要なら個別取込:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/some_request.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --runtime-summary-md refs/reports/runtime_trace_summary.md \
  --runtime-comparison-dir refs/reports/runtime_trace_comparisons
```

pending runtime queue の正本:
`refs/reports/pending_runtime_trace_packages.md`

## bit depth 拡張の現状

16bpc normalized exact request の Windows 参照返却と Mac AE validation は
すでに一巡しています。45 cases の current lane は、広い見た目合わせではなく
plug-in ごとの narrow witness に分解して進めています。

- `OLMColorKey`: covered 16bpc slice 9/9 exact
- `OLMBlur`: `case_0006/0007` を narrow witness に分離済み
- `OLMDistanceGradation`: Power / Constant fixes 後も family-level residual が残り、
  `case_0023` OutsideThreshold=0 witness が active

古い一括 16bpc rerun の説明より、現在は個別 witness-led notes を優先します。
詳細は `notes/CONFORMANCE_LEDGER.md` と各 `refs/conformance/*.md` を見ます。

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
