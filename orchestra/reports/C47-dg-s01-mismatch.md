status: done

summary:
- C43's already-merged general PF8 Bilateral dispatch fix also fixes the S01 witness; no further production change is needed.
- Pre-C43 replay reproduces all 2558 differences; the first observed divergent stage is the post-Bilateral float plane.
- Current captured pre/post planes and full witness output are exact. Updated only its saved result, retaining previous evidence.
- Fresh seeds 1 and 104, n300 each: zero Smart mismatches and zero previously exact case/hash losses.
- Full DG corpus: 147/147 matches saved results.

facts:

FACT: Starting HEAD `d6cd18daa05d1106718faa2594d4fe7a3b089564`, branch `orch/C47-dg-s01-mismatch`.
Production source remains SHA256 `8a13dc9d113ef735f0d11e4f6d9ce6a914621b1d508e67cb442f0eb4ce8cbd63`.
The relevant existing fix is `abdc36026c358b8a27242162915bcc462b073e79` (C43).
Reference is the prebuilt F46 worker, SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
Corpus replay independently uses each saved hash-bound worker (four groups). Original assets and Python environment were accessed in MAIN by absolute path, without modifying MAIN or rebuilding workers.

FACT: Initial `run.py --replay` of `seed104_case000207_S01.json` returns Smart exact and exit1 because the saved expectation was mismatch. Both Smart hashes are
`ce105eef699eaeadc66b5df833664962825b18db9b4991c99b60283db2863ea1`.
Classic remains its original mismatch; its output and the original AEX results are unchanged.
`rebaseline_corpus.py --production-rebaseline C47-dg-s01-mismatch` changes one entry, Smart mismatch -> exact, and preserves previous result/provenance. Input, parameters and reduction history are unchanged.

FACT: Reused `trace_distancegradation_blur_C14.py` against source from `abdc3602^` and current production, generated seed104 case207. Generated input hash equals the saved witness input hash. The pre-C43 output hash equals the saved mismatching Mac hash.
The original full-plane watch attempt exceeded the worker's 4096-byte watch limit and exited2; added an explicit PF8 prefix option instead of changing the reference worker. Each captured plane is 4096 bytes / 1024 FLOAT32 words out of 89040 bytes / 22260 words. Full public output is still compared without truncation; original PNG trace and typed public output hashes agree.

| Boundary | Pre-C43 Mac versus original AEX | Current Mac versus original AEX |
|---|---|---|
| Pre-filter prefix | 0/1024 differing words | 0/1024 differing words |
| Post-filter prefix | 310/1024 differing words; first word0, Mac `0x42ff0000`, AEX `0x42ff0001` | 0/1024 differing words |
| Full PF8 output | 2558/89040 differing bytes; first93, Mac `c4`, AEX `c5` | 0/89040 differing bytes |

FACT: Old Mac captured pre/post planes are byte-identical. Static inspection of the C43 diff shows the old PF8 Bilateral branch skipped the filter; C43 dispatches PF8 radius>1 into the existing general IPP body. This witness is radius29. The radius-one exponent cutoff change in the same commit is not used here. No arithmetic/output adjustment or new refusal was introduced in C47.

Fresh `run.py` campaigns, `--n 300 --jobs 1 --shrink-attempts 0`, default F46, timeout10s; both exit0:

| Seed | Smart exact | mismatch | refusal | budget | uncompared |
|---|---:|---:|---:|---:|---:|
| 1 | 290 | 0 | 3 | 1 | 6 |
| 104 | 290 | 0 | 3 | 0 | 7 |

FACT: Compared all generated input hashes, parameters, geometry, depth, padding and profile against C43 `fresh1.json.gz` and S01 `olmdistancegradation_seed104.json.gz`. All 290 + 287 previously exact Smart cases remain exact with unchanged raw hashes. Seed1 has no status changes; seed104 cases142/190 change refusal -> exact, case207 mismatch -> exact. Existing Classic mismatches are outside the Smart acceptance. An initial seed1 run with default shrinking was interrupted and restarted with shrinking disabled; only the completed n300 run is counted.

FACT: Full post-rebaseline corpus replay completes147/147 with `replay_matches_saved=true`, exit0. Compressed full reports and their SHA256 manifest are in `C47-evidence/`; the audit checks all previous exact hashes and the paired-stage results. The stage comparison establishes the first observed divergence at the filter boundary, not equality of every untraced intermediate.

FACT: `python3 tools/fuzz/audit_distancegradation_C47.py` exits0 with `acceptance_met=true`; `git diff --check` passes. All started render/build processes have exited. Regenerable work directories and generated campaign corpus copies were removed; retained scratch is approximately2.9MB, below5GiB. No permission rejection occurred.

inference:

INFERENCE: This S01 residual is another consequence of the omitted PF8 Bilateral dispatch closed by C43, not another original-OLM undefined-read bug. The captured exact pre-filter field, unchanged old post-filter field, restored dispatch and exact current full output support that attribution. No KNOWN_ORIGINAL_BUGS entry is indicated. Finite seeds, prefix traces and CPU emulation/fake SDK hosts do not prove all-input or native AE equivalence. Refusals, budgets and uncompared outcomes are not exact evidence.

changed_files:
- `tools/emulation/trace_distancegradation_blur_C14.py`: explicit bounded PF8 plane-prefix capture with byte-length checks and recorded capture/full sizes.
- `tools/fuzz/audit_distancegradation_C47.py`: retained evidence audit.
- `tests/fuzz_corpus/olmdistancegradation/seed104_case000207_S01.json`: measured Smart exact rebaseline with history.
- This report and `orchestra/reports/C47-evidence/`.
- No production, release gate, ledger, other-plugin or external emulator edits; no push/stash/history rewrite/subagents.

verify:

Run from the worktree root. Retained evidence audit (no emulator needed):

```sh
python3 tools/fuzz/audit_distancegradation_C47.py
git diff --check
```

Expected: `acceptance_met=true`, zero exact losses, corpus147, witness exact; diff check clean.

Independent remeasurement, sequential jobs1:

```sh
s="$PWD/orchestra/state/C47-dg-s01-mismatch/recheck"
mkdir -p "$s"
for seed in 1 104; do
  python3 tools/fuzz/run.py --plugin olmdistancegradation --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --scratch "$s/seed$seed-work" --corpus "$s/seed$seed-corpus" --report "$s/seed$seed.json" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s/corpus-work" --report "$s/corpus.json" > "$s/corpus.log" 2>&1
```

Expected: two complete300 campaigns, zero Smart mismatches, corpus147/147 matches saved. Wall-time budgets/uncompared counts can vary with contention; they must not be counted as exactness.

Paired original/current stage reproduction (the before run intentionally reports mismatches):

```sh
git show abdc3602^:mac/OLMDistanceGradation/OLMDistanceGradation.cpp > "$s/before.cpp"
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/trace_distancegradation_blur_C14.py --seed 104 --index 207 --plane-prefix-bytes 4096 --source "$s/before.cpp" --scratch "$s/trace-before-work" --report "$s/trace-before.json" > "$s/trace-before.log" 2>&1
"$py" tools/emulation/trace_distancegradation_blur_C14.py --seed 104 --index 207 --plane-prefix-bytes 4096 --scratch "$s/trace-after-work" --report "$s/trace-after.json" > "$s/trace-after.log" 2>&1
```

Expected: both exit0, prefix/full counts in the table above, identical original output hashes.

next:
- No further C47 production fix. Merge the witness rebaseline and evidence.
- Broader DG refusal/uncompared domains and native AE validation remain separate work.
