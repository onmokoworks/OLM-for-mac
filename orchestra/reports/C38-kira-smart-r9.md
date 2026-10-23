status: done

summary:
- Closed three Smart clusters in separate commits: finite brightness box, ordered color-alpha aggregation/finite color box, and finite Alpha Gaussian/approximation.
- Seed1 n300 Smart282 exact/0 mismatch/18 refusal →287 exact/0 mismatch/13 refusal.
- Every successful original Smart render in seed1 is now exact; all282 initial exact hashes and all300 Classic result objects persist.
- Fresh seeds, independent sanitized matrices, campaign/history replays and corpus audits pass; two saved refusal→exact migrations preserve23 inherited T06 discrepancies.

facts:

Initial revision `f97b0143ab0f3a2ff14d34a957587722145f66fe`, branch `orch/C38-kira-smart-r9`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, Kira ledger restrictions and prior triage/fix reports. All campaigns use n300/jobs1/no shrinking, ticket-local scratch and scratch corpora. MAIN, external emulator source and retained workers stayed read-only. No release gate, ledger, other-plugin code, installed bundle, push, stash, history rewrite, worker rebuild or permission rejection.

| Cluster | Seed1 Smart exact/mismatch/refusal | Fresh seed before → after |
|---|---|---|
| Initial remeasurement |282/0/18|—|
| Finite brightness box (`dc116dbc`) |284/0/16|seed23:280/0/20 →285/0/15|
| Ordered color alpha / finite color box (`2cca6ea7`) |285/0/15|seed24:282/0/18 →283/0/17|
| Finite Alpha Gaussian/approximation (final cluster commit) |287/0/13|seed25:289/0/11 →293/0/7|

Newly exact seed1 indices39,52,86,179,272. Every cluster preserves its previous exact Smart outputs and all Classic campaign result objects. Direct initial→final comparison confirms the282 initial exact result objects and300 Classic result objects are unchanged. Classic remains48 mismatches/252 refusals, outside this Smart ticket.

Detailed evidence, hypotheses, first-stage differences, exact reproduction commands and before/after tables:
- [Brightness](C38-kira-smart-r9-brightness.md):612 final independent exact conditions,8 negative refusals; finite scalar brightness box source admission, no renderer arithmetic change. Index39 retains explicitly classified intermediate NaN sign differences removed by the existing original clamp;86 is stage-exact.
- [Color](C38-kira-smart-r9-color.md): initial756 exact/108 mismatches →864 exact after restoring the original COMISD/JBE unordered-alpha branch;54 further boundary conditions exact,12 negative refusals,20 original aggregator leaf witnesses. First numerical branch divergence is at aggregation; earlier ray differences are NaN-only. One corrected leaf-probe ABI setup error is documented, not treated as numerical evidence.
- [Alpha](C38-kira-smart-r9-alpha.md):630 final independent exact conditions,12 negative refusals; existing Gaussian/resize paths accept finite Alpha input. Both newly admitted seed1 paired traces match every stage and bind to public AEX output.

Each cluster runs600 sanitized campaign Smart renders and70 guarded F32 corpus cases. The three both-route sample audits each compare140 rows, with0 changed samples. Final historical replay runs1200 additional sanitized routes and preserves568 earlier exact Smart hashes from seeds23/24 plus all earlier rendered Classic hashes. Additional admissions match cached original F32 hashes. Counts are execution evidence, not exhaustive-domain or native-AE claims.

| Corpus | Initial | Final |
|---|---|---|
| Production saved corpus |8/8 matches_saved|8/8|
| T06 saved matches |39/62|39/62; same23 failing paths|
| Migrated expectations |—|52 and272: refusal→exact only|

Migration preserves input/reduction fields and result/provenance history. Each migration has an explicit before/after replay table; final saved-result verification compares current files with the complete recorded replay. Full T06 replay exits1 for the inherited23 discrepancies and is not reported green.26 fast tests and the existing compiled sanitizer test pass after every cluster; final compiled test43.129s.

The13 remaining seed1 refusals are original-Smart rejections under F32, classified only:
- 11 OpenCV resize `inv_scale_x > 0` assertions:28,56,100,103,121,124,206,228,246,248,270.
- 2 IPP `IwException` throws:57,117.

Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`. Final Mac source SHA256 `9a0417738cb50f27aa9cab4383a9c8df6db91b7b6cf2683c4b0b54ce3f331a67`. Machine evidence is in `reports/fuzz/olmkirakira_smart_C38_{brightness,color,alpha}.json`.

Twelve regenerable build trees and13 trace libraries were removed. Scratch47MiB, below5GiB. All started emulator/build commands completed. Python syntax and `git diff --check` pass. No subagents were used. The refuted color admission hypothesis produced a new boundary; the two-refutations-without-new-boundary stop condition did not occur.

inference:

The requested seed1 successful-oracle residual is closed in three clusters, using general source rules and an original ordered comparison. Intermediate NaN sign/payload identity remains explicitly unimplemented where original downstream clamps erase it. No tolerance or per-case sample patch is used. Native AE/UCRT, arbitrary ramps, ROI/downsample, other source domains and larger workloads remain unproved. No still-host math first divergence was observed; no ucrt-math-pending closure is claimed. Work-budget limits are unchanged.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/probe_kirakira_color_alpha_C38.py`
- T06 fixtures `seed1_case000052_cdd504885120.json`, `seed1_case000272_cf5cfa58c159.json`
- Three C38 machine evidence reports, three cluster reports and this summary

verify:

Cluster reports contain exact before/after/matrix/trace/audit commands. Run them at the corresponding cluster commits. Final quick check:

```sh
s="$PWD/orchestra/state/C38-kira-smart-r9/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 25; do
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/corpus$seed" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 - "$s/replay.json" <<'PYCHECK'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['completed']==8 and all(x['matches_saved'] for x in r['replays'])
print('production replay8/8')
PYCHECK
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

Expected seed1=287/0/13, seed25=293/0/7, production8/8,26 fast tests and compiled sanitizer success. The compiled test reads MAIN SDK/utilities while using worktree source/harness and ticket-local compiler outputs. T06 replay deliberately retains39/62 saved matches and exits1.

next:
- Three clusters closed; stop as requested.
- Suggested next ticket: nonfinite Alpha approximation, e.g. fresh seed25/index222; trace resize/seed/filter before any promotion.
- Keep original rejection classification, the23 inherited T06 expectation discrepancies, F41b budgets and F42/F43 host math as separate follow-up work.
