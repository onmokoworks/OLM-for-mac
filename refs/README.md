# refs ディレクトリ案内

このディレクトリには、Windows／Macの参照出力、固定fixture、完全一致の証拠、
Windows AEへの依頼パッケージを保存します。

現在のリリース判断では、古いPNG差分レポートや探索用requestより次を優先してください。

- [`conformance/OLM_MAC_RELEASE_NOTES_20260806.md`](conformance/OLM_MAC_RELEASE_NOTES_20260806.md)：日本語リリースノート
- [`conformance/olm_release_completion_matrix_20260806.md`](conformance/olm_release_completion_matrix_20260806.md)：プラグイン別の完成対象と証拠境界
- [`conformance/olm_release_gate_status_20260806.json`](conformance/olm_release_gate_status_20260806.json)：最終Mac統合ゲート
- [`reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`](reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip)：保留中のWindows 7観測

`conformance/`の古い日付の記録は、調査過程と判断根拠を保存する履歴です。最新状態を
決める正本ではありません。現在のWindows作業で過去のpending requestを一括再送せず、
hash固定された最小7行パッケージだけを使用してください。

## 旧Reference Render Diff Harness

以下は初期のPNG差分harnessの説明です。過去fixtureの再現用として残しています。

`fixtures/test_cellanim.png` is the shared input image for Win/Mac renders.

Expected local-only folders:

- `win/` Windows reference PNG sequence
- `mac/` macOS port PNG sequence
- `diff/` amplified diff output

These folders are ignored by git.

Usage:

```sh
python3 refs/scripts/make_test_cellanim.py
refs/scripts/diff_all.sh
```

Parameterized case verification:

```sh
python3 refs/scripts/verify_cases.py
```

The default manifest is `cases/olmsmoother_v1_minimal.json`. It records the
input image, expected frame names, and the parameters used for each render.
Reports are written to `reports/`, and amplified diff images are written to
`diff/`.

Windows reference transfer:

```sh
python3 refs/scripts/normalize_render_names.py path/to/ae_png_sequence
python3 refs/scripts/package_win_reference.py path/to/rendered_pngs --out OLMSmoother_win_reference.zip
python3 refs/scripts/import_win_reference.py path/to/OLMSmoother_win_reference.zip
```

If AE outputs arbitrary sequence names, normalize them first. The normalizer maps
sorted PNGs to the manifest case order and writes `f0.png`, `f1.png`, and so on
into `_normalized/`. The package stores PNGs, parameter values from the manifest,
and SHA-256 hashes. The import command validates the package and copies the
reference frames into `win/`.

For a single file:

```sh
refs/scripts/diff_one.py refs/win/frame.png refs/mac/frame.png refs/diff/frame.diff.png
```

For AE-free algorithm debugging, see `ALGORITHM_HARNESS.md`.

Windows-side reference requests live in `reference_requests/`. These are
case lists that can be handed to the Windows AE/Codex environment when the Mac
port needs stronger CUDA vs SOFTWARE or parameter-isolation references.

Fresh-instance default capture for all OLM effects now lives in:

- `reference_requests/olm_fresh_instance_defaults_20260629.json`

Use that request when we need the original Windows AEX cold-start defaults and
property-tree shape, rather than a tuned validation case.

After importing that return, audit it with:

```sh
python3 scripts/audit_windows_fresh_defaults.py path/to/imported/reference_manifest.json
```

Imported Windows AE reference sets live in `win_references/`:

- `win_references/20260604_olm/`: first broad OLM reference package.
- `win_references/20260605_extra/`: Distance Gradation, RadialBlur img2, and
  Smoother v2 extra references from Windows AE 25.2x131.
- `win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return/`:
  final randomized Windows Software holdout set, split into 9 per-plug-in
  manifests with 10 random cases each.
- `win_references/olm_final_random_smoke_20260629_windows_reference_return/`:
  smaller randomized Windows Software smoke set. Some requested values were
  rejected by AE scripting, so the returned manifest's effective values are the
  source of truth for those cases.

Summarize that final randomized holdout set with:

```sh
python3 scripts/summarize_combined_reference_manifest.py \
  refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return \
  --output-md refs/reports/olm_final_random_per_plugin_10cases_20260629_summary.md \
  --output-json refs/reports/olm_final_random_per_plugin_10cases_20260629_summary.json
```

Treat that dataset as a final validation / holdout suite, not as the primary
spec-discovery source. Use the narrower reference requests and runtime traces to
establish the algorithm first, then spend the randomized set as a confidence
check near the end.

A short combined note for both randomized sets lives at:

- `refs/reports/olm_final_random_reference_sets_20260629.md`

If a returned zip embeds `reference_requests/*.json`, materialize those request
files into the tracked repo so `check_reference_request_status.py` and
`print_next_olm_action.py` can see them:

```sh
python3 scripts/materialize_embedded_reference_requests.py \
  path/to/windows_return.zip \
  --dest refs/reference_requests
```

To turn an imported Windows reference set into Mac AE batch-validation request
directories under `handoff/ae_pixel_validation_20260618/requests/`, use:

```sh
python3 scripts/materialize_ae_pixel_validation_requests_from_refs.py \
  refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return \
  --replace
```

The 2026-06-29 final randomized holdout request id list is tracked at:

- `refs/reports/final_random_holdout_request_ids_20260629.txt`

You can preflight the AE wrapper generation without launching a render:

```sh
python3 scripts/run_ae_validation_batch.py \
  --request-ids-file refs/reports/final_random_holdout_request_ids_20260629.txt \
  --dump-js /tmp/ae_final_random_holdout_wrapper.jsx
```

After Mac AE renders are collected, verification can now use either packaged
request zips or materialized request directories. For the final randomized
holdout lane, the direct directory flow is:

```sh
python3 scripts/verify_ae_pixel_validation_batch.py \
  handoff/ae_pixel_validation_20260618/requests \
  path/to/final_random_holdout_results_dir \
  --run-dir /tmp/olm_final_random_holdout_verify
```

The batch verifier matches result folders/zips against request ids and writes a
`batch_summary.json` plus per-request diff reports under the chosen run dir.

Smoke-test the whole AE-free harness:

```sh
python3 refs/scripts/smoke_algorithm_harness.py
```

Smoke-test the simple ColorKeep algorithm CLI:

```sh
python3 refs/scripts/smoke_colorkeep_cli.py
```

End-to-end reference package test:

```sh
python3 refs/scripts/run_reference_test.py path/to/windows_reference_folder_or_zip \
  --input refs/fixtures/test_cellanim.png \
  --command 'python3 refs/scripts/identity_image_cli.py --input "{input}" --params "{params}" --output "{output}"'
```
