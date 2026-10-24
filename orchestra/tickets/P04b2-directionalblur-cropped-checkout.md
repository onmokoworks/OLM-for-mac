depends: F53-oracle-cropped-checkout
# P04b2: DirectionalBlur refuses a cropped checkout (input/output world smaller than the layer)

## Facts (P00b report, "Refusal interpretation")
- Situation "cropped-expand": full layer 1920x1080, checked-out input 960x540, and PreRender returns 960x540. With non-default blur, Mac refuses with `SmartRender:smart-generic-world-or-budget@2707`, via `DirectionalGenericWorldIsFullFrame` (`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2378`). Default (zero) blur passes.
- P02j original excerpts (`orchestra/reports/P02j-evidence/original-geometry-excerpts.txt`, worker `0x180004a20`) show that working planes derive from the input world dimensions and PreRender forwards the request. So the original likely renders this case. Measure it first: build a small original witness (e.g. layer 40x30 with checkout 20x15) on F52c.
- In AE this is likely black whenever the checkout is smaller than the layer.

## Do
- Get the original witness. Then reconstruct input-sized workspace and request handling so this checkout renders exactly. Drop the full-frame requirement only where the original has none.
- Add a realistic-v1 sampler option (opt-in) that produces checkout < layer, so the fuzzer covers this geometry for all plugins, and report which other plugins refuse or mismatch under it (report only, fix only DirectionalBlur).

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 and realistic-v2, seed 1 + a fresh seed, n100 each, and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.

## Resume note
- The first attempt was blocked on oracle capability (`orchestra/reports/P04b-directionalblur-cropped-checkout.md`). F53 adds cropped checkout (worker `~/.cache/olm-emu/worker-F53-geom/`, sampler `realistic-v2`). Use them; the sampler task in "Do" is already done by F53.

- F53 survey (`orchestra/reports/F53-oracle-cropped-checkout.md`, `F53-evidence/`) has the witnesses and per-case data for this plugin; start from them.
