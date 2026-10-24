depends: F53-oracle-cropped-checkout
# P04d: ColorKeep refuses a cropped checkout (`ColorKeepValidateWorldPair:world-alignment@219`)

## Facts (F53, `orchestra/reports/F53-oracle-cropped-checkout.md`, survey-auto)
- Under realistic-v2 (cropped checkout from the PreRender request ∩ layer), seed 1 n100: ColorKeep 97 exact / 3 Mac-only refusals at `ColorKeepValidateWorldPair:world-alignment@219`. The original renders all three. Per-case data are in `F53-evidence/survey-auto-*.jsonl`.
- In AE this is black whenever the checkout origin or size does not line up with the output in the way the Mac guard expects.

## Do
- Reproduce on F53 (`~/.cache/olm-emu/worker-F53-geom/`, `--geometry realistic-v2`). Read P02a (ColorKeep geometry) for the iterate contract the original uses, and find from disassembly how the original maps input to output when their origins/sizes differ. Implement that and remove the refusal only where the original has none.
- F53 also notes a pre-existing bundle-host limitation: ColorKeep bundle `iterate` is unsupported in the bundle host. Fix it in the host if it is cheap, so the bundle smoke covers ColorKeep.

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 and realistic-v2, seed 1 + a fresh seed, n100 each, and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
