# OLM for Mac

Private working repo for porting OLM After Effects plug-ins to modern macOS.

## Porting Status

Current progress:

- `OLMSmoother2`: port complete
- `OLMSmoother` v1: port in progress
- `DistanceGradation`: port complete
- `ColorKeep`: port complete
- all other OLM plug-ins: not started / pending

Current source:

- `mac/OLMSmoother2/`
- `mac/OLMDistanceGradation/`
- `mac/ColorKeep/`
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
- その他の OLM plug-in: 未着手 / 移植待ち

主なソース:

- `mac/OLMSmoother2/`
- `mac/OLMDistanceGradation/`
- `mac/ColorKeep/`
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

`OLMSmoother2` と `DistanceGradation` は build 済み確認済みです。codesign が `resource fork, Finder information, or similar detritus not allowed` で落ちる場合は、build product に付いた xattr を消してから再実行します。

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
