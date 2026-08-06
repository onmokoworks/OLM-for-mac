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

PF16 classifierのforward比較に、reverse-table側ポインタを上書きして同じslot同士を比較する移植誤りがあった。actual AEX逆変換に合わせて選択方向とreverse-table-2を比較するよう修正した。

actual AEXのPF16/PF8 classifierを、512個のbinary 3x3 mask × 4方向（計2048呼び出し）で比較すると戻り値は一致した。ただし、同条件を利用したclassifier shortcutはMac AE出力を一語も改善しなかったため採用しなかった。

次にEdgeWalker16（392命令）とSubHandler16（963命令）をactual AEXの全CFGから生成した実装へ置換した。独立fixture 32呼び出し、canonical control 80呼び出し、MainKernel 80呼び出し、10,000 pixelの累積callback比較はすべてactual AEXと完全一致した。補間評価器の`LinearOffsetZeroOneValue`はWindows同様、終端値をobject `+0x18`へ配置した。

最終Mac AE出力は、960×540×RGBAの全FLOAT sampleについて`sample × 32768`が整数（最大delta 0）であり、PF16 wordを正確に正規化している。残る183語はすべてR channel、bbox `(860,440)..(959,539)`内にあり、Windows値は`Mac値 ^ 2.4`で最大絶対誤差`9.624730730184439e-07`まで説明できる。effect offは0/1だけなので、このcross-host Gamma 2.4境界が現れない。

明示的row-major走査はAE host iterate順と端部30 R語が異なるため採用しなかった。プラグインへ逆Gammaや独自走査を入れてWindows EXRだけに合わせることもしていない。PF16演算はactual AEX一致、raw EXR不一致はAE host/export色変換境界として分離する。

機械可読証拠は `refs/conformance/olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.json` と `refs/conformance/olmsmoother_v1_pf16_crosshost_gamma_boundary_20260806.json`。raw EXRについては`pf16_exact_eligible=false`を維持するが、PF16 plugin arithmeticのactual AEX一致は成立する。
