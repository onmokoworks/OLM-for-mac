status: done

summary:
- Closed three Smart clusters separately: scalar Gaussian, four-component Gaussian, and four-component box approximation.
- Seed1 n300 Smart263/0/37 → 269/0/31; all263 base-exact result objects persist.
- Fresh-seed validation, sanitizer checks and corpus monotonicity pass; strict saved replay8/8.
- Stop at the requested three clusters; residual31 includes13 original rejects and18 successful-oracle refusals.

facts:

Base `1ccc9cd494617dde93a1b9eb3882de0c2aa9d25c`; branch `orch/C28-kira-smart-r6`. Read the shared guide, compatibility plan, emulator gotchas, Kira restrictions and previous triage/fix reports. All campaigns use n300/jobs1/no shrinking/ticket-local scratch and corpus. MAIN, original assets and retained worker are read-only; no reference rebuild, push, stash, installation, release-gate edit, ledger edit or other-plugin change.

| Cluster | Seed1 exact/mismatch/refusal | Fresh seed before → after |
|---|---|---|
| Initial remeasurement |263/0/37|—|
| Scalar directional Gaussian (`d7fb906c`) |264/0/36|seed14:262/0/38 → 264/0/36|
| Four-component directional Gaussian (`37e21ddf`) |266/0/34|seed15:261/0/39 → 263/0/37|
| Four-component box approximation (this commit) |269/0/31|seed16:258/0/42 → 264/0/36|

Seed13 additionally stays255/0/45, but contained no newly eligible scalar Gaussian tuple; seed14 provides the positive fresh-domain check. Final seed1 original Smart output/reject is287/13; seed16 is275/25. Original rejects are never counted as exact. All original263 exact Smart result objects and all300 Classic result objects are unchanged at the final source. Classic remains48 mismatches/252 refusals against its separate original route.

Detailed first-stage evidence, source bindings, commands and expected results:

- [Scalar Gaussian](C28-kira-smart-r6-scalar-gaussian.md): Max case12 has a one-word seed difference hidden by exact final output. Connect the already recovered FLOAT32 scalar constructor to the Gaussian owner; final648 independent conditions exact,7 negative refusals. Both final paired traces are public-bound/all stages exact.
- [Color Gaussian](C28-kira-smart-r6-color-gaussian.md): case77 first has a scalar-versus-four-component seed shape mismatch. The unit-normalizer hypothesis reaches exact rays but diverges at glow word3. Original normalizer8 proves Length remains the separate aggregation divisor. Final396 independent conditions exact,7 refusals; both final traces exact.
- [Color approximation](C28-kira-smart-r6-color-approximation.md): case214 first differs in reduced source. Connecting resize/seed/rays exposes a glow divergence if raw UI lengths are retained. Original normalizers204,5,6,23,9 bind to scaled helper lengths and Highlight area. Final828 independent conditions exact,18 refusals; four final traces exact, including Mode2/Highlight500.

Each cluster independently verifies previous exact preservation, sanitized campaign replay and both corpus routes. Total final independent matrix executions1872; sanitized campaign renders2100 (including seed13). These are execution counts, not unique-input or whole-domain claims. Every cluster passes25 existing fast tests and the compiled54-row generic sanitizer test; final compiled test44.865s. No sanitizer error or admitted mismatch was observed.

| Corpus audit | Scalar Gaussian | Color Gaussian | Color approximation |
|---|---|---|---|
| Production8 |unchanged|unchanged|unchanged|
| Guarded diagnostic62 |unchanged|unchanged|61 unchanged;214 refusal→exact|
| Changed samples, both diagnostic routes |0|0|310, all toward exact|
| Changes away from exact |0|0|0|
| Strict production saved replay |8/8|8/8|8/8|

Each sample audit checks140 route replays. The310 changed samples are155 per route in the historical shrunk214 input, whose former155 mismatches per route become0. Saved production expectations need no rebaseline; historical diagnostic expectations remain historical observations. Input/oracle provenance is not rewritten. Both failed diagnostic patches reconstruct their source bytes exactly. Each refuted hypothesis supplied a new intermediate boundary; the two-refutations-without-new-boundary stopping condition did not occur.

Identities:
- Final Mac source SHA256 `e149e56aac5b36f8325913dcdb852b92b8a275ed674110e74b76f4893f2c749c`.
- Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained Kira worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; absolute path in each machine report. The replay tool's preliminary default-worker log does not override the saved corpus's hash-bound Kira worker.
- Machine reports: `reports/fuzz/olmkirakira_smart_C28_{scalar_gaussian,color_gaussian,color_approximation}.json`.

Twelve regenerable sample build trees were removed; retained scratch is approximately41.6MB, below5GiB. All started command sessions completed; logs and diagnostic evidence remain. No permission rejection occurred.

inference:

These are bounded CPU-emulation closures. The math import scaffold is unchanged; native AE/UCRT, arbitrary floating inputs, custom ramps and ROI/downsample remain unproved. Remaining parameter-family groups are not yet proved shared root causes.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/fixtures/kirakira_gaussian_color_unit_normalizer_C28.patch`
- `tools/emulation/fixtures/kirakira_color_approx_raw_normalizer_C28.patch`
- `reports/fuzz/olmkirakira_smart_C28_{scalar_gaussian,color_gaussian,color_approximation}.json`
- `orchestra/reports/C28-kira-smart-r6{,-scalar-gaussian,-color-gaussian,-color-approximation}.md`

verify:

The linked cluster reports contain exact before/after, independent matrix, trace, sanitizer campaign and sample-audit commands. Quick final recheck (sequential):

```sh
s="$PWD/orchestra/state/C28-kira-smart-r6/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 16; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/corpus-$seed" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 - "$s/replay.json" <<'PYCHECK'
import json, sys
r=json.load(open(sys.argv[1]))
assert r['completed']==8 and len(r['replays'])==8
assert all(row['matches_saved'] for row in r['replays'])
print('strict saved replay 8/8')
PYCHECK
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
PYTHONPATH=tests python3 - <<'PYTEST' > "$s/compiled-sanitizer.log" 2>&1
import unittest
from pathlib import Path
import test_olmkirakira_generic_beta_sanitizers_20260820 as t
t.ROOT=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t))
raise SystemExit(not r.wasSuccessful())
PYTEST
git diff --check
```

Expected seed1=269/0/31, seed16=264/0/36; strict replay8/8;25 fast tests and1 compiled sanitizer test pass. The compiled test uses only MAIN SDK headers/utilities; source/harness stay in the worktree.

next:
- Three clusters closed; stop as requested.
- Residual31 =13 original rejects +18 successful-oracle refusals: Gaussian6, approximation4, non-SDR box5, nonfinite3. Every residual row is retained in the final machine report.
- Suggested next ticket: Gaussian Highlight scalar/four-component owners and Gaussian approximation; retain non-SDR/nonfinite boundaries. Route any first divergence inside a UCRT math import to F30.
