# OLMKiraKira Mode4 full caller hostless exact gate（2026-08-07）

Status: **exact**

actual AEX `FUN_18114f4a0` を16引数で直接実行し、4×1 canonical PF32 fixtureのMakeSeed、Highlight 11×11 box filter 3 pass、Mode-1 aggregation、Merge-1 compose/PF32 writerを通した。

- Highlight plane: 4/4 words exact
- aggregation: 16/16 words exact
- final PF8 ARGB: 16/16 bytes exact
- final PF16 ARGB: 32/32 bytes exact
- final PF32 ARGB: 64/64 bytes exact
- max ULP: 0
- PF Handle Suite: Acquire 12 / Release 12、faultなし

Mac productionは `core/kirakira_highlight.h` の同じportable primitiveを使用する。最終compose/writerはtyped world上で既存binary-grounded oracleと比較した。PF8/PF16はclamp後に255/32768倍し、ゼロ方向へ切り捨てる。これはhostless actual-AEX境界であり、live Windows/AE出力のraw exact主張ではない。

Verification: `python3 tools/emulation/probe_olmkirakira_mode4_fullcaller_scaffold_20260807.py`
