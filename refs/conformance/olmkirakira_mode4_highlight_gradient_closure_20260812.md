# OLMKiraKira Mode 4 Highlight gradient closure（2026-08-12）

Status: **raw exact**

5×3、Highlight Radius 3、gradient `i/17` の限定tuple。actual AEX same-run seedからHighlight rayまで15/15 words exact。旧separable実装のword 3/11各1 ULP差はcounterfactualとして保持した。AEXの3回の`boxFilter` callsiteと`RowSum<float,double>`→`ColumnSum<double,float>`を静的に固定し、public Mode 4 PF8/PF16/PF32はそれぞれ`5026fd…`、`c2e203…`、`fbd4f245…`でraw exact。

Mode 2の同tupleは3深度exactの回帰control。Mode 1も別のhash-bound PF8 source-decode closure `olmkirakira_pf8_source_decode_closure_20260812.json` （SHA-256 `d3da9c00aa57297f7b2fa937803f6e8a2b1f955f01884e65edaed85435f03bb3`）を適用後、この固定tupleは3深度exactである。
