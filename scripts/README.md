# scripts ディレクトリ案内

このディレクトリの Python / shell スクリプトは、主に「移植そのもの」ではなく、
Windows 実機との証拠収集、Mac AE 検証、比較、レポート更新を回すためにあります。

大きく分けると次の6系統です。

## 1. Windows 往復

- `publish_windows_request_to_share.sh`
- `stage_next_windows_request_to_share.py`
- `publish_pending_runtime_trace_packages_to_share.py`
- `intake_latest_windows_return_from_share.py`
- `list_olm_return_candidates.py`
- `intake_olm_return.py`
- `summarize_win_reference_return.py`

使いどころ:

- `/Volumes/onmk/olm_pr/new` に request zip を置く
- Windows 側から戻ってきた `*_return_windows.zip` を検出する
- 戻り zip を repo に取り込み、比較レポートを更新する
- 返却が `PNG-only` だったか `EXR` / float-preserving だったかを summary で確認する

## 2. request / handoff 生成

- `generate_bitdepth_reference_request.py`
- `package_runtime_trace_requests.py`
- `package_ae_pixel_validation_request.py`
- `package_ae_pixel_validation_bundle.py`
- `package_windows_action_bundle.py`
- `prepare_windows_reference_handoff.sh`

使いどころ:

- Windows に渡す追加 PNG request を作る
- runtime trace / AE host validation 用の zip をまとめる
- 依頼文と request 一式を一度に束ねる

## 3. Mac AE 実行と host 診断

- `run_ae_single_case.py`
- `run_ae_validation_batch.py`
- `diagnose_ae_host_block.py`
- `verify_ae_host_return.py`
- `verify_ae_pixel_validation_batch.py`
- `verify_ae_pixel_validation_result.py`

使いどころ:

- Mac AE 上で 1 ケースだけ再レンダーして witness を見る
- 16bpc などの batch validation を回す
- AE が modal / duplicate plugin / script 側で詰まっていないか診断する

## 4. プラグイン別の解析

命名規則はだいたいこうです。

- `analyze_<plugin>_*.py`
- `compare_<plugin>_trace.py`
- `audit_<plugin>_*.py`

例:

- `analyze_olmblur_*`
- `analyze_distancegradation_*`
- `analyze_olmradialblur_*`
- `analyze_olmkirakira_*`
- `analyze_smoother2_*`

使いどころ:

- 既存の Windows 参照 / runtime trace / asm facts から
  「今どこまで証拠が取れているか」を機械的に再生成する
- residual family を分ける
- 次に要求すべき narrow witness を決める

## 5. レポート / 台帳更新

- `generate_conformance_summary.py`
- `report_parallel_olm_lanes.py`
- `analyze_pending_runtime_trace_packages.py`
- `summarize_runtime_trace_proof_lanes.py`
- `summarize_windows_fresh_param_parity.py`

使いどころ:

- conformance 状態を再集計する
- pending queue を更新する
- dashboard / ledger 向けの中間 JSON / Markdown を再出力する

## 6. 補助

- `install_mac_plugins_to_mediacore.sh`
- `build_all_mac_plugins.sh`
- `package_mac_plugins.sh`
- `zip_clean.py`
- `ghidra_status.py`
- `ghidra_export_one.sh`

使いどころ:

- Mac plugin のビルドと配置
- duplicate plugin 回避
- Ghidra export や軽い整形

## いまよく使う入口

共有フォルダへ次の依頼を置く:

```sh
python3 scripts/stage_next_windows_request_to_share.py
```

pending runtime trace をまとめて置く:

```sh
python3 scripts/publish_pending_runtime_trace_packages_to_share.py
```

返却候補を見る:

```sh
python3 scripts/list_olm_return_candidates.py /Volumes/onmk/olm_pr/new /Volumes/onmk/olm_pr/old
```

最新返却を自動 intake:

```sh
python3 scripts/intake_latest_windows_return_from_share.py --share-root /Volumes/onmk/olm_pr
```

返却の format / float-preserving 状態を見る:

```sh
python3 scripts/summarize_win_reference_return.py path/to/returned_reference.zip \
  --imported-set-dir refs/win_references/<set_id>
```

次に何を送るべきか確認:

```sh
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

## 見方の目安

- コア実装は `mac/` や `cli/` にある
- `scripts/` は「証拠を取る」「比較する」「進捗を壊さず更新する」ための運用層
- スクリプト数が多いのは、プラグインごとに unresolved family が違うため

なので、見始める順番としては

1. `README.md`
2. `notes/CONFORMANCE_LEDGER.md`
3. この `scripts/README.md`
4. 触りたいプラグイン名の `analyze_*` / `compare_*`

が一番楽です。
