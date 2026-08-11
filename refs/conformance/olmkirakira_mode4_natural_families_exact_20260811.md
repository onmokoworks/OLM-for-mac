# OLMKiraKira Mode 4 natural family matrix（2026-08-11）

Status: **exact**

Horizontal controlに加え、Vertical、Diagonal、Diagonal2、Highlightを各1件、actual AEX full callerのsame-run seed→selected ray→aggregate→PF8/PF16/PF32へ接続した。全5ケースのray 75 wordsとtyped 15 rows（残り4 familyは12 rows）がraw exact、max ULP 0。

Directional 3 familyはnondefault length/rotation、Highlightはconstant 5×3 source・Radius 3で専用branchを分離した。全直積およびlive Windows AE一般一致は主張しない。

Verification: `python3 tools/emulation/probe_olmkirakira_mode4_natural_families_exact_20260811.py`
