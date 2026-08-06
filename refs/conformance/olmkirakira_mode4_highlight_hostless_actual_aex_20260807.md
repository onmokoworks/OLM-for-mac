# OLMKiraKira Mode4 Highlight hostless actual-AEX gate（2026-08-07）

Status: **highlight planeからPF32 writerまでbit exact**

4×1のcanonical fixtureでray slot 0〜3をゼロ、slot 4だけをHighlightにした。
checked-in AEXの `FUN_18114fd90 @ 0x18114fd90` を直接呼び、続いて
`FUN_18114e460 @ 0x18114e460` のMerge mode 1 outer compose/PF32 writerを
実行した。WindowsとAEは使用していない。

実AEXのaggregation出力16 FLOAT32 wordsは、Mac productionの
`AddColoredUnion` とMode4 unit highlight scaleを再生したportable modelと全word一致した。
さらに実AEXのcompose/writeback出力16 wordsは、既存のbinary-grounded portable oracle
`tools/emulation/olmkirakira_outer_compose_oracle_20260728.py` と全word一致した。

## 境界

このgateが証明する開始点は、すでに生成されたHighlight scalar planeである。
`MakeSeed` とMode4の11×11等方box filter 3 passは含まれず、その生成自体の
actual-AEX exactを主張しない。

full `FUN_18114f4a0` は15引数に加え、AE-owned vtable/channel object、上流Mat、
embedded OpenCVのTLS/dispatch初期化を必要とする。既存のPython Unicorn
`tools/emulation/aex_loader.py` は今回の10引数leafを実行できるが、full caller scaffoldはない。
AEXCompat側の
`guest/crates/aex-guest-worker/src/x64.rs::GuestEngine::call_win64` は6引数固定であり、
現状は10引数の`fd90`にも15引数の`f4a0`にも直接使用できない。

## Verification

```sh
python3 tools/emulation/test_olmkirakira_mode4_highlight_hostless_actual_aex_20260807.py
```
