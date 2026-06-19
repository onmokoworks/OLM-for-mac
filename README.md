# OLM for Mac

Private working repo for porting OLM After Effects plug-ins to modern macOS.

## Porting Status

Correctness policy:

- Final completion means `AE exact`: Mac AE output matches the Windows AE
  Software render reference with zero diff for the declared bit depth.
- AE-free CLI exactness is intermediate evidence, not final completion.
- Tolerance-gated regression smokes, off-by-1 results, and known-red probes are
  not release-complete.
- Current conformance status is tracked in `notes/CONFORMANCE_LEDGER.md`; terms
  are defined in `notes/AE_EXACT_CONFORMANCE.md`.

Current progress:

- 10 Mac plug-in projects build as universal Debug bundles:
  `ColorKeep`, `OLMBlur`, `OLMColorKey`, `OLMDirectionalBlur`,
  `OLMRadialBlur`, `OLMKiraKira`, `OLMToonDilate`, `OLMDistanceGradation`,
  `OLMSmoother`, and `OLMSmoother2`.
- AE-free CLI regression gates exist for `ColorKeep`, `OLMBlur`,
  `OLMColorKey`, `OLMToonDilate`, stable `OLMDistanceGradation` cases,
  `OLMRadialBlur` Zoom/tiny Rotation slices, and `OLMSmoother2` key/v1
  compatibility slices. These are regression checks, not final completion
  claims.
- Known-red diagnostic probes remain for unresolved paths in
  `OLMDirectionalBlur`, `OLMRadialBlur` Inner/Edge Fade, `OLMKiraKira`, and
  `OLMSmoother2` no-key v2. These are kept as measurement scaffolds, not
  release gates.
- Final AE-host load/apply/render validation is pending on a real After Effects
  machine.

Current source:

- Mac plug-ins: `mac/`
- CLI algorithm probes: `cli/` and `refs/scripts/`
- Windows references: `refs/win_references/`
- pending Windows reference requests: `refs/reference_requests/`
- reverse-engineering notes: `notes/`

Large local artifacts are intentionally ignored:

- Ghidra projects
- full decompiler dumps
- raw disassembly dumps
- built `.aex` / `.plugin` binaries
- local Win/Mac render outputs

## Build

The repo builds against the local After Effects SDK. Create/update the ignored
SDK symlinks and build all Mac plug-ins with:

```sh
scripts/build_all_mac_plugins.sh
```

To build a single plug-in:

```sh
xcodebuild -project mac/<PluginName>/Mac/<PluginName>.xcodeproj -configuration Debug build
```

Install target used during development:

```sh
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin
```

## Verification

Run the quick AE-free regression suite:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

