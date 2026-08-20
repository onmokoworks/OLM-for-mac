# scripts ディレクトリ案内

このディレクトリの Python / shell スクリプトは、主に「移植そのもの」ではなく、
Windows 実機との証拠収集、Mac AE 検証、比較、レポート更新を回すためにあります。

## 現在のリリース作業で使う入口

通常回帰：

```sh
python3 scripts/run_olm_mac_fixed_fixture_regression_20260805.py
```

Macリリース統合ゲート：

```sh
python3 scripts/run_olm_release_gate_20260806.py
```

Windows最小7観測パッケージの再生成と返却検証：

```sh
python3 scripts/package_windows_ae_release_boundary_minimal_20260806.py
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py RETURN.zip
```

現在のWindows対象は
`refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`
だけです。以下に列挙された旧request／pending queue系スクリプトは調査履歴や将来の
追加校正用であり、現行リリースの通常手順ではありません。

大きく分けると次の6系統です。

## 1. Windows 往復

- `publish_windows_request_to_share.sh`
- `stage_next_windows_request_to_share.py`
- `materialize_windows_send_first_staging.py`
- `publish_pending_runtime_trace_packages_to_share.py`
- `intake_latest_windows_return_from_share.py`
- `list_olm_return_candidates.py`
- `intake_olm_return.py`
- `summarize_win_reference_return.py`

使いどころ:

- `$OLM_PR_SHARE_ROOT/new/mac_requests` に request zip を置く
- Windows 側の作業中ログは `new/windows_processing`、完了返却は
  `new/mac_returns` に分離する
- repo 内 `refs/share_staging/...` に現在の Send First zip と README を再生成する
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

`run_ae_validation_batch.py` は各実行を `batch_run_<run_id>/` に隔離し、
入力を single-link/read-only の `source_capsule/staged_requests/` に固定したうえで、
`runtime/`、`raw_candidates/`、`validated_outputs/`、`validated_summaries/` を分離する。
全 PNG の CRC・critical structure・IDAT inflate・SHA/ファイル identity 検証後、
検証済みbytesを `validated_outputs/` へatomicに派生し、`AE_PIXEL_VALIDATION_BATCH_RESULT.json` を
generation commit marker として最後に書く。`--results-base` はこの run tree の
親ディレクトリであり、従来の共有 flat output ではない。request 単位の summary は
単独では authoritative ではない。static な `passed` marker や `--batch-result-json` の
published pointer だけでも authority にはせず、consumer は採用時ごとに
published pointer/呼出し元が保持する `generation_commit_anchor.sha256` を期待値として
`run_ae_validation_batch.verify_generation_commit(expected_commit_sha256=...)` を実行する。同 verifier が、同じ
`run_id` の commit に列挙された staged source・raw/validated PNG・summary・raw JSON を
O_NOFOLLOW/SHA/identity で再検査して成功した場合だけ generation を採用する。

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
- `materialize_windows_fresh_param_parity.py`
- `materialize_16bpc_exact_manifest.py`
- `materialize_32bpc_probe_status.py`

使いどころ:

- conformance 状態を再集計する
- pending queue を更新する
- dashboard / ledger 向けの中間 JSON / Markdown を再出力する
- Windows fresh defaults / ranges の parity を `refs/conformance/` に確定記録する
- live request/result から covered 16bpc exact slice を `refs/conformance/` に確定記録する
- 32bpc probe lane を `probe-only-png-return` / `awaiting-return` として committed に固定する

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

project-local Send First staging を再生成:

```sh
python3 scripts/materialize_windows_send_first_staging.py
```

返却候補を見る:

```sh
python3 scripts/list_olm_return_candidates.py "$OLM_PR_SHARE_ROOT" ~/Downloads
```

最新返却を自動 intake:

```sh
python3 scripts/intake_latest_windows_return_from_share.py --share-root "$OLM_PR_SHARE_ROOT"
```

`OLM_PR_SHARE_ROOT` が未設定なら、スクリプトは `/Volumes/*/olm_pr` を自動検出します。
split layout では返却候補を `mac_returns` だけから読み、`windows_processing`
を intake 対象に混ぜません。取り込み済みファイルは `old` へ移動します。

reference request zip の契約チェック:

```sh
python3 refs/scripts/verify_reference_request_package.py path/to/package.zip
```

2026-07-03 以降、この verifier は `request_id` / `cases` だけでなく request
JSON の契約も見ます。とくに `32bpc` は `compare_policy` と
`output_requirements` が揃っていないと通らないので、EXR-first /
`probe-only` の約束が zip 検証でも落ちます。

返却の format / float-preserving 状態を見る:

```sh
python3 scripts/summarize_win_reference_return.py path/to/returned_reference.zip \
  --imported-set-dir refs/win_references/<set_id>
```

この summary は 2026-07-03 以降、`reference_quality` も出します。
とくに 32bpc は `float-preserving-return` / `probe-only-png-return` を
request 契約と返却 format の両方から判定します。

`refs/scripts/verify_manifest.py` は、manifest 上の `frame` が `.png` でも
reference/candidate 両方に同 stem の `.exr` companion があれば、比較時に
そちらを優先します。2026-07-03 以降は EXR/TIFF/HDR companion の比較を
float のまま行うので、`32bpc` の `0 < delta < 1` も潰れません。
比較ポリシーは
`refs/conformance/bitdepth_32bpc_compare_policy_20260703.md` を見てください。

次に何を送るべきか確認:

```sh
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

出力の `pending Windows refs` は PNG/EXR などの Windows reference request
だけを数えます。`pending runtime traces` は debugger/runtime trace package
の待ち数です。前者が `0` でも後者が `1` なら、次に送るものは runtime trace
zip です。

Windows Send First staging の中身が現在の pending queue と一致しているか確認:

```sh
python3 refs/scripts/smoke_windows_send_first_staging.py
```

`OLMDirectionalBlur` のローカル witness JSON 出力と比較器を確認:

```sh
python3 refs/scripts/smoke_olmdirectionalblur_cli_witness.py
python3 refs/scripts/smoke_compare_directionalblur_trace.py
```

AEX CPU simulation / OpenCV detour の最低限の健全性を確認:

```sh
python3 refs/scripts/smoke_emulation_opencv_detours.py
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
