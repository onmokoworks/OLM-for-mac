status: done
summary:
- Closed three Smart clusters in separate commits: nonfinite Alpha Gaussian, finite color approximation/IPP resize edges, and nonfinite Alpha approximation.
- Seed105 improves282/0/18 →285/0/15; all285 successfully rendered AEX Smart cases are exact.
- Seed1 stays287/0/13; fresh seed106 improves282/0/18 →283/0/17. No admitted mismatch or regression of an initially exact output.
- Sanitizer matrices/campaigns/history, corpus comparisons,26 existing tests and compiled sanitizer checks pass.

facts:

Base `d6cd18daa05d1106718faa2594d4fe7a3b089564`, branch `orch/C50-kira-smart-r1`. Read AGENT_GUIDE, compatibility plan, Kira ledger restrictions, GOTCHAS and plugin triage/fix/S01 reports. Used MAIN assets and retained F46 worker by absolute path without modifying them. No worker rebuild, release-gate/ledger/other-plugin edit, push, stash, history rewrite, native install or subagent. No permission rejection. All scratch stayed in this ticket, below5GiB; regenerable build/trace-library outputs were removed and all started commands finished.

| Cluster | Seed1 Smart E/M/R | Seed105 | Fresh seed106 |
|---|---|---|---|
| Initial remeasurement |287/0/13|282/0/18|282/0/18|
| Alpha Gaussian (`00338f78`) |287/0/13|283/0/17|282/0/18|
| Color approximation / IPP edges (`31eeda2e`) |287/0/13|285/0/15|282/0/18|
| Alpha approximation (final commit) |287/0/13|285/0/15|283/0/17|

Every row is a completed n300/jobs1/no-shrinking campaign with scratch corpus. All851 initial exact Smart result objects and all900 initial Classic result objects persist. New admissions are seed105 indices179/199/285 and seed106 index88. Seed1's13 and seed105's15 remaining refusals lack successful original Smart output. Seed106 retains14 original rejections plus3 successful-oracle refusals122/123/248, not counted as exact.

Detailed commands, source/AEX/worker hashes, before/after tables and committed evidence:
- [Gaussian](C50-kira-smart-r1-gaussian.md):512 gate-off and512 production exact,5 negative refusals. General existing Gaussian Alpha admission; arithmetic unchanged.
- [Color](C50-kira-smart-r1-color.md): initial369 exact/63 mismatch. A public-bound trace locates the meaningful finite/NaN divergence at enlarged glow, after exact reduced glow (an earlier raw source NaN-sign difference is retained explicitly). Original IPP border dispatch evaluates one varying axis; the port evaluated both. Recover the general operation, yielding486 independent exact/12 negative refusals. Corrected signed trace40 is all-stage exact; trace5's final output is exact with documented internal differences. F46 trace imports were brought current.
- [Alpha approximation](C50-kira-smart-r1-alpha.md):1152 gate-off and1152 production exact,20 negative refusals; existing box/Gaussian approximation source admission only.

Each cluster runs900 sanitized Smart campaign renders and70 guarded corpus comparisons. Corpus table at every stage: production8 unchanged, T06 62 unchanged, no expectation migrations. Color's additional both-route140 sample audit has0 changed samples. Saved production replay passes8/8 after each cluster; historical T06 saved expectations were not rebaselined or claimed current. Each cluster passes26 fast tests and the compiled54-row sanitizer test. Final S01 history replay runs1200 further sanitized Smart routes against archived F46 hashes, preserving1156 prior exact cases and admitting103/82 and104/120 exactly (1158 exact/42 refusal). These are measured execution counts, not exhaustive or native-AE claims.

Only the broad finite color-approximation admission hypothesis was refuted; it yielded a new public-bound resize boundary and a successful general fix. The two-refutations-without-new-boundary stop condition did not occur. No new original undefined-memory bug or deterministic-semantics substitution was needed.

Final Mac source SHA256 `098ab80805c4083e9b0c7f98c99b9549f3139d7f184f1466cb3bd3bf9c9af0f8`; AEX `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; F46 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. Compressed reports and uncompressed hash manifests are under `orchestra/reports/C50-kira-smart-r1/`. Python syntax and final diff whitespace checks pass. The patch fixture's context-prefix whitespace warning was repaired without changing its reconstructed candidate bytes.

inference:

These bounded source rules and the original IPP edge operation reduce the measured Smart residual without sample patches or tolerance. Native AE, arbitrary ramps/ROI/downsample and remaining finite Gaussian domains remain unproved. Original rejection is a reference boundary, not an exact result.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/probe_kirakira_filtered_C50.py`
- `tools/emulation/verify_kirakira_history_C50.py`
- `tools/emulation/fixtures/kirakira_resize_edges_C50.patch`
- Three cluster reports, this ticket report and committed evidence directory. No corpus files changed.

verify:

Cluster reports give exact matrix/trace/before-after/corpus/history reproduction commands. Final quick check (expected counts in final table; saved replay8/8;26 fast tests and compiled sanitizer success):

```sh
s="$PWD/orchestra/state/C50-kira-smart-r1/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 105 106; do
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/corpus$seed" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
mkdir -p "$s/bin"
ln -sf "$PWD/tools/ucrt_cxx.py" "$s/bin/clang++"
PATH="$s/bin:$PATH" PYTHONPATH=tests python3 - <<'PYTEST' > "$s/compiled-sanitizer.log" 2>&1
import unittest
from pathlib import Path
import test_olmkirakira_generic_beta_sanitizers_20260820 as t
t.ROOT=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t))
raise SystemExit(not r.wasSuccessful())
PYTEST
git diff --check
```

next:
- Three clusters closed; stop here.
- Follow-up: finite scalar/color Gaussian source domains at seed106 indices122/123/248; S01 also retains scalar approximation witnesses. Use gate-off/first-stage evidence before promotion.
- Keep original OpenCV/IPP rejection and native-host behavior separate from successful-render compatibility.
