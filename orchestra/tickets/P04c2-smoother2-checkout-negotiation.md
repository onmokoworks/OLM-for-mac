depends: F53-oracle-cropped-checkout
# P04c2: Smoother2 PreRender forces full-frame output, creating an unequal world pair that its own guard rejects

## Facts (P00b report, "Refusal interpretation")
- Situation "cropped-expand": input 960x540, but Mac PreRender allocates 1920x1080 output. `ValidatePublicWorlds:validate-world-shape@5240` (`mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:5240`) then refuses.
- The original has the same equal-world check (P02f static evidence: worker `0x180003eb0`, comparisons `0x180003f16..0x180003f4e`, throw at `0x180004244`). Keep the guard.
- Open question: does the **original's PreRender** produce this unequal layout for a cropped checkout, or does it return a result rect equal to the request, so that the pair is equal and renders?

## Do
- Trace the original SmartPreRender result_rect/max_result_rect for a cropped checkout on F52c, with a small witness.
- If the original returns equal worlds, make Mac PreRender match and verify the render is exact. If the original also produces unequal worlds and throws, document it as faithful and stop.

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 seed 1 + a fresh seed n100 and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.

## Resume note
- The first attempt (`orchestra/reports/P04c-smoother2-checkout-negotiation.md`) found that with a full input and a cropped extent/request, the original's PreRender returns result `[0,0,7,5]` with max `[0,0,14,10]`, and SmartRender then throws (`0x180022410`). That is faithful. The cropped-input layout itself could not be built on F52c.
- Use F53 (`~/.cache/olm-emu/worker-F53-geom/`, sampler `realistic-v2`) to measure the cropped-input layout, then decide whether to make a Mac fix or document it as faithful.
