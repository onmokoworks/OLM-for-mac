# OLMSmoother2 PF32 SmartRender-to-installed chain

Verdict: `PASS_PRODUCTION_EFFECTMAIN_SMARTRENDER_PF32_TO_ACTUAL_AEX_CORE_INSTALLED_IDENTITY`

Production `EffectMain(PF_Cmd_SMART_RENDER)` executes layer/output checkout, all 15 parameter checkouts, PF32 RenderBits, and all checkins. Its padded bytes equal the natural actual-AEX classifier/PF32 worker/writer fixture and are bound to installed Universal SHA `c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f`.

Actual-AEX exported entry invocation, SmartPreRender, and AE-host loading remain separate boundaries.
