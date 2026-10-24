# P04a: DistanceGradation refuses at 32 bpc with its DEFAULT params (black in AE)

## Facts (P00b, `orchestra/reports/P00b-ae-realism-audit-rerun.md`, "Refusal interpretation")
- With the real PARAMS_SETUP defaults, every PF32 render of the real Mac bundle returns 516 with `RenderBits:pf32-smart-profile@2201`. The guard is the union of admission profiles at `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2180-2201`.
- `P00b-evidence/original-default-probe.json`: at 32x24 with zero overrides, the original (F52c) succeeds at PF8/16/32, and its outputs are all-zero buffers. Mac PF8/16 also give all-zero output; Mac PF32 refuses.
- The fuzz adapter clamps the out-of-range builder In/Out default 0 to 1, so the fuzzer never generated this default. That is why it was missed. P00b ran before P03b (which changed PF32 admission at :2163), so first recheck on HEAD with `tools/fuzz/probe_P00b_defaults.py` or equivalent.
- A user who applies DistanceGradation in a 32 bpc comp without touching params sees black.

## Do
- Reproduce on HEAD. From disassembly, find what the original computes for In/Out=0 (and other out-of-range builder values the real UI can produce) at PF32, and admit it through the general path. Do **not** add a default-only zero-output shortcut.
- Make the fuzz adapter able to generate the unclamped real defaults (opt-in, or add them as explicit corpus cases), so this stays covered. Keep default generation and replay identical.

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 seed 1 + a fresh seed n100 and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
