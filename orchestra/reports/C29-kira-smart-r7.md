status: done

summary:
- Closed three Smart clusters in separate commits: scalar Highlight Gaussian, Alpha box NaN-seed filtering, and directional Gaussian approximation.
- Seed1 n300 Smart269/0/31 →275/0/25; all269 original exact outputs and all300 Classic result objects persist.
- Fresh seeds,1144 final independent conditions,1800 sanitizer campaign renders and corpus monotonicity checks pass.
- Four ticket-new saved refusals are rebaselined to exact with history; production8/8 and the inherited T06 discrepancy set are preserved.

facts:

Base `395e5d8af90321982f0493bc052f09e671bd8368`, branch `orch/C29-kira-smart-r7`. Read AGENT_GUIDE, emulator GOTCHAS, compatibility plan, Kira ledger restrictions and prior triage/fix reports. All campaigns n300/jobs1/no shrinking, scratch and corpora ticket-local. MAIN, retained reference workers and emulator source stayed read-only. No push, stash, history rewrite, installation, release-gate edit, ledger edit or other-plugin change. No permission rejection occurred.

| Closed cluster | seed1 Smart exact/mismatch/refusal | Fresh seed before → after |
|---|---|---|
| Initial measurement |269/0/31|—|
| Scalar Highlight (`d94b33a6`) |272/0/28|seed17:264/0/36 →266/0/34|
| Alpha NaN-seed ColumnSum (`2032aa79`) |274/0/26|seed18:274/0/26 →276/0/24|
| Directional Gaussian approximation (final commit) |275/0/25|seed19:275/0/25 →276/0/24|

Final seed1 original Smart output/reject287/13; rejects are never counted exact. Classic remains48 mismatches/252 refusals with every complete result object unchanged. Ticket-new exact indices48,89,174,213,235,299. Each cluster independently checks previous-exact preservation at both seeds.

Detailed commands, input/source/worker hashes and first divergence evidence:

- [Scalar Highlight](C29-kira-smart-r7-scalar-highlight.md): missing ray4; fixed sigma-zero small kernels and singleton-axis identity. Final204 independent conditions and5 negative refusals; four all-stage exact traces. The paired trace's optional UCRT imports now match F32.
- [Alpha NaN seed](C29-kira-smart-r7-nan-alpha.md): forward warp exact, first box output diverges. Original ColumnSum resets on four-row FilterEngine calls; persistent whole-image state is refuted at a new row boundary. Final562 independent conditions and5 refusals; two all-stage exact traces. Input NaN/Inf and infinite powf seeds remain excluded.
- [Gaussian approximation](C29-kira-smart-r7-gaussian-approximation.md): first reduced-source divergence, resolved by connecting existing resize/constructor/Gaussian/compose owners. Final378 independent conditions and6 refusals; two all-stage exact traces.

Each cluster passes600 sanitized Smart campaign replays,25 existing fast tests and the compiled54-row generic sanitizer test. Counts are executions, not unique-input or whole-domain claims. No admitted mismatch or sanitizer error was observed. Refuted hypotheses supplied new intermediate boundaries; the two-refutations-without-new-boundary stop condition did not occur.

| Corpus audit | Scalar Highlight | NaN seed | Gaussian approximation |
|---|---|---|---|
| Guarded Smart70 |3 refusal→exact|1 refusal→exact|unchanged|
| Both-route sample comparisons |140|140|140|
| Changed samples |34|26|0|
| Changes away from exact |0|0|0|
| Production saved replay |8/8|8/8|8/8|

The four guarded changes are T06 indices48,59,89,235 (shrunk inputs differ from same-index campaign inputs). Final expectation updates preserve all case inputs/reductions and previous results/provenance. Full T06 saved matches:39/62 at ticket start,35/62 before migration,39/62 after migration. The four ticket updates all match; the remaining23 paths/results are exactly the inherited baseline discrepancy set. Explicit F32 and final saved-worker replay have identical complete results on62/62 cases. This is not a claim that the entire historical T06 saved corpus passes.

Identities:
- Final Mac source SHA256 `6b2e5e93f807835b82d76a27edf1e757ce9a42c0f3cd7fd467c3f209106ca8bb`.
- New Highlight helper SHA256 `6a7ecdefc638c46a609da98b56b632f45ccace25990a6a5ed7ccc0a566ef6ffb`.
- Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Default F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`.
- Machine reports: `reports/fuzz/olmkirakira_smart_C29_{scalar_highlight,nan_alpha,gaussian_approximation}.json`.

Twelve regenerable sample build trees and20 trace shared libraries were removed. Retained scratch is33MiB, below5GiB. All started emulator/build command sessions completed; no task subprocess remains. Python syntax and `git diff --check` pass.

inference:

These are bounded original-AEX CPU-emulation closures. Native AE/UCRT, arbitrary floating inputs, custom ramps, ROI/downsample and all geometries remain unproved. Seed1/index39's first divergence is invalid-op NaN sign only and is left to F38. No first divergence at a still-host math import was observed in the closed clusters. Residual family labels do not prove a shared root cause.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `core/kirakira_highlight_gaussian.h`
- `tools/emulation/{probe_kirakira_smart_C07,trace_kirakira_numeric_F09,verify_kirakira_admission_F10,rebaseline_kirakira_C29}.py`
- Three diagnostic patches under `tools/emulation/fixtures/`
- Four T06 saved corpus cases (48,59,89,235)
- Three machine evidence reports and four C29 Markdown reports

verify:

The linked cluster reports provide before/after, matrices, traces and corpus audit commands. Final quick recheck:

```sh
s="$PWD/orchestra/state/C29-kira-smart-r7/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 19; do
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/corpus$seed" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 - "$s/replay.json" <<'PYCHECK'
import json, sys
r=json.load(open(sys.argv[1]))
assert r['completed']==8 and all(x['matches_saved'] for x in r['replays'])
print('strict production saved replay8/8')
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

Expected seed1=275/0/25, seed19=276/0/24; production replay8/8;25 fast tests and1 compiled sanitizer test pass. The compiled test uses MAIN SDK headers/utilities read-only; source/harness and all generated outputs stay in this worktree. The Gaussian approximation report includes the final T06 recheck and inherited-drift assertions.

next:
- Three clusters closed; stop as requested.
- Final25 refusals include13 original rejects and12 rendered-oracle cases: approximation31/215/272; non-SDR box39/52/86; Gaussian59/62/179; nonfinite63/116/126.
- Suggested follow-up: four-component Highlight and Gaussian Highlight approximation. Retain the non-SDR/nonfinite witnesses and keep index39 with F38.
- The23 pre-existing T06 saved expectation discrepancies remain a separate migration decision; no C29 regression was hidden by that baseline issue.
