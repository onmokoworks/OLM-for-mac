# N03: DistanceGradation Mac-only refusals with Bilateral blur (nightly 2026-10-25)

## Facts
- `orchestra/reports/N02-olmdistancegradation-nightly-20261025.md`: six nightly Smart refusals reproduce. They all involve the Bilateral path (`RenderBits:` admission). Two provisional admission widenings failed wider direct-original probes and were reverted. The witnesses are in `tests/fuzz_corpus/olmdistancegradation_N02/` and `orchestra/reports/nightly-20261025/witnesses/`.
- The new worker `~/.cache/olm-emu/worker-F54b/` (AEXCompat upstream, equal to F53 on all corpora) supports geometry + 4K + watches (F49 generic watches). Use it to capture the original's intermediates on these exact witnesses.

## Do
- Dump the original's Bilateral intermediates for each witness: kernel weights, range weights, per-pixel sums, and the order of the reductions. Compare them with Mac at the first differing stage, then implement the original's arithmetic in the general Bilateral path so that admission can be widened without mismatches.
- Prove it with a Bilateral-focused campaign: PF8/16/32, realistic-v1/v2 and odd-even, 3 seeds n200, with 0 mismatches and 0 Mac-only refusals.
- Then run default fuzz seed 1 n300 (no exact→non-exact), replay all corpora (record both routes), and run `ref_vs_fast`.

## Rules
- Use 1-2 processes. Change only DistanceGradation sources. Do not touch the release gate or ledger. Build workers only as described in BRIEF.md. The stop rule applies, but use the intermediate dumps before declaring a hypothesis refuted.
