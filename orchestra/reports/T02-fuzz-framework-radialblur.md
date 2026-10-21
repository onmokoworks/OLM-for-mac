status: done

summary:
- Added a reusable seeded public-path differential fuzzer, RadialBlur adapter, bounded shrinker, corpus replay, and tests.
- Final 500-case run: 35 pixel-mismatch cases in 19 cheap signature clusters; these are not 19 proven causes.
- All 35 counterexamples reduced, 28 to smaller geometry; all 35 saved cases replayed exactly.
- AEX: 462 successful renders, 32 rejects, 6 time budgets. Mac refusals remain separate from pixel differences.
- No production plugin, release gate, ledger, MAIN, or installed bundle changes.

facts:
- Branch: `orch/T02-fuzz-framework-radialblur`; base commit `59ea6f441d622c005c1340adc5d0a30d0f78f5d6`.
- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, RadialBlur ledger matches, and `docs/COMPATIBILITY_ANALYSIS_PLAN_JA.md`.
- Ran `python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 --budget-minutes 30`, redirecting output to `orchestra/state/T02-fuzz-framework-radialblur/campaign.log`.
  Result: `complete`, 500 cases in 63.4841 seconds, zero framework errors. Classic: 62 exact / 24 mismatch / 413 refusal / 1 uncompared. Smart: 74 exact / 35 mismatch / 390 refusal / 1 uncompared. Both routes exact: 62. The 35 mismatch cases form 19 signatures after bounded reduction.
- Depth counts: PF8 153, PF16 180, PF32 167. Profiles: SDR 447, HDR 30, signed 15, nonfinite 8. HDR/signed/nonfinite profiles occur only in PF32. Generator tests verify legal ranges, 1x1, single rows/columns, dimensions above 200, odd padding and reproducibility.
- First original mismatch: seed 1, index 6, PF8, 33x61; Classic and Smart each differ in 2 bytes. First byte offset 5785: AEX `2c`, Mac `2b`. Saved reduced case: `tests/fuzz_corpus/radialblur/seed1_case000006_253d4390d90b.json`.
- Corpus: 35 JSON files, 320246 bytes total, largest 14577 bytes. All 35 accepted reductions preserve the originally mismatching routes; 28 reduce geometry. Reductions are bounded, not globally minimal.
- Largest signatures each contain four cases: PF16 Inner Strength (slot 10), PF16 Outer Strength (slot 4), and PF8 Outer Offset (slot 6). Every signature has stage `raw-output`; the selected paired public harness exposes no corresponding intermediate stages.
- Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Retained worker: `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`; SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Six retained public calibration outputs match (Zoom/Rotation x three depths). This is a newer worker, not the October 1 controlled worker hash.
- Production source SHA-256: `344f79b0e1064839d26ad5df341aa664ae513e05a9934b5c06405b6b8eb89cc0`.
- Committed campaign report SHA-256: `59dbf9fdfba7ce4878e94cf0e98324ad38fe32e728be408581846514eb0998a9`. Its framework hashes match the final Python files.
- Ran `python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 2 --report orchestra/state/T02-fuzz-framework-radialblur/replay-all.json` (output redirected to `replay-all.log` in scratch). Result: 35/35 saved results reproduce, including raw hashes/statuses, in 7.328 seconds.
- Ran `OLM_FUZZ_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/orchestra/state/T02-fuzz-framework-radialblur" python3 tools/fuzz/test_framework.py` (output redirected to `tests.log` in scratch). Result: eight tests pass in 8.571 seconds, including real repeated public replay and shrinking.
- Ran `python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 --budget-minutes 0.1 --report orchestra/state/T02-fuzz-framework-radialblur/budget.json --corpus orchestra/state/T02-fuzz-framework-radialblur/budget-corpus` (output redirected to `budget.log` in scratch). Result: `budget_exhausted`, 18 attempted cases retained, 6.0095 seconds including shutdown/reporting. AEX and Mac budget results are separate.
- During integration, repeated worker sessions initially rejected shrink attempts because an exclusive `fixture-input-world.bin` sidecar already existed. The adapter now gives every AEX replay a fresh disposable directory, following the existing public helper. The final campaign above was rerun after the correction.
- The adapter clears inherited RadialBlur debug/force-scalar environment variables; a regression test checks that diagnostic behavior cannot silently replace the production path.
- Scratch stayed below 5 GiB; disposable build outputs/worlds are removed automatically. No writes to `/tmp`, no push, no history rewrite.

inference:
- The 35 cases establish a measured residual for this seed, distribution, production revision and hash-bound emulation worker. Signature clustering suggests follow-up groups, not independent root causes.
- Host math differences may contribute to residuals. Six calibration matches do not prove arbitrary Windows UCRT equivalence, nor does the fake SDK host prove native AE behavior.
- Mac refusal counts are a separate compatibility boundary. PF_Err alone does not distinguish internal work-budget refusal from unsupported controls; the fuzzer does not invent that attribution.
- AEX session worlds are packed; only Mac worlds receive random odd byte strides. Noise Layer is None, including when the Layer popup is selected. Independent selected-layer worlds, native AE, ROI/downsample and full parameter/input coverage remain outside this first adapter.
- Wall-time refusals and shrink progress can vary under machine load. Earlier development runs had different timeout counts; the committed report is the final run above.

changed_files:
- `tools/fuzz/run.py`
- `tools/fuzz/core.py`
- `tools/fuzz/adapters/__init__.py`
- `tools/fuzz/adapters/radialblur.py`
- `tools/fuzz/test_framework.py`
- `tools/fuzz/README.md`
- `reports/fuzz/radialblur_20261021.json`
- `tests/fuzz_corpus/radialblur/*.json` (35 counterexamples)
- `orchestra/reports/T02-fuzz-framework-radialblur.md`

verify:
```sh
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 2 --report orchestra/state/T02-fuzz-framework-radialblur/verify-replay.json
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 --budget-minutes 30 --report orchestra/state/T02-fuzz-framework-radialblur/verify-500.json --corpus orchestra/state/T02-fuzz-framework-radialblur/verify-corpus
```
Expected on the recorded worker/source: eight tests pass; corpus replay exits 0 with 35/35 `matches_saved`; campaign completes 500 with zero framework errors. Recorded residual is 35 mismatches / 19 signatures; wall timeout/reduction counts may vary. Use `--worker` or `OLM_AEX_WORKER` if the retained binary is relocated; preserve its recorded hash for an equivalent reference.

next:
- Classify the minimized offset/strength/fade cases against the retained controlled-math worker and paired intermediate traces before assigning production causes.
- Follow-up adapters can add independent Noise Layer worlds and AEX odd-stride hosting; the current report explicitly bounds those gaps.
- Re-run the same seed and saved corpus after T01 or future plugin fixes; changed expected hashes should be reviewed as new evidence, not patched into production.
