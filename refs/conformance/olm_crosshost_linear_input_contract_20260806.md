# OLM Windows/Mac 共通linear入力契約（2026-08-06）

## 結論

既存7-row返却のColorKeep/Kiraは、Windows/Macとも同じPNG、AE 26.3x87、
Software、working space None、linear blending offを指定していた。しかしeffect-offの
時点で、全2,073,600 pixelのRGB 3値、合計6,220,800値が全深度で異なった。
alphaは一致した。従ってこの差はプラグインworkerではなく、PNGの素材解釈から
FLOAT32 EXR書き出しまでのhost経路に属する。

また、旧契約はPreserve RGBを宣言していたが、実runnerは
`FootageItem.replace()`後の`mainSource.preserveRGB`を明示設定・live readbackして
いなかった。Mac ExtendScriptではこのpropertyが`undefined`になる観測もあるため、
propertyの存在だけを共通契約の根拠にはしない。

## 新しい最小契約

- 入力は1920×1080、RGBA、非圧縮scanline FLOAT32 OpenEXR。
- 元PNGの各8-bit code valueを`value / 255.0`として一度だけbinary32へ丸める。
- EXRにICC、gamma、chromaticities属性を付けず、AE projectのworking spaceはNone、
  linear blendingはoff、alphaはstraightとする。
- `preserveRGB`をExtendScriptが公開するhostでは、replace後にtrueを書き、trueを
  readbackできなければfail-closeする。公開しないhostではAPI非公開を記録する。
- 両hostで`colorProfileName`、alpha mode、source extensionをlive readbackする。
- 色変換なしの最終証明は設定名ではなく、effect-off EXRの全raw FLOAT32 wordが
  0差であることとする。effect-onも同様に0差でなければpixel exactにしない。

fixtureは
`refs/fixtures/olm_crosshost_linear/opaque_cells_linear_float32.exr`、生成根拠は
同ディレクトリの`manifest.json`、再生成器は
`scripts/generate_olm_crosshost_linear_fixture_20260806.py`である。

## 既存証拠の再利用境界

既存7-row返却から再利用できるのは、Windows AEXのhash、AE process/module binding、
parameter readback、およびColorKeepの同一host内での保持／棄却関係である。
既存PNG由来のeffect-off/effect-on画像はcross-host raw exactには再利用できない。

新たなWindows観測はColorKeepとOLMKiraKiraの代表ケースをPF8/PF16/PF32で各1行、
合計6行に限定する。各行がeffect-offとeffect-onを同時に返すため、これ以上行を
減らすと少なくとも1プラグイン／native depthのeffect-onが未観測になる。
Smootherは別laneのためこの再取得へ混ぜない。

## 実行と判定

Windowsでは`olm_crosshost_linear_input_20260806.zip`を展開し、AEを閉じた状態で
次を実行する。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_olm_crosshost_linear_input_20260806.ps1
```

同一packageをMacで実行して同形式のreturnを作成後、paired verifierへWindows、
Mac、request packageの順で渡す。verifierは6行すべてのeffect-off/effect-onをraw
FLOAT32で比較し、1 wordでも異なればfail-closeする。

Mac側はAEを1processだけ起動した状態で次を実行する。

```bash
python3 scripts/run_olm_crosshost_linear_input_mac_ae_20260806.py --run
python3 scripts/verify_olm_crosshost_linear_input_20260806.py \
  RETURN_OLM_CROSSHOST_LINEAR_INPUT_20260806.zip \
  refs/returns/mac/RETURN_OLM_CROSSHOST_LINEAR_INPUT_MAC_20260806.zip \
  refs/reference_requests/olm_crosshost_linear_input_20260806.zip
```

この契約が閉じるのはColorKeep/Kiraの指定代表ケース、PF8/PF16/PF32、AE 26.3x87、
Softwareレンダーだけである。ほかの入力、mode、AE version、rendererへ一般化しない。
