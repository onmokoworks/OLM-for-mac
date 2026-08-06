# ColorKeep パラメーターUI証拠境界（2026-08-06）

## 結論

ColorKeep の `PF_Cmd_PARAMS_SETUP` は、表示名を除く登録ABIについて
actual 2025 AEX と現在のMac実装が完全一致している。

- inputを除く登録行数: 101
- disk ID: `1`、`2..101`
- 型: slider 1行、color 100行
- flags / ui_flags
- sliderの有効範囲、表示範囲、既定値
- colorのcurrent/default raw値

これらを正規化した4040-byte streamはbyte exactである。
`GLOBAL_SETUP`も、version / `out_flags` / `out_flags2` の12 bytesが
actual AEXとMac実装で完全一致している。

## 表示名について証明できること

actual AEX本体とMac文字列テーブルの双方に、次のASCII文字列が
NUL終端で完全一致して存在する。

- `Enabled Color Num`
- `Color`

したがってMac側が独自に翻訳・改名した状態ではない。

## 表示名について証明していないこと

現在のhostless actual-AEX fixtureは、Windows DLL/CRTの文字列テーブル
初期化を実行せずにexported Effect entryを直接呼ぶ。そのためactual側の
101個の `PF_ParamDef.name[32]` はすべてゼロである。

このゼロ領域を名前一致の証拠には使わない。現時点の正確な分類は、

`literal_exact_registration_binding_unproved_hostless`

である。つまり文字列リテラル自体は一致するが、actual AEXが各行へ
その文字列を結び付ける動的過程と、AE上のローカライズ・レイアウトは
このfixtureだけでは未証明である。

## 回帰ゲート

```sh
python3 tools/emulation/test_colorkeep_params_setup_actual_aex_20260805.py
python3 tools/emulation/test_colorkeep_global_setup_actual_aex_20260805.py
```

前者はraw name領域が全ゼロである境界も明示的に検査し、将来これを
誤って「表示名exact」と一般化することを防ぐ。

