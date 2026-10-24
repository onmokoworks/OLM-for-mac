depends: P03a-distancegradation-pf32-downsample-ulp
# P03b: PF32 nonfinite / HDR inputs: Mac-only refusals in four plugins

## Witnesses (T15b report, section "Five Mac-only refusals"; reduced witnesses in `tests/fuzz_corpus/<plugin>/T15b-odd-even-realistic/`)
In each case the original renders, and Mac returns a refusal (black in AE). Replacing only the nonfinite/HDR lanes with 0.5 makes Smart exact, so these are admission gaps, not geometry bugs.
- DirectionalBlur: `RenderWorld:pf32-neutral-nonfinite-input@1815` (reduced 1x5, 1/3).
- KiraKira: `SmartRender:tuple-or-source@2933`; the finite color check at `mac/OLMKiraKira/OLMKiraKira.cpp:2128`, composed at `:2925` (reduced 1x1, blue qNaN, Channel=5, Blur Mode=2).
- DistanceGradation: `RenderBits:pf32-smart-bounded-sdr@2163`, twice. Once with HDR RGB plus Gaussian 2696 and Power≠1 (predicates at `:2057`), once with nonfinite plus Bilateral radius 0 (restriction at `:2052`).
- RadialBlur: `RenderRotationTyped:generic-size-variation-topology@3762`, because `BuildRadialSizeFactorPlaneAEX` (`mac/OLMRadialBlur/OLMRadialBlur.cpp:1798`) rejects nonfinite alpha before labelling (reduced 1x4).

## Do
For each plugin, determine from disassembly what the original does with NaN/Inf/HDR values on that path: comparisons with NaN, float→int conversions (x86 cvttss2si gives 0x80000000), min/max operand order, and clamping. Then implement exactly that, so the refusal goes away and the output is byte-exact. If the original's behaviour depends on something we cannot reproduce faithfully, keep the refusal and document why.

## Acceptance
- All five witnesses either exact, or kept as a refusal with a documented reason.
- Per touched plugin: realistic + odd-even-v1 seeds 2026/2027 n150 with no new mismatches; default fuzz seed 1 n300 with no exact→non-exact; all its corpora replay true; unit tests before/after.

## Rules
- Use 1-2 processes. Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- The stop rule applies. Partial progress, plugin by plugin, is valuable.
