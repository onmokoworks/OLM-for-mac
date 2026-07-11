# Claude prompt: OLMRadialBlur tiny Rotation follow-up

作業ディレクトリ:
/Users/onmk/Documents/Projects/Personal/OLM as

まず読むファイル:
- /Users/onmk/Documents/Projects/Personal/OLM as/refs/conformance/olmradialblur_tiny_rotation_lane_state_20260703.md
- /Users/onmk/Documents/Projects/Personal/OLM as/refs/conformance/olmradialblur_tiny_rotation_intake_audit_20260703.md
- /Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_direct_postreturn_20260705.md
- /Users/onmk/Documents/Projects/Personal/OLM as/notes/OLMRadialBlur_ASM_FACTS.md

前提:
- 目的は OLMRadialBlur tiny Rotation `case_0010` witness `(1614,6)` の白化理由を binary-grounded に確定すること。
- Mac 側候補は現在 `[0,0,0,255]`、Windows Software 参照は `[255,255,255,255]`。
- same-row の直接 source cells は全部黒で、row843 側の正の寄与クラスタが怪しい。
- 2026-07-05 の Windows runtime trace で、前回 missing だった direct post-return registers は取れた。

今回の新事実:
- request_id: `olmradialblur_tiny_rotation_anchor_context_watch_followup_direct_postreturn_20260705`
- status: `partial_with_direct_postreturn_registers`
- retained watchpoint hit: `OLMRadialBlur+0x111f`
- caller path: `+0x111f -> +0x4ec8 -> +0x7b4a -> +0x41f8 -> entry_point+0x458`
- direct post-return registers:
  - `+0x7b4a`: `r9=1`, `r10=2`, `r14=0x780`, `r12=0x438`
  - `+0x41f8`: `r9=1`, `r10=2`, `r14=8`, `r15=0`
- typed sampled cells remain:
  - row844 col1603 = `bc70f44b bc70f44b bc70f44b 3f800000`
  - row845 col1603 = `bd46d045 bd46d045 bd46d045 3f800000`
  - row843 col1601 = `3dd69702 3dd69702 3dd69702 3f800000`
  - row843 col1602 = `3de119ce 3de119ce 3de119ce 3f800000`
- `f250 = 00000000 3f800000 00000000 00000000`
- `f252 = 00000000`
- まだ未取得:
  - first upstream promotion branch
  - `+0x7404` direct post-return / normalized-final bridge
  - typed normalized final `+0xe` promotion state

お願いしたいこと:
1. この新 trace だけを前提に、`+0x7b4a` / `+0x41f8` がアルゴリズム上どの段階に対応するか仮説を整理してほしい。
2. 次の Windows debugger ask を 1 本だけ、最小で判別力が高い形に絞って提案してほしい。
3. もし Mac 側で先に読める asm / decomp 上の確認ポイントがあるなら、アドレス・関数・見るべきレジスタ/メモリを具体的に列挙してほしい。

禁止:
- PNG 見た目合わせの提案
- global validity-alpha rewrite の提案
- final byte conversion だけをいじる提案

期待する出力:
- 「現状の解釈」
- 「次の最小 Windows ask」
- 「Mac 側で今すぐ確認できる箇所」
- 「危ない読み違いポイント」
