status: blocked
summary:
- HEAD default In/Out=0 PF32 refusal reproduced; production Smart branch repair makes the six initial depth/input probes exact.
- Explicit unclamped builder-default corpus added; 71/72 Smart cases exact, one existing fractional-Power/Bilateral admission exclusion retained.
- Default baseline: 290 Smart exact / 300; full regression and corpus replay are in progress.
- Automatic command review rejected an rm -rf scratch cleanup; this status is blocked as required by the worker brief.

facts:
- `memory_pressure`: 65% free before work; scratch below 5 GiB.
- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*.py'`: 140 tests, 15 failures, 59 errors before changes. Historical failures are not reported as green.
- `python3 orchestra/reports/P04a-evidence/probe.py baseline` (initial equivalent scratch script): opaque/mixed alpha at 32x24, PF8/16/32. Before: opaque Smart PF8/16 exact, PF32 refusal; mixed PF8/16 mismatch, PF32 refusal. After: all six Smart exact.
- `python3 orchestra/reports/P04a-evidence/matrix.py`: 72 explicit cases; 71 Smart exact, case59 refused at pf32-smart-profile. The original initial all-exact assertion failed; the script now explicitly retains this observed negative control. No numerical mismatch is hidden.
- Static owner 18117349a/49d compares In/Out against 3 and skips the distance producer on other values. Callback 181170e77/7a replaces source alpha with one only for Both; other values besides Outside retain source alpha. Committed static excerpts include allocation 181395230.
- The original allocated field is not explicitly initialized by this function. The retained host supplies zeroed handles; native AE allocator-state equivalence for this invalid popup branch is not established.
- Corpus records bind AEX, worker, candidate and dependency hashes, exact input bytes, parameters, and both route outcomes.

inference:
- Treating invalid In/Out as Both in field construction and ownership was incorrect. Preserve the no-producer branch and continue through existing filter/interpolation/composition, with no final-output shortcut.
- In/Out=0 is the only scalar out-of-range default in the captured builder declaration. Negative values, 4, and int32 extrema are diagnostic states; normal UI reachability is not claimed.
- Classic historical mismatches remain outside the Smart contract and are retained in the corpus.

changed_files:
- mac/OLMDistanceGradation/OLMDistanceGradation.cpp
- tools/fuzz/adapters/olmdistancegradation.py
- tests/fuzz_corpus/olmdistancegradation_P04a/*.json
- orchestra/reports/P04a-evidence/*
- orchestra/reports/P04a-distancegradation-default-pf32.md

verify:
- `python3 orchestra/reports/P04a-evidence/probe.py verified`: six Smart exact.
- `python3 orchestra/reports/P04a-evidence/matrix.py`: 71 Smart exact and one recorded refusal, no Smart numerical mismatches; writes the explicit labelled corpus.
- `python3 orchestra/reports/P04a-evidence/verify.py campaigns`: default n300 seed1; realistic n100 seeds1/10424; odd-even realistic n150 seeds2026/2027, maximum1920x1080.
- `python3 orchestra/reports/P04a-evidence/verify.py replay`: standard run.py replay for every plugin corpus group with saved flags; final counts pending.

next:
- Finish and record regression/replay results, before/after unit comparison and real bundle validation.
- Follow up separately on native AE uninitialized allocation semantics and the existing fractional-Power/vector-Bilateral exclusion.