Run the full aggregate suite, including registered red-measurement probes:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py
```

Package pending Windows reference requests:

```sh
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/package_reference_requests.py --pending
```

Package Mac plug-ins for AE-host validation:

```sh
scripts/package_mac_plugins.sh
```

Returned AE-host validation JSON can be checked in two modes:

```sh
python3 scripts/verify_ae_validation_result.py AE_VALIDATION_RESULT.json
python3 scripts/verify_ae_validation_result.py --require-all-pass AE_VALIDATION_RESULT.json
```

The first command accepts complete, actionable reports even when a plug-in
failed in AE. The second command is the all-pass release gate.

## Status

See `notes/CONFORMANCE_LEDGER.md`, `notes/AE_EXACT_CONFORMANCE.md`,
`notes/HANDOFF_CODEX.md`, and `notes/PORTING_BOARD.md`.

---

# OLM for Mac 日本語メモ

OLM After Effects plug-in 群を、現行 macOS / After Effects 向けに移植するためのプライベート作業 repo です。

## 移植状況

正しさの基準:

- 最終完了は `AE exact` のみです。同一bit depthで、Mac AE出力がWindows
  AE Software render参照と差分ゼロになった状態を指します。
- AEなしCLIのexactは強い中間証拠ですが、最終完了ではありません。
- tolerance付き回帰ゲート、off-by-1、known-red probeは完了扱いしません。
- 現在のconformance状態は `notes/CONFORMANCE_LEDGER.md`、用語定義は
  `notes/AE_EXACT_CONFORMANCE.md` を見ます。

現在の進捗:

- 10本のMac plug-in projectがDebug universal bundleとしてビルド可能:
  `ColorKeep`, `OLMBlur`, `OLMColorKey`, `OLMDirectionalBlur`,
  `OLMRadialBlur`, `OLMKiraKira`, `OLMToonDilate`, `OLMDistanceGradation`,
  `OLMSmoother`, `OLMSmoother2`
- AEなしCLIの回帰ゲートあり:
  `ColorKeep`, `OLMBlur`, `OLMColorKey`, `OLMToonDilate`,
  `OLMDistanceGradation`の安定ケース、`OLMRadialBlur`のZoom/tiny Rotation、
  `OLMSmoother2`のkey/v1互換スライス。これは回帰確認であり、最終完了の
  主張ではありません。
- 未解決パスはknown-red診断として維持:
  `OLMDirectionalBlur`, `OLMRadialBlur` Inner/Edge Fade, `OLMKiraKira`,
  `OLMSmoother2` no-key v2
- 最終AE実機のload/apply/render検証は未完了

主なソース:

- Mac plug-in: `mac/`
- CLI algorithm probe: `cli/`, `refs/scripts/`
- Windows reference: `refs/win_references/`
- 追加Windows reference request: `refs/reference_requests/`
- 解析メモ: `notes/`

Git に入れていないもの:

- Ghidra project DB
- decompiler の巨大 dump
- raw disassembly dump
- build 済み `.aex` / `.plugin`
- Win/Mac のローカル render 結果

これらはサイズが大きい、差分レビューしづらい、またはローカル生成物なので `.gitignore` で除外しています。

## ビルド

ローカルの After Effects SDK に対するignored symlinkを作り、全Mac plug-inをまとめてビルド:

```sh
scripts/build_all_mac_plugins.sh
```

単体ビルド:

```sh
xcodebuild -project mac/<PluginName>/Mac/<PluginName>.xcodeproj -configuration Debug build
```

開発中の install 先:

```sh
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
```

全Macプラグインをビルド・universal slice確認・codesign確認して、AE実機へ渡すzipにまとめる:

```sh
scripts/package_mac_plugins.sh
```

既に `scripts/build_all_mac_plugins.sh` を同じセッションで通している場合だけ、再ビルドを省略して梱包できます:

```sh
scripts/package_mac_plugins.sh --skip-build --output /tmp/olm_mac_plugins_Debug.zip
```

zipを展開し、中の `*.plugin` bundle を上記 MediaCore へコピーしてからAfter Effectsを再起動します。codesign が `resource fork, Finder information, or similar detritus not allowed` で落ちる場合は、build product に付いた xattr を消してから再実行します。
zipには `INSTALL.txt`, `AE_VALIDATION_CHECKLIST.txt`, `AE_VALIDATION_RESULT.template.json`, `manifest.json` も入ります。AE実機検証時はチェックリストに沿って、AE version、renderer/project_gpu_accel_type、各plug-inのload/apply/render結果を返してください。戻ってきたJSONは以下で検証できます:

```sh
python3 scripts/verify_ae_validation_result.py AE_VALIDATION_RESULT.json
python3 scripts/verify_ae_validation_result.py --require-all-pass AE_VALIDATION_RESULT.json
```

1行目は失敗plug-inがあっても、AE環境情報やエラー内容が揃った「解析可能な結果」なら通します。2行目は全plug-inが load/apply/render 成功したことをリリースゲートとして確認します。

```sh
xattr -cr build/Debug/<PluginName>.plugin
xcodebuild -project <PluginName>.xcodeproj -configuration Debug
```

## AEなし検証

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
python3 refs/scripts/smoke_all_algorithm_clis.py
```

追加Windows参照の状態確認とパッケージ作成:

```sh
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/package_reference_requests.py --pending
```

Win側で返ってきたreference zipはimportしてrequestに照合します:

```sh
python3 refs/scripts/import_win_reference.py path/to/packed_reference.zip
python3 refs/scripts/verify_reference_request_result.py refs/reference_requests/<request>.json path/to/imported/reference_manifest.json
```

## 引き継ぎ

詳しい引き継ぎメモは以下です。

```txt
notes/HANDOFF_CODEX.md
notes/PORTING_BOARD.md
notes/CONFORMANCE_LEDGER.md
notes/AE_EXACT_CONFORMANCE.md
notes/BIT_DEPTH_REFERENCE_STRATEGY.md
```
