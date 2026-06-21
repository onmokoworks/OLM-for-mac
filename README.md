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

現在の大まかな状態です。

直近の packaged 8bpc AE-host validation では、意味のある比較対象
70 ケース中 59 ケースが `max_diff=0` でした。これは現在の検証セット内の
数字であり、全体完了率ではありません。

| 範囲 | 状態 |
| --- | --- |
| Mac plug-in project | 10 本とも Debug universal bundle としてビルド可能 |
| OLMBlur | 8bpc packaged slice は Mac AE exact。残る CLI `max=1` は runtime trace で binary-grounding 中 |
| OLMToonDilate | 8bpc packaged slice は Mac AE exact |
| OLMDistanceGradation | basic / extended / blur の 8bpc packaged slice は Mac AE exact。CLI 側の説明はまだ詰め中 |
| OLMColorKey | core はかなり進んでいる。Edge Blur `case_0009` が残差あり |
| OLMSmoother2 | no-key grid は 8bpc Mac AE exact。legacy current-AEX recapture 済み。key/gamma は Smooth Range threshold 昇格で大幅改善、残る局所残差を調査中 |
| OLMSmoother v1 | 960x540 再検証で 8bpc Mac AE exact。v2 互換扱いへ寄せる判断は別途 |
| OLMDirectionalBlur | 参照は多いが、まだ blocked。PNG-only tuning は止めて asm/runtime evidence 待ち |
| OLMRadialBlur | 一部 binary-grounded。Inner / Edge Fade などは未完 |
| OLMKiraKira | ray order などはかなり分離済み。OpenCV 4.5.5 AVX2 / stage trace 待ち |

詳しい台帳は `notes/CONFORMANCE_LEDGER.md`、IR の入口は
`notes/IR_INDEX_20260621.md`、用語定義は
`notes/AE_EXACT_CONFORMANCE.md` にあります。

## 未解決点

各 plug-in の主な未解決点です。

| Plug-in | 未解決 | 理由 | 解決方法 |
| --- | --- | --- | --- |
| ColorKeep | 実参照が薄い | synthetic/helper 扱いが中心 | 必要なら Windows Software 実参照を作る |
| OLMBlur | CLI に `max=1` 残差 | AE exact は出ているが、丸め・蓄積・Legacy border の説明が未完 | Blur runtime trace で writeback と border state を確定 |
| OLMColorKey | Edge Blur `case_0009` | core は進んだが Edge Blur の seed/distance/weight/apply が未確定 | Edge runtime trace と Mac baseline を比較して Edge だけ詰める |
| OLMToonDilate | 16/32bpc 未検証 | 8bpc packaged slice は通ったが bit depth 展開がまだ | 16bpc/32bpc Windows Software 参照を追加 |
| OLMDistanceGradation | CLI 仕様説明が未完 | Mac AE exact はあるが field prep / OpenCV args の説明が不足 | field world、distanceTransform、blur 引数を runtime trace で確定 |
| OLMSmoother v1 | 8bpc AE exact | 960x540 再検証で `case_0001..0003` が exact | v2 互換扱いへ寄せるか、v1 独立維持かを明示する |
| OLMSmoother2 | Legacy key / gamma | current-AEX recapture 12ケースを取り込み済み。case 0002/0003 はAE保存before入力でCLI exact。0004 は Smooth Range threshold で target final writer float と一致。0012 は `cardinal6 key=50 -> f270/e170/e3a0` まで局所化 | 0012 `(91,841)` の scanner/emit 中間値を binary/runtime evidence で確定 |
| OLMDirectionalBlur | blocked | PNG tuning だけで進めると誤実装になりやすい | asm/runtime evidence で sampling/group/scale を先に確定 |
| OLMRadialBlur | Inner / Edge Fade / variation | 一部 span は確定したが sampler/prepass/writeback が未完 | runtime trace と IR で scatter/normalize を詰める |
| OLMKiraKira | OpenCV helper 精度 | ray order 等は分離済みだが OpenCV 4.5.5 AVX2 stage が未確定 | KiraKira stage trace で warpAffine/boxFilter/compose の初回ズレ箇所を特定 |

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
python3 scripts/print_next_olm_action.py handoffs/windows_batch refs/runtime_trace_packages refs/ae_pixel_validation_packages
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

Windows PNG参照待ちは現時点でありません。Smoother2 は
`0004 (501,1055)` の final writer witness を基準にしたMac側監査で、
key有効時も class-plane threshold は Smooth Range を使うほうが現行
Windows Software参照に合うことが分かりました。これにより同targetの
`cce0_after_b120` は Windows final writer float とほぼ一致し、legacy
12ケース全体の平均残差も大きく下がっています。

次は残る `0012` の `(91,841)` について、
`d3b0/da50/e170/f270/e3a0` の scanner/emit 中間値を確定します。
透明中心パススルー、`idx=105` 停止、`cardinal6 key=50` 停止は
いずれも別ピクセルを壊すため採用しません。

Windows側へ新しく送るzipは、スレッド固定や既ヒット箇所からの確実な
single-stepができる場合だけ作ります。

KiraKira を並行して追う場合は、次のruntime trace packageを使います。

```txt
refs/runtime_trace_packages/olm_runtime_trace_kirakira_deep_stage_values_20260621_021018.zip
```

Smoother2 legacy full current-AEX recapture は取り込み済みです。古い
20260605 legacy PNG は正解データから外し、以後は current-AEX Software
参照を基準にします。2026-06-21 のwriter traceで、残差はPNG exportや
8bpc packingではなく class-plane / switch-index / polygon emitter 側に
あることが分かっています。取り込み手順と優先順位は
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
