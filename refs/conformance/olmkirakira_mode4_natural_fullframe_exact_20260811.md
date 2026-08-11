# OLMKiraKira Mode4 natural full-frame exact gate（2026-08-11）

Status: **exact**

actual AEX full callerの同一実行で、vtable seed 15 words、Horizontal slot 1 / Length 5 / Rotation 0°、aggregate入口ray 15 wordsを結んだ。portable Mode4 chainとray全15 wordsがraw exactで、同じaggregateからPF8/PF16/PF32 typed outputまでbyte exact。

これは5×3の1 source caseに限るhostless境界であり、live Windows AEや任意sourceの一般一致主張ではない。

Verification: `python3 tools/emulation/probe_olmkirakira_mode4_natural_fullframe_exact_20260811.py`
