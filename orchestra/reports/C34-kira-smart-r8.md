status: done

summary:
- Closed three Smart clusters in separate commits: four-component Gaussian Highlight, Gaussian Highlight approximation, and nonfinite PF32 Alpha box.
- Seed1 n300 Smart275/0/25 →282/0/18; all275 initial exact outputs and all300 Classic result objects persist.
- Fresh seeds, sanitized matrices/campaign replays and corpus monotonicity checks pass; zero admitted mismatches.
- One saved refusal is rebaselined to exact; production8/8 and the inherited23-case T06 discrepancy set are preserved.

facts:

Initial commit `67a34ff3d82f316810dd1f9df8b2648c5dc59bd2`, branch `orch/C34-kira-smart-r8`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, Kira ledger restrictions and prior triage/fix reports. All campaigns n300/jobs1/no shrinking with ticket-local scratch/corpora. MAIN, external emulator source and retained workers remained read-only. No release gate, ledger or other-plugin code changed. No push, stash, history rewrite, installation, worker rebuild or permission rejection occurred.

| Cluster | Seed1 Smart exact/mismatch/refusal | Fresh seed before → after |
|---|---|---|
| Initial measurement |275/0/25|—|
| Four-component Gaussian Highlight (`6a92db2f`) |277/0/23|seed20:280/0/20 →281/0/19|
| Gaussian Highlight approximation (`ecc0c27b`) |279/0/21|seed21:279/0/21 →280/0/20|
| Nonfinite Alpha box (final commit) |282/0/18|seed22:282/0/18 →284/0/16|

Final seed1 original Smart renders/rejects=287/13. Original rejects are never counted exact. Classic remains48 mismatches/252 refusals with all result objects unchanged. Newly exact indices31,59,62,63,116,126,215. Every cluster preserves its previous exact Smart outputs and complete Classic campaign results.

Detailed evidence, first mismatches, identities and exact reproduction commands:
- [Four-component Highlight](C34-kira-smart-r8-color-highlight.md): first seed-shape divergence; connect existing four-component constructor, separable Gaussian and area-normalized aggregation. Independent204 conditions,600 sanitized campaign Smart renders and140 sample comparisons pass.
- [Highlight approximation](C34-kira-smart-r8-highlight-approximation.md): first reduced-source divergence; connect existing resize/scaled-length/Gaussian/full-resolution compose pipeline. Independent360 conditions and600 sanitized campaign Smart renders pass.
- [Nonfinite Alpha box](C34-kira-smart-r8-nonfinite-alpha.md): new source-opacity-zero counterexample reveals MAXSS NaN clamping; a second9×1 boundary reveals direct3/5-tap RowSum. Final1312 matrix conditions,600 sanitized campaign Smart renders,1200 earlier-seed route replays and18/18 actual-AEX clamp leaf comparisons pass.

The final earlier-seed audit preserves561 prior exact Smart hashes from seeds20/21 and every previously rendered Classic hash. Additional admissions match cached F32 reference hashes. Counts describe executions, not an exhaustive-domain proof. Final fast tests26/26 and compiled54-row sanitizer test pass. All five final nonfinite paired traces bind to the public AEX output, with exact glow and post-clamp storage. Raw intermediate NaN sign/payload differences remain explicitly non-exact where original downstream clamps erase them. No tolerance comparator or final-byte patch is used.

| Corpus audit | Color Highlight | Highlight approximation | Nonfinite Alpha |
|---|---|---|---|
| Guarded Smart70 |unchanged|unchanged|1 refusal→exact|
| Both-route sample comparisons |140|140|140|
| Changed samples |0|0|0|
| Changes away from exact |0|0|0|
| Production saved replay |8/8|8/8|8/8|

T06 case116 is the single expectation update; inputs/reductions and previous results/provenance are preserved. Saved matches62-case baseline39 → pre-migration38 → final39. The final23 mismatching paths equal the initial set, and all62 final complete result objects equal the explicit F32 replay. T06 replay exits1 for inherited drift; the full historical corpus is not claimed green.

Final identities:
- Mac source SHA256 `52adf53f477672536fdee028a2610356efff28903eab52c30b74e9a594032bc0`.
- Highlight helper SHA256 `aa5bb0314f1d97c2d28278994db0370be938ab46ba49a6da0d895a26b76f6297`.
- Compose helper SHA256 `5aa9d28fd15be9e31be51eb42b9a960b654df9f24cdb4b26a5b79a7aaf6dca52`.
- Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
- Machine evidence: `reports/fuzz/olmkirakira_smart_C34_{color_highlight,highlight_approximation,nonfinite_alpha}.json`.

Twelve regenerable sample build trees and17 trace libraries were removed. Scratch is43MiB, below5GiB. All started emulator/build sessions completed; no task subprocess remains. Python syntax and `git diff --check` pass. Refuted proposals each supplied a new numerical boundary; the two-refutations-without-new-boundary stop condition did not occur.

inference:

These are bounded original-AEX CPU-emulation closures. Native AE/UCRT, arbitrary ramps and ROI/downsample remain unproved. No first divergence at a still-host math import was observed in the closed clusters, so none is labeled ucrt-math-pending. Work-budget thresholds are unchanged. Residual parameter families do not establish a common root cause.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `core/kirakira_highlight.h`, `core/kirakira_merge2.h`
- `tools/emulation/probe_kirakira_smart_C07.py`, `probe_kirakira_clamp_C34.py`, `snapshot_kirakira_C34.py`, `verify_kirakira_history_C34.py`
- `tools/emulation/olmkirakira_outer_compose_oracle_20260728.py` and its test
- `tools/emulation/rebaseline_kirakira_C29.py` (optional ticket argument)
- T06 corpus case116, three machine evidence reports and four C34 Markdown reports

verify:

Cluster reports contain full before/after, matrix, paired trace and migration commands. Header changes require the committed snapshot helper for historical builds. Final quick check:

```sh
s="$PWD/orchestra/state/C34-kira-smart-r8/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 22; do
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

Expected seed1=282/0/18, seed22=284/0/16; production replay8/8;26 fast tests and one compiled54-row sanitizer test pass. The compiled test reads MAIN SDK/utilities; worktree source/harness and ticket-local compiler outputs are used.

next:
- Three clusters closed; stop as requested.
- Remaining18 refusals include13 original rejects and5 AEX-rendered cases:39 signed luminance box;52 signed four-component box;86 HDR Max box;179 signed Alpha Gaussian;272 HDR Alpha approximation.
- Suggested follow-up: finite-HDR Max and Alpha Gaussian/approximation admission with fresh stage-bound evidence. Keep the23 inherited T06 saved-result discrepancies as a separate migration decision.
