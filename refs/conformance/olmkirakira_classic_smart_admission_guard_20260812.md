# OLMKiraKira Classic/Smart admission guard（2026-08-12）

Status: **exact_bounded_admission**

Classicは宣言済み5×3・row padding 12の14 tupleと対応する2種のsource fixtureだけをPF8/PF16/PF32でadmitする。format/depth不一致、短い・負の・unaligned rowbytes、geometry/origin差分、tuple変異、sourceの先頭・中央・末尾pixel変異はBAD_CALLBACK_PARAMでfail-closeする。

Smartは別証跡 `olmkirakira_public_smart_bounded_closure_20260812.json` に接続済みで、同じ14 tuple×PF8/PF16/PF32の42セルがClassicおよび固定Windows oracle hashとraw exactである。canonical positive/negative digestとproduction/AEX/AEXCompat identityを本guardから再検証する。pixel checkin callbackはWindows ownerと同じく任意で、要求も呼出しもしない。

追加でMode3 / Merge1 / Horizontal 50 / Rotation 0 / Gain 0.1のwrapped-linear sourceを32×18・padding 12・full Smart requestに限って3深度でadmitする。Windows exported Smart、Mac Classic、Mac Smartのactive bytesは3/3 raw exactで、1条件違いはfail-closeする。

Universal isolated Debug buildはarm64/x86_64とstrict codesign verifyを確認した。installとAE host実行は実施していない。未列挙tuple/source/layoutは引き続きfail-closeする。

Verification: `python3 tools/emulation/test_olmkirakira_classic_smart_admission_guard_20260812.py`
