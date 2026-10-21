## Goal
Decide, per plugin, which render route real After Effects uses for the ORIGINAL Windows AEX,
so the compatibility target is the right route.

## Facts
- F17 (`orchestra/reports/F17-fuzz-per-route-oracle.md`): in the emulator the original Classic
  command writes nothing (all-zero destination) for ColorKey, DirectionalBlur, KiraKira, RadialBlur,
  Smoother2, ToonDilate on 300/300 seed-1 inputs; ColorKeep/OLMBlur/DistanceGradation Classic render.
- AE calls SmartPreRender/SmartRender (never Classic Render) for effects that set
  PF_OutFlag2_SUPPORTS_SMART_RENDER in GlobalSetup (and PiPL OutFlags2 must agree).

## Steps
1. For each of the 10 original AEX: read PiPL OutFlags/OutFlags2 (resources) AND the out_flags /
   out_flags2 values written by PF_Cmd_GLOBAL_SETUP in the emulator. Report SMART_RENDER,
   FLOAT_COLOR_AWARE, DEEP_COLOR_AWARE, threaded flags etc.
2. Same for the Mac builds (PiPL + GlobalSetup).
3. Table: plugin | original smart? | original classic used by AE? | Mac flags agree? | target route.
4. Flag any Mac/original flag disagreement as a compatibility bug (AE behavior differs).
No production changes unless a flag disagreement is unambiguous; then fix it as a separate commit
with evidence.
