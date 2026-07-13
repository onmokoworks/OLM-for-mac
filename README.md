# OLM for Mac

OLM Tools の Windows 版 After Effects AEX を、macOS / Apple Silicon 向け
After Effects plug-in として互換移植する作業リポジトリです。

最終目標は、指定した Windows AE Software render と同じ入力、パラメータ、
bit depth、カラープロファイルでレンダーした Mac AE 出力が `max_diff=0` になる
ことです。見た目が近いこと、CLI の一致、off-by-1、許容差内は完了ではありません。

## 現在地

プラグイン全体を「完了」と呼べるものはまだありません。対応範囲を
feature / path / bit depth ごとに分け、各セルを `AE exact` まで閉じます。

| Plug-in | 現在の確定事項 | 次のレーン |
| --- | --- | --- |
| ColorKeep | 互換対象外の support/helper | 実Windows参照が必要になった時だけ再開 |
| OLMBlur | 完全workerの局所AEX再生は進展。Mac AE / Windows参照のプロベナンスを再確認中 | 8/16/32bpcのhash固定参照とhost境界の証明 |
| OLMColorKey | covered 8bpc / 16bpc slice は `AE exact` | AE 26.3 FLOAT EXRで32bpcを分類 |
| OLMToonDilate | covered 8bpc / 16bpc slice は `AE exact` | 32bpc EXR参照とholdout展開 |
| OLMDistanceGradation | 16bpc extended は `7/16 AE exact`。OpenCV正規化からPF16 worldへの丸め境界を再現し、`case_0010/0011`を閉鎖 | Layer/no-bg、field/export、case_0028を別々に証明。現行8bpcは `0/29` のknown-redで、旧29/29記録はバイナリプロベナンス不足 |
| OLMSmoother v1 | 8bpcの既存sliceは保持。endgame扱い | 独立維持かSmoother2互換かを明示 |
| OLMSmoother2 | no-key slice は `AE exact`。legacy/key/gammaは局所producer状態まで狭め済み | 0004/0012のlive class-plane / c280 / cce0 witness |
| OLMDirectionalBlur | front-onlyの限定8bpc slice は `AE exact`。Alpha Fade以降はhost境界待ち | Windows 2025 AEX hash固定のPF input/output witness |
| OLMRadialBlur | plane layoutはbinary-grounded、Zoom / Rotation / Innerの意味論は未閉鎖 | sampler / prepass / writebackのtyped witness |
| OLMKiraKira | Blur Mode 1/2 のpass dispatchはgrounded。hotspotは参照プロベナンス分岐 | Merge Mode 2、Blur Mode 3/4、export/placement証明 |

`AE exact` の唯一の定義、禁止事項、次の許可アクションは
[`notes/CONFORMANCE_LEDGER.md`](notes/CONFORMANCE_LEDGER.md) が正です。
Distance Gradation の直近の閉鎖と8bpc記録の訂正は
[`refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`](refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md)
を参照してください。

`host_status` は正しさの評価ではありません。「Mac AEでプラグインを開いて、
いま何を確認してよいか」の目安です。出力が正しいかは
`correctness_status`、次に進めてよい作業は `work_lane` で判断します。

## 進め方

1. Windows AEX の objdump / Ghidra / runtime trace から、定数・分岐・丸め・境界処理を読む。
2. 事実を binary-grounded IR に固定する。
3. 共有coreまたはCLIで局所fixtureを再生し、仮説を潰す。
4. Mac AE plug-inへ狭く反映する。
5. Windows Software参照とMac AE出力を、8bpc、16bpc、32bpcの順に比較する。

PNG差分は症状です。アルゴリズムの確定は、AEX命令列・runtime witness・
独立オラクルのいずれかで裏付けます。

## 検証

通常のAEなしsmoke:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile nonhard
```

Windows側に必要な次の依頼を確認:

```sh
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

conformance集計を再生成:

```sh
python3 scripts/generate_conformance_summary.py
```

AE-host / runtime trace の返却は、取り込む前に必ず対応するrequest contractと
expected AEX hashを確認します。返却が要求したwitnessを含まなければ
`answered_partial` または `failed` として扱い、実装根拠へ昇格しません。

## Windowsとの往復

共有フォルダのルートは環境変数 `OLM_PR_SHARE_ROOT` で指定します。

- `new/`: Mac側が作成した最新request ZIP、またはWindows側の未処理return ZIP
- `old/`: intake済みのZIP

候補の確認:

```sh
python3 scripts/list_olm_return_candidates.py "$OLM_PR_SHARE_ROOT/new" "$OLM_PR_SHARE_ROOT/old"
```

返却の取込:

```sh
python3 scripts/intake_latest_windows_return_from_share.py --share-root "$OLM_PR_SHARE_ROOT"
```

pending queueの正本は
[`refs/reports/pending_runtime_trace_packages.md`](refs/reports/pending_runtime_trace_packages.md)
です。

## ビルド

全プラグイン:

```sh
scripts/build_all_mac_plugins.sh
```

単体例:

```sh
xcodebuild -project mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj \
  -configuration Debug build
```

Mac AE用bundleの配布ZIP:

```sh
scripts/package_mac_plugins.sh
```

## 構成

| Path | 内容 |
| --- | --- |
| `mac/` | Mac After Effects plug-in projects |
| `core/` | AEX命令列に寄せた共有C++ kernel / worker |
| `cli/` | AEなしのアルゴリズム検証CLI |
| `tools/emulation/` | Windows AEX CPU simulation / OpenCV detour / fixture replay |
| `refs/conformance/` | ケース単位の証拠・判定・受け入れ記録 |
| `refs/reference_requests/` | Windowsで取得する参照リクエスト |
| `refs/scripts/` | smoke、比較、依頼生成 |
| `notes/` | 台帳、IR、ロードマップ、運用ルール |
| `scripts/` | AE-host実行、runtime trace intake、共有フォルダ操作 |

大きなローカル生成物（Ghidra DB、AEX/plug-in build、AE render出力、raw trace、
一時HTML）はGit管理しません。再現に必要なfixture、request contract、要約証拠は
コミットします。

## 主要文書

- [`notes/CONFORMANCE_LEDGER.md`](notes/CONFORMANCE_LEDGER.md): 状態、優先順位、禁止事項の正本
- [`notes/AE_EXACT_CONFORMANCE.md`](notes/AE_EXACT_CONFORMANCE.md): `AE exact` と各状態の定義
- [`notes/PORTING_ROADMAP.md`](notes/PORTING_ROADMAP.md): 完了までの作業順序
- [`notes/IR_INDEX_20260621.md`](notes/IR_INDEX_20260621.md): プラグイン別IRの入口
- [`scripts/README.md`](scripts/README.md): 自動化スクリプトの用途

## English

Private compatibility-porting workspace for OLM Tools After Effects plug-ins.
The only completion bar is byte-exact Mac AE output against a declared Windows
AE Software reference for the same feature, parameters, host profile, and bit
depth. CLI matches and visual similarity are intermediate evidence, not
completion.
