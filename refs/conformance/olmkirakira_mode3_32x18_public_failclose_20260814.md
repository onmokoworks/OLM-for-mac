# OLMKiraKira Mode3 32x18 public fail-close（2026-08-14）

Status: **exact_fail_closed_unlisted_source**

現行Mac public `EffectMain`へMode3 / Horizontal Length 50 / 32x18をPF8・PF16・PF32で入力した。全深度が `PF_Err_BAD_CALLBACK_PARAM` を返し、入力全領域は不変、出力全領域は未変更だった。別途raw exactで証明したwrapped-linear sourceだけを32x18へadmitし、このmodulo-192-alpha sourceには数値一致やWindows owner一致を主張しない。
