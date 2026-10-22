status: done

summary:
- Final replay: all 708 cases in 11 nonempty corpora match saved results; ColorKeep is empty.
- Rebaselined 111 cases across four corpora, preserving previous result and provenance in history.
- All 708 primary/per-route oracle comparisons remained unchanged; zero forbidden transitions.
- No production plugin, release gate, forbidden-action list, MAIN asset, or emulator source changes.
- Added explicit production transition guards, grouped provenance support, audit/replay helpers and tests.

facts:
- Branch: `orch/F23-corpus-rebaseline-all`; production/base commit: `301649aee7e5395d4ebfcd99c39862d6393db375`.
- Resumed with an uncommitted rebaseline implementation and three helper/test files; no corpus edits. Reviewed, tested and completed these changes. Re-ran every corpus instead of relying on the interrupted replay.
- Read the shared guide, emulation gotchas, compatibility plan and ledger decision matrix. Reference workers used their recorded absolute paths and validated SHA-256 values; no worker or timeout overrides. No inherited `OLM_*` environment overrides were present.
- `python3 -B tools/fuzz/replay_all_F23.py before > orchestra/state/F23-corpus-rebaseline-all/before.log 2>&1`: exit 0; 597/708 saved matches, 708/708 oracle comparisons unchanged. Each replay uses `--jobs 2 --budget-minutes 30 --scratch orchestra/state/F23-corpus-rebaseline-all`; the inherited case timeout is 10 seconds. Replays run sequentially.
- `python3 -B tools/fuzz/classify_rebaseline_F23.py > orchestra/state/F23-corpus-rebaseline-all/classify.log 2>&1`: exit 0, zero forbidden transitions. Per-case route statuses, hashes, first differences and changed flags are committed in `F23-corpus-rebaseline-all-transitions.json`.
- `git log --merges --oneline d027fd4d..HEAD` inspected. No forbidden transition required bisect; no causal merge identification is claimed.
- `python3 -B tools/fuzz/apply_rebaseline_F23.py > orchestra/state/F23-corpus-rebaseline-all/rebaseline.log 2>&1`: exit 0; invokes `rebaseline_corpus.py --production-rebaseline F23-corpus-rebaseline-all` only for eligible changed corpora. Updated ColorKey 3, KiraKira diagnostic 62, ToonDilate 23, ToonDilate T13 23 cases.
- Compared all 111 modified corpus files against `git show HEAD:<path>` before committing: inputs, operations, reductions and all other fields unchanged; history retains the full old result/provenance and any prior history.
- `python3 -B tools/fuzz/replay_all_F23.py after > orchestra/state/F23-corpus-rebaseline-all/after.log 2>&1`: exit 0; 708/708 saved matches. Every nonempty child replay exited 0 with `replay_complete`. Empty ColorKeep correctly exited 2 with `setup_error`; it contains no cases to baseline.
- Final route outcomes remain visible: Classic 131 exact, 150 mismatch, 104 refusal, 323 no_write; Smart 644 exact, 33 mismatch, 31 refusal. Saved-result agreement is not universal AEX exactness.
- `python3 -B tools/fuzz/test_framework.py`: 14 tests, 13 passed, one opt-in integration skip; `python3 -B tools/fuzz/test_route_oracles.py`: 6 passed; `python3 -B tools/fuzz/test_rebaseline_production.py`: 2 tests passed (11 status/hash scenarios plus four oracle/route/report integrity scenarios). Logs are in ticket scratch. These tests used scratch TMPDIR/TMP/TEMP.
- `git diff --check`: exit 0. Scratch is 3.0 MiB after removing regenerable run directories, including the interrupted attempt's directory. All launched replay/test processes exited.

Per-corpus saved-result matches:

| Corpus | Before | Final |
| --- | ---: | ---: |
| colorkeep | 0/0 | 0/0 |
| olmblur | 39/39 | 39/39 |
| olmcolorkey | 0/3 | 3/3 |
| olmdirectionalblur | 56/56 | 56/56 |
| olmdistancegradation | 145/145 | 145/145 |
| olmkirakira | 8/8 | 8/8 |
| olmkirakira_gate_off_T06 | 0/62 | 62/62 |
| olmsmoother | 29/29 | 29/29 |
| olmsmoother2 | 8/8 | 8/8 |
| olmtoondilate | 277/300 | 300/300 |
| olmtoondilate_T13 | 0/23 | 23/23 |
| radialblur | 35/35 | 35/35 |

