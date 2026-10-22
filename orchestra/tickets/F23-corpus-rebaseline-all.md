## Goal
Bring every fuzz corpus in `tests/fuzz_corpus/*` back to `matches_saved` against current production,
without hiding regressions.

## Facts
F14 (`orchestra/reports/F14-fuzz-replay-provenance-worker.md`): replay without `--worker` now uses each
file's recorded worker. 708 cases: all 708 oracle records match, but only 597 saved Mac results match.
The other 111 differ because production changed in merged fixes whose corpora were not rebaselined.

## Steps
1. Replay every plugin corpus (`--jobs 2`). For each non-matching case and route classify
   saved_status -> current_status (and hash change for exact->exact).
2. Allowed for rebaseline: anything->exact, mismatch->mismatch (new bytes), mismatch->refusal,
   refusal->refusal (metadata only). Forbidden: exact->non-exact, exact->exact with different bytes,
   refusal->mismatch. If any forbidden transition exists: do NOT rebaseline that plugin; report the
   case and bisect the merge commit that changed it (git log --merges since d027fd4d).
3. Rebaseline allowed plugins with `tools/fuzz/rebaseline_corpus.py`, keeping history.
4. Final: replay all corpora, report per plugin matches.
