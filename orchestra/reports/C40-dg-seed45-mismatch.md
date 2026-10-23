status: blocked

summary:
- Mandatory fallback B implemented: Smart PF8 Bilateral Size0 refuses fields with half-integer pre-filter byte-quantization ties.
- No pixel arithmetic changes or case/coordinate lookup. Only the requested corpus witness is rebaselined mismatch -> refusal.
- Full 146-case corpus replay matches all saved results after that rebaseline.
- The requested zero-loss / zero-Smart-mismatch campaign acceptance is not achieved; this is a blocked verification result, not conformance closure.

facts:
- Starting HEAD `1ff606b05ea8cf1599442ede1d717ddc29425088`; baseline source held unchanged through baseline builds. Original worker F45, SHA256 `8849565128e4147bb39b145bf392e20da1983c476498ca4448001ea278a38409`.
- Read AGENT_GUIDE, emulation GOTCHAS, compatibility plan and the DistanceGradation ledger row. No release gate, ledger, other plugin, MAIN or emulator edits; no push/stash/history rewriting/subagents.
- C39's two rejected numerical candidates are inherited evidence, not rerun or accepted fixes. No third numerical candidate was attempted.
- Additional inspection of committed C39 paired planes: only original post-filter words 106/107/123/124 change from FLOAT32 `00805443` (212.5) to `01805443` (212.50001525878906). Original pre-filter half-tie levels are 42.5, 127.5, 212.5. These four words explain the four final byte differences. The original first divergence remains the earlier pre-filter staging.
- Initial conservative admission probe refuses the witness and five previously exact generated cases (seed1 indices4/9/146; seed44 index275; seed45 index245). A scratch-only exclusion of the symmetric midpoint still loses an exact case; it is not retained. Stopped admission refinements rather than selecting a predicate around known case identities.
- Initial full corpus replay: completed146; only `seed45_case000002_C39.json` changes. After rebaselining only that witness, replay: completed146, requested146, `replay_matches_saved=true`, three recorded-worker groups.
- Seed44 baseline also reproduces case70, PF8 Bilateral Size7, 16x21: eight differing bytes, first232, original `39`, Mac `38`. This separate larger-radius mismatch is outside the Size0 admission boundary; it was also recorded by C39.


Campaign results (300 generated cases per seed, original AEX sampled once per route; current candidate compared to those retained route hashes):

| Seed | Baseline Smart exact | Candidate Smart exact | Smart mismatch | Smart refusal | Smart uncompared | Exact -> refusal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 290 | 287 | 0 | 6 | 7 | 3 |
| 44 | 276 | 276 | 1 | 10 | 13 | 1 |
| 45 | 279 | 278 | 0 | 13 | 9 | 1 |
| 46 | 280 | 280 | 0 | 13 | 7 | 0 |

- Completed all1200 candidate cases. Acceptance is explicitly false: five Smart exact cases became refusals, and the independent seed44 case70 mismatch remains. No previously exact Classic case was lost. Smart mismatch count falls from2 to1.
- Mac budget-to-result transitions are timing observations, not numerical improvements. They do not offset the five listed admission losses. Original-AEX Smart outcomes across the four baseline campaigns: 1146 ok, 45 reject, 9 budget. Uncompared rows are not exact evidence.
- Candidate source SHA256 `2f43e023e3e2894b6ed36bcaa819b59254a576a1fa05968925a756cbeab1f3a9`. `git diff --check` and Python AST parsing pass; all compiler/probe/replay/verification processes exited. No permission rejection occurred. Scratch remains below5GiB; regenerable probe builds and generated corpus copies were deleted.

inference:
- Half-integer field values are exact discontinuities of byte quantization; a filter's last-bit change can cross them. The guard is derived from the field reaching the known divergent stage, not geometry, seed, colors or output-byte comparisons.
- The guard is narrower than rejecting all PF8 Bilateral Size0: it admits fields without half ties. It is a conservative restriction of the unresolved domain, not proof of general Bilateral correctness or a proof that this is the mathematically minimal refusal set. In Both mode it conservatively watches either pre-merge field.
- Neither the numerical implementation nor a zero-exact-loss admission predicate is established. The mandatory witness refusal is achieved, but the full ticket verification remains blocked.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/verify_distancegradation_C40.py`
- `tests/fuzz_corpus/olmdistancegradation/seed45_case000002_C39.json`
- This report and `orchestra/reports/C40-evidence/` evidence.

verify:
From this worktree, replay the current candidate against the committed original-AEX campaign hashes (no emulator needed for this step):
```sh
s="$PWD/orchestra/state/C40-dg-seed45-mismatch"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/verify_distancegradation_C40.py --baseline-dir orchestra/reports/C40-evidence --scratch "$s/recheck" --report "$s/recheck.json" > "$s/recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --budget-minutes 90 --scratch "$s/replay-recheck" --report "$s/replay-recheck.json" > "$s/replay-recheck.log" 2>&1
git diff --check
```
Expected: both commands exit0 on completed observation; cached verification explicitly reports `acceptance_met=false` (it is not a release gate), and corpus replay reports completed146 / `replay_matches_saved=true`.

To independently reacquire the original-AEX comparisons rather than use retained hashes:
```sh
for seed in 1 44 45 46; do
  python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --budget-minutes 90 --scratch "$s/fresh-$seed" --corpus "$s/fresh-corpus-$seed" --report "$s/fresh-$seed.json" > "$s/fresh-$seed.log" 2>&1
done
```
Expected persistent numerical residual: seed44 case70 remains a Smart mismatch. Seed45 case2 is refused. AEX and Mac wall-budget counts can vary with shared-machine load. No zero-mismatch expectation is claimed.

Baseline acquisition used exactly the latter loop with `baseline` path prefixes before source edits. All four provenance records bind the original source SHA256 `0faa2fb61d5e0e6b0c083164a6f100b92bf3e7b12114131a6ac0f894cfcedb90`. Candidate verification regenerates all 1200 inputs and checks input hashes, geometry, depth, parameters, padding and profile before using each original AEX route's output hash. The verifier allows 60s for Mac calls versus the baseline runner's 10s; budget-to-result transitions are reported separately from exact losses.

The corpus campaign used a scratch copy of the identical candidate body with absolute include paths so baseline builds could remain unchanged. The final production build was independently replayed with `--replay tests/fuzz_corpus/olmdistancegradation/seed45_case000002_C39.json`, giving `replay_matches_saved=true`. Compressed complete reports retain source/worker hashes and all per-case outcomes.

Rejected admission variant reproduction: copy the final production source under `$s`, replace the condition `staging_half_tie && value - floorf(value) == 0.5f` with `staging_half_tie && value != 255.0f * 0.5f && value - floorf(value) == 0.5f`, then pass that copy as `--source` to the verification script. This variant still refuses the previously exact seed1 case146 and is not production code.

next:
- Recover the actual Bilateral accumulation at the retained pre/post boundary, then remove the refusal without losing exact cases.
- Track seed44 case70's Size7 residual separately; do not treat witness refusal as universal Bilateral closure.