Changed route transitions (unchanged companion routes are included separately in the JSON audit):

| Corpus | Route | Transition | Count |
| --- | --- | --- | ---: |
| olmcolorkey | Classic | mismatch -> mismatch, changed bytes | 3 |
| olmcolorkey | Smart | mismatch -> exact | 3 |
| olmkirakira_gate_off_T06 | Classic | mismatch -> mismatch, changed bytes | 8 |
| olmkirakira_gate_off_T06 | Classic | mismatch -> refusal | 54 |
| olmkirakira_gate_off_T06 | Smart | mismatch -> exact | 21 |
| olmkirakira_gate_off_T06 | Smart | mismatch -> refusal | 13 |
| olmkirakira_gate_off_T06 | Smart | refusal -> exact | 11 |
| olmkirakira_gate_off_T06 | Smart | refusal -> refusal, metadata only | 17 |
| olmtoondilate | Smart | mismatch -> exact | 23 |
| olmtoondilate_T13 | Smart | mismatch -> exact | 23 |

First saved-result differences:
- ColorKey `seed1_case000020_32358eb88430.json`: candidate SHA `5a84100cd36b1fcd1313c825a6024399c709c61c71f092b13bd1981f7a7d9bf2` -> `5acad5ae07164031d1b7dda4ef816b83df950e40d014976545734909f6fcbfb7`. Smart becomes exact. Classic remains mismatch: first byte/word 3/0 -> 4/1; differing bytes/words 11/4 -> 10/3.
- KiraKira diagnostic `seed1_case000000_7b627ae38e84.json`: both routes change mismatch -> refusal. Previous SHA `25225c9ba28948125b422dcab05d3febddae6eab43b11e2215342852602d7d3d`, first byte/word 0/0, 259 differing bytes; refusal has no output hash.
- Both ToonDilate corpora first differ at `seed1_case000015_9b13c27c2f2e.json`: Smart mismatch -> exact, SHA `827c2540f8ee6d3cfd1b7ce67db6b6c4fab2513621f872b564d73ca294e4b0fc` -> `501461adefd891bfd5e245ed582c61337157338b79217b077d5ffb647023f3c4`. Previous first byte/word 64/16 with 41 differing bytes / 12 words. Classic no_write is unchanged.
- There were no changed exact -> exact hashes. Final saved-result first mismatch: none.

inference:
- The measured drift is eligible under this ticket's transition policy and consistent with F14's stale-baseline finding. This is not a claim that all remaining mismatch/refusal routes are correct or resolved.
- The KiraKira diagnostic corpus name records its origin; its new saved results describe current production with original experimental results retained in history.

changed_files:
- 111 JSON cases under `tests/fuzz_corpus/{olmcolorkey,olmkirakira_gate_off_T06,olmtoondilate,olmtoondilate_T13}/`.
- `tools/fuzz/rebaseline_corpus.py`, `tools/fuzz/README.md`.
- `tools/fuzz/{replay_all_F23,classify_rebaseline_F23,apply_rebaseline_F23,test_rebaseline_production}.py`.
- `orchestra/reports/F23-corpus-rebaseline-all.md`, `F23-corpus-rebaseline-all-transitions.json`, `F23-corpus-rebaseline-all-results.json` (final counts, route outcomes and source/worker/dependency provenance).

verify:
Run from this worktree with the recorded workers and MAIN assets available:

```sh
mkdir -p orchestra/state/F23-corpus-rebaseline-all
export TMPDIR="$PWD/orchestra/state/F23-corpus-rebaseline-all"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1
python3 -B tools/fuzz/test_rebaseline_production.py > "$TMPDIR/verify-policy.log" 2>&1
python3 -B tools/fuzz/test_route_oracles.py > "$TMPDIR/verify-routes.log" 2>&1
python3 -B tools/fuzz/test_framework.py > "$TMPDIR/verify-framework.log" 2>&1
python3 -B tools/fuzz/replay_all_F23.py verify > "$TMPDIR/verify.log" 2>&1
cat "$TMPDIR/verify.log"
git diff --check
```
Expected: test totals above; replay helper exit 0, 708/708 matches in the table above, empty ColorKeep explicitly reported as exit 2; diff check clean. Do not rerun the migration to verify: final replay is read-only with respect to saved corpus files.

next:
- None for F23. Remaining measured numerical mismatches/refusals require separate plugin tickets; ColorKeep has no saved fuzz corpus to replay. This work does not add cases or promote local emulator checks to native AE conformance.
