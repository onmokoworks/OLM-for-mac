# OLM for Mac

Private working repo for porting OLM After Effects plug-ins to modern macOS.

## Porting Status

Current progress:

- `OLMSmoother2`: port complete
- `OLMSmoother` v1: port in progress
- `DistanceGradation`: port complete
- `ColorKeep`: port complete
- `OLMBlur`: port in progress
- all other OLM plug-ins: not started / pending

Current source:

- `mac/OLMSmoother2/`
- `mac/OLMDistanceGradation/`
- `mac/ColorKeep/`
- `mac/OLMBlur/`
- `mac/OLMSmoother/`
- main implementation: `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`
- reverse-engineering notes: `disasm/v1_analysis/`
- verification fixture/scripts: `refs/`

Large local artifacts are intentionally ignored:

- Ghidra projects
- full decompiler dumps
- raw disassembly dumps
- built `.aex` / `.plugin` binaries
- local Win/Mac render outputs

## Build

This source was developed inside the After Effects SDK template tree:

```sh
/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother
```

To build, copy or sync `mac/OLMSmoother/` into the AE SDK `Examples/Template`
folder as `OLMSmoother`, then run:

```sh
cd "/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother/Mac"
xcodebuild -project OLMSmoother.xcodeproj -configuration Debug
```

Install target used during development:

```sh
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin
```

## Verification

Generate the shared input image:

```sh
python3 refs/scripts/make_test_cellanim.py
```

Render the same AE comp on Windows and macOS, then place PNGs here:

- `refs/win/`
- `refs/mac/`

Run:

```sh
refs/scripts/diff_all.sh
```

`max=0` means byte-perfect for that frame.

For parameter-aware verification, use the case manifest:

```sh
python3 refs/scripts/verify_cases.py
```

The default manifest is `refs/cases/olmsmoother_v1_minimal.json`; it maps each
frame to the input image and parameter values used for that render. This makes
it easier to tell whether a mismatch is limited to key-color handling,
tolerance, or the shared smoothing kernel.

To move Windows reference renders into this Mac workspace, package them on the
Windows side and import the zip here:

```sh
python3 refs/scripts/normalize_render_names.py path/to/ae_png_sequence
python3 refs/scripts/package_win_reference.py path/to/rendered_pngs --out OLMSmoother_win_reference.zip
python3 refs/scripts/import_win_reference.py path/to/OLMSmoother_win_reference.zip
```

If AE outputs arbitrary sequence names, normalize them first. The normalizer maps
sorted PNGs to the manifest case order and writes `f0.png`, `f1.png`, and so on
into `_normalized/`. The package includes PNGs, parameter values, and SHA-256
hashes. Importing writes the checked frames into `refs/win/`.

## Status

See `notes/HANDOFF.md`.

---

# OLM for Mac 日本語メモ

OLM After Effects plug-in 群を、現行 macOS / After Effects 向けに移植するためのプライベート作業 repo です。

## 移植状況

現在の進捗:

- `OLMSmoother2`: 移植完了
- `OLMSmoother` 初代: 移植中
- `DistanceGradation`: 移植完了
- `ColorKeep`: 移植完了
- `OLMBlur`: 移植中
- その他の OLM plug-in: 未着手 / 移植待ち

主なソース:

- `mac/OLMSmoother2/`
- `mac/OLMDistanceGradation/`
- `mac/ColorKeep/`
- `mac/OLMBlur/`
- `mac/OLMSmoother/`
- 初代 Smoother の中心実装: `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`
- 初代 Smoother の解析メモ: `disasm/v1_analysis/`
- Win/Mac 出力比較用 fixture と scripts: `refs/`

Git に入れていないもの:

- Ghidra project DB
- decompiler の巨大 dump
- raw disassembly dump
- build 済み `.aex` / `.plugin`
- Win/Mac のローカル render 結果

これらはサイズが大きい、差分レビューしづらい、またはローカル生成物なので `.gitignore` で除外しています。

## ビルド

作業中は After Effects SDK の template tree 上でビルドしています。

```sh
/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template
```

例: 初代 `OLMSmoother` をビルドする場合:

```sh
cd "/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother/Mac"
xcodebuild -project OLMSmoother.xcodeproj -configuration Debug
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
zipには `INSTALL.txt`, `AE_VALIDATION_CHECKLIST.txt`, `manifest.json` も入ります。AE実機検証時はチェックリストに沿って、AE version、renderer/project_gpu_accel_type、各plug-inのload/apply/render結果を返してください。

```sh
xattr -cr build/Debug/<PluginName>.plugin
xcodebuild -project <PluginName>.xcodeproj -configuration Debug
```

## 初代 OLMSmoother の検証方針

Win 版 `.aex` の出力を reference として、Mac 版 `.plugin` の出力が pixel 単位で一致するか確認します。

fixture 画像を生成:

```sh
python3 refs/scripts/make_test_cellanim.py
```

Windows AE と macOS AE で同じ comp を render し、PNG sequence を以下へ置きます。

- Windows reference: `refs/win/`
- Mac port output: `refs/mac/`

比較:

```sh
refs/scripts/diff_all.sh
```

`max=0` なら、その frame は byte-perfect です。

パラメータ込みで検証する場合:

```sh
python3 refs/scripts/verify_cases.py
```

デフォルト manifest は `refs/cases/olmsmoother_v1_minimal.json` です。各
frame と入力画像、パラメータ値を紐づけているので、ズレが key-color 側か、
tolerance 側か、共通 smoothing kernel 側かを切り分けやすくします。

Windows 実機で出した reference render をこの Mac 環境へ持ってくる場合:

```sh
python3 refs/scripts/normalize_render_names.py path/to/ae_png_sequence
python3 refs/scripts/package_win_reference.py path/to/rendered_pngs --out OLMSmoother_win_reference.zip
python3 refs/scripts/import_win_reference.py path/to/OLMSmoother_win_reference.zip
```

AE が任意の連番名で吐いた場合は、先に normalize します。manifest のケース順に
sorted PNG を対応させて、`_normalized/` に `f0.png`, `f1.png` ... を作ります。
zip には PNG、manifest 上のパラメータ値、SHA-256 hash が入ります。import 時に
検証してから `refs/win/` へコピーします。

## 引き継ぎ

詳しい引き継ぎメモは以下です。

```txt
notes/HANDOFF.md
```

初代 `OLMSmoother` の残作業は主に以下です。

- first-pass key-mask path の実装
- Win reference render との byte-perfect 検証
- 8-bpc が合った後の 16-bpc 検証
- 32-bpc float path の扱い確認
