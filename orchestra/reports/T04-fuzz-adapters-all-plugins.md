status: partial

summary:
- Added typed public-path adapters and measured 3/9 requested 300-case seed-1 campaigns so far.
- Original AEX Smart via the retained worker; production Mac Classic and Smart via existing public replay hosts.
- Raw comparisons, bounded shrinking, separate refusal/budget/error counters, and a 2,000,000-byte corpus cap.
- No production plugin, release gate, ledger, MAIN, emulator source, or installed bundle changes.

facts:
- Read AGENT_GUIDE.md, emulation GOTCHAS, the per-plugin decision-matrix rows, and COMPATIBILITY_ANALYSIS_PLAN_JA.md.
- `/Users/onmk/.cache/olm-emu/INDEX.json` is absent. Used the existing T02 fallback `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`; no emulator rebuild.
- Captured original PARAMS_SETUP with `python3 tools/fuzz/capture_declarations.py --plugin NAME --aex-name BASENAME --scratch orchestra/state/T04-fuzz-adapters-all-plugins`. Committed snapshots bind the original AEX and worker. Each successful session checks live builder ranges/types/defaults against its snapshot.
- Campaign commands below were run with `--report reports/fuzz/NAME_20261021.json` and default corpus destination, output redirected to scratch/NAME.log. Replay commands used scratch/NAME-replay.json and scratch/NAME-replay.log.

| plugin | AEX ok/reject/budget | Classic exact/mismatch/refusal | Smart exact/mismatch/refusal | clusters | worker SHA-256 |
|---|---|---|---|---|---|
| olmdirectionalblur | 298/0/2 | 115/56/128 | 115/56/128 | 18 | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| olmcolorkey | 300/0/0 | 256/3/41 | 256/3/41 | 2 | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| olmsmoother2 | 300/0/0 | 0/0/300 | 292/8/0 | 4 | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| olmkirakira | pending | pending | pending | — | — |
| olmblur | pending | pending | pending | — | — |
| colorkeep | pending | pending | pending | — | — |
| olmdistancegradation | pending | pending | pending | — | — |
| olmsmoother | pending | pending | pending | — | — |
| olmtoondilate | pending | pending | pending | — | — |

- `olmdirectionalblur`: `complete`, 300/300 cases, 30.89 s; corpus 56 files / 376132 bytes. Full counters: `{"aex_budget": 2, "aex_ok": 298, "both_routes_exact": 115, "classic_exact": 115, "classic_mismatch": 56, "classic_refusal": 128, "classic_uncompared": 1, "pixel_mismatch_cases": 56, "smart_exact": 115, "smart_mismatch": 56, "smart_refusal": 128, "smart_uncompared": 1}`. Campaign SHA-256 `24ca2fc461491bef2ea01ebee0a0af6138c2a8bd4b047f8409abec1d797c1ef6`; AEX `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
  First mismatch: seed 1, index 0, PF8, [21, 19], classic: `{"actual_bytes": 1596, "actual_word_hex": "50", "different_bytes": 34, "different_words": 34, "expected_bytes": 1596, "expected_word_hex": "54", "first_byte": 24, "first_word": 24}`.
  Corpus replay: 56/56 match saved statuses and raw hashes; replay_complete.
- `olmcolorkey`: `complete`, 300/300 cases, 9.0629 s; corpus 3 files / 76619 bytes. Full counters: `{"aex_ok": 300, "both_routes_exact": 256, "classic_exact": 256, "classic_mismatch": 3, "classic_refusal": 41, "pixel_mismatch_cases": 3, "smart_exact": 256, "smart_mismatch": 3, "smart_refusal": 41}`. Campaign SHA-256 `aecda1de554621452af602ec7071c3883bd5b8a3ce3d44ec49295d2c7344b8bb`; AEX `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
  First mismatch: seed 1, index 20, PF32, [10, 22], classic: `{"actual_bytes": 3520, "actual_word_hex": "00000080", "different_bytes": 21, "different_words": 21, "expected_bytes": 3520, "expected_word_hex": "00000000", "first_byte": 3, "first_word": 0}`.
  Corpus replay: 3/3 match saved statuses and raw hashes; replay_complete.
- `olmsmoother2`: `complete`, 300/300 cases, 7.2078 s; corpus 8 files / 63493 bytes. Full counters: `{"aex_ok": 300, "both_routes_exact": 0, "classic_refusal": 300, "pixel_mismatch_cases": 8, "smart_exact": 292, "smart_mismatch": 8}`. Campaign SHA-256 `6c03a88446fc0b99e1fd48107c8b7346a381ce5bb9b654944ca39dd453dca220`; AEX `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
  First mismatch: seed 1, index 17, PF32, [19, 158], smart: `{"actual_bytes": 48032, "actual_word_hex": "0000c07f", "different_bytes": 158, "different_words": 155, "expected_bytes": 48032, "expected_word_hex": "0000c0ff", "first_byte": 419, "first_word": 104}`.
  Corpus replay: 8/8 match saved statuses and raw hashes; replay_complete.

inference:
- These are finite CPU-emulation residuals, not native AE or Windows UCRT equivalence. Signature clusters are not proven causes; no numerical production changes were attempted.
- Refusals are public PF_Err results; their internal budget/unsupported-control cause is not inferred. A successful Mac render with a rejected/timed-out oracle is uncompared.
- The sampler uses sparse/dense changes over recovered builder bounds, small/degenerate and occasional large geometry, PF8/PF16 SDR and PF32 SDR/HDR/signed/nonfinite pixels. Angles are a legal +/-720-degree subset. Selected layer worlds and native UI/ROI/downsample are outside these first adapters.
- Only final raw outputs are paired by the reused public hosts. No first internal numerical stage is claimed. Shrinking preserves the initially mismatching routes, is bounded, and does not prove minimality.
- Wall-clock budgets and shrink progress can vary under load. Corpus omission at the byte cap is explicitly recorded; mismatch rows and clusters remain in the campaign report.

changed_files:
- tools/fuzz/adapters/public.py and per-plugin adapter modules
- tools/fuzz/declarations/*.json and tools/fuzz/capture_declarations.py
- tools/fuzz/run.py (bounded corpus retention)
- reports/fuzz/*_20261021.json for the plugins above
- tests/fuzz_corpus/<plugin>/*.json
- orchestra/reports/T04-fuzz-adapters-all-plugins.md

verify:
```sh
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmdirectionalblur-verify.json --corpus orchestra/state/T04-fuzz-adapters-all-plugins/olmdirectionalblur-verify-corpus
python3 tools/fuzz/run.py --plugin olmdirectionalblur --replay tests/fuzz_corpus/olmdirectionalblur --budget-minutes 5 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmdirectionalblur-verify-replay.json
python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed 1 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmcolorkey-verify.json --corpus orchestra/state/T04-fuzz-adapters-all-plugins/olmcolorkey-verify-corpus
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --budget-minutes 5 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmcolorkey-verify-replay.json
python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmsmoother2-verify.json --corpus orchestra/state/T04-fuzz-adapters-all-plugins/olmsmoother2-verify-corpus
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --budget-minutes 5 --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/olmsmoother2-verify-replay.json
```
Expected: campaigns complete 300 cases with zero framework errors; retained corpus replay matches saved raw hashes/statuses. Keep the recorded worker/source hashes for comparable measurements. Read full counters for uncompared/error cells in addition to the compact summary table.

next:
- Continue in ticket order: olmkirakira, olmblur, colorkeep, olmdistancegradation, olmsmoother, olmtoondilate.
