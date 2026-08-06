# OLMSmoother v1 PF16 Windows/Mac AE 境界 — 2026-08-06

結論: **現時点ではPF16完全一致を宣言しない**。

同一のAE契約（AE 26.3x87、Software raw 1816、16 bpc、作業色空間None、linear blending無効、Preserve RGB、Straight Alpha）で、Windows返却とMac実機を比較した。

- 対象行: `olmsmoother_v1__canonical_3__case_0001__16bpc`
- パラメータ: Use Color Key=0、Color Key=white、Do Smooth Range=6
- Windows返却ZIPは厳格verifierで受理済み
- MacでロードされたモジュールpathとSHA、3パラメータの順序・型・値は一致
- effect off: EXRの全FLOAT32語がWindowsと完全一致
- effect on: 183語が不一致
- Mac effect onは複数回のfresh AE取得で決定的

PF16 classifierのforward比較に、reverse-table側ポインタを上書きして同じslot同士を比較する移植誤りがあった。actual AEX逆変換に合わせて選択方向とreverse-table-2を比較するよう限定修正した。この修正は実機出力40語を変化させた。

actual AEXのPF16/PF8 classifierを、512個のbinary 3x3 mask × 4方向（計2048呼び出し）で比較すると戻り値は一致した。ただし、同条件を利用したclassifier shortcutはMac AE出力を一語も改善しなかったため採用しなかった。

次にcanonical座標でactual AEXのSubHandler16とMac移植を比較し、制御座標の1点差を確認した。8bit素材からlosslessにwidenされたPF16入力に限り、制御geometryをactual AEXと一致するSubHandler8へ渡し、PF16の補間・色演算は維持した。これによりWindowsとの差の絶対誤差総和は `45.59158470638795` から `33.02504000655608`、最大絶対誤差は `0.7950260639190674` から `0.31183870136737823` へ縮小した。異なるFLOAT32語数はなお183で、完全一致には至っていない。ネイティブPF16入力はこのshadow経路に入らず従来実装へ戻る。

機械可読証拠は `refs/conformance/olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.json`。`pf16_exact_eligible=false` を維持し、未一致を隠してリリースゲートを通さない。
