# Backlog

Items moved out of GitHub Issues on 2026-10-25. They are low priority now that verification runs on the AEXCompat/F5x emulator oracle instead of Windows round-trips. Reopen the issue if one becomes relevant again.

## #1 Extract shared Python operations for Windows exchange and package workflows

Originally https://github.com/onmokoworks/OLM-for-mac/issues/1 (opened 2026-07-14).

## 背景

`scripts/` と `refs/scripts/` には、Windows実機との往復、request package生成、返却intake、検証、台帳更新を担う多数のPythonスクリプトがある。

個別スクリプトの目的は分離されている一方、次の基盤処理が複数箇所で反復している。

- repository rootと標準パスの解決
- `--share-root` など共通CLI引数
- JSON manifest / pending reportの読込と型検証
- SHA-256計算
- ZIP内manifestの列挙
- subprocessの実行と出力取得
- 一時ディレクトリとstaging管理
- Windows共有フォルダへのpublish / intake前検証

証拠生成スクリプト自体を統合するのではなく、運用基盤だけを共通化した方が、パス・manifest・エラー処理の不一致を減らせる。

## 目的

既存のCLI、生成物、request ID、証拠の意味を変えずに、反復するPython運用処理を内部ライブラリへ抽出する。

## 提案する境界

```text
python/olm_ops/
  __init__.py
  paths.py
  jsonio.py
  packages.py
  processes.py
  share.py
```

または既存のPython import構成に合わせて `scripts/lib/` 等を使用してよい。

### `paths.py`

- repo root
- share root
- refs / reports / stagingへの標準パス
- repo相対パスの正規化

### `jsonio.py`

- JSON object / listの検証付き読込
- pending rowの抽出
-必須fieldの型検証

### `packages.py`

- SHA-256
- ZIP内JSON manifest列挙
- request ID抽出
- package metadata解決

### `processes.py`

- checked subprocess
- stdout / stderrの統一的な扱い
- JSONを返す子スクリプトの実行

### `share.py`

- publish前検証
- staging directory操作
- `new/` / `old/` の扱い

## 最初の実装スライス

1. `repo_root`、JSON読込、SHA-256、ZIP request ID抽出を共通化する
2. `stage_next_windows_request_to_share.py` と `publish_pending_runtime_trace_packages.py` を共通APIへ移行する
3. 現在のCLI引数とstdoutの主要形式を維持する
4. 共通ライブラリの単体テストを追加する
5. 既存smokeを実行して生成物が変化していないことを確認する

## 固定したいケース

- 不正JSONを従来通りfail-closedで拒否する
- ZIP内に複数JSONがある場合もrequest IDを回収する
- 壊れたZIPはpublish対象へ昇格しない
- `--dry-run` で共有フォルダを書き換えない
- repo相対package pathと絶対pathの双方を扱える
- 同一packageのSHA-256が移行前後で一致する
- pending queueのpriority順が変わらない

## 完了条件

- 共通処理が内部Python packageへ集約されている
- 少なくとも2つの既存entry pointが共通APIを利用している
- CLIの主要な引数・exit behavior・生成物名を維持している
- request / returnのprovenance情報を失っていない
- 共通処理に自動テストがある
- 関連smokeが通る

## 非目標

- plugin別 `analyze_*` / `compare_*` の統合
- fixtureやrequest IDの改名
- conformance判定ロジックの変更
- Windows / Mac AE実行手順の変更
- 既存の証拠ファイルを一括移動すること

証拠生成の意味論には触れず、運用上の重複だけを狭く除去する。

## #2 Windows witness: RadialBlur random01 sampler-entry render context at RVA 0x9d80

Originally https://github.com/onmokoworks/OLM-for-mac/issues/2 (opened 2026-07-25).

## Goal

Separate an AEXCompat render-context/ABI defect from legitimate OLMRadialBlur sampler behavior using one same-run Windows CPU Software witness.

## Frozen case

- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- request: `refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/OLMRadialBlur`
- case: `final_random10_olm_radialblur_01`
- input: packaged `*_before_effects.png`
- 1920x1080, Windows AE Software
- use the manifest parameter vector exactly; do not substitute an older RadialBlur case

## Why

AEXCompat commit `59e002c` closes the prior `omp_get_max_threads=0` divide-by-zero. The same real AEX now reaches bilinear float4 sampler `FUN_180009d80` and stops at RVA `0x9e35` because the derived x index is approximately `9,874,418`. PF Handle allocation failures are empty.

## Required same-run capture

At sampler entry RVA `0x9d80` and its direct caller, capture typed values for the first failing invocation:

- sampler `param6` / `param7` float coordinates
- integerized x / y before the `0x9e35` load
- sampler `param4` / `param5`
- source base pointer
- source width, height, rowbytes/stride
- caller context fields `+0x20`, `+0x28`, `+0x2c`, `+0x4208`, `+0x420c`
- module base, AEX SHA-256, thread id, hit order

Also include the final AE render result/hash from the same run.

## Acceptance

- `answered`: all fields above are from one run of the frozen case and addresses are module-relative/resolved after load.
- `answered_partial`: at least sampler coordinates + source metadata + caller context are present, with missing fields named.
- `failed_*`: hook did not fire, module/hash mismatch, mixed runs, or case mismatch.

Do not infer missing values and do not claim algorithm equivalence from the final PNG alone.
