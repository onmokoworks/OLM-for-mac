status: done
summary:
- Closed three clusters: finite scalar Gaussian, finite color Gaussian, and finite scalar approximation with original unordered comparison behavior.
- Seed1 remains287/0/13; seed106 improves283/0/17 to286/0/14, matching every successful original Smart render.
- Fresh seed107 improves288/0/12 to289/0/11; final-cluster S01 history improves1159/41 to1162/38 with all prior exact hashes preserved.
- Independent matrices, negative guards, sanitized campaign/corpus/history replay, saved corpus and existing tests pass.

facts:

Base f3da6fe1f89f0742a0c57d2c7a41399128c62c14; branch orch/C55-kira-smart-r2. Read AGENT_GUIDE, compatibility plan, Kira ledger restrictions, emulator GOTCHAS and prior plugin reports. Used MAIN AEX/venvs and the retained cache worker by absolute path. No MAIN, release gate, forbidden-action list, other-plugin, external emulator/worker, installed bundle or corpus-expectation edit. No push, stash, history rewrite, worker rebuild, subagent or permission rejection. All long work logged under this ticket; scratch remained below60MiB. Regenerable builds/libraries removed and started commands completed.

|Stage|Seed1 Smart E/M/R|Seed106 Smart E/M/R|Fresh seed107|
|---|---|---|---|
|Initial measurement|287/0/13|283/0/17|not measured|
|Scalar Gaussian,82661ef7|287/0/13|284/0/16|not measured|
|Color Gaussian,44f3b1b6|287/0/13|286/0/14|288/0/12 before final cluster|
|Scalar approximation,final|287/0/13|286/0/14|289/0/11|

All campaigns n300/jobs1/no shrinking, ticket-local scratch/corpus. Initial seed1/106 original successful Smart/reject287/13 and286/14; fresh107291/9. The final seed1/106 residuals are entirely original rejections, not claimed exact. Fresh107 retains two successful-oracle nonfinite-source refusals12/20 plus nine original rejections.

Cluster details and complete reproducible evidence:
- C55-kira-smart-r2-scalar.md:612 gate-off and612 production exact,8 negative refusals,600 sanitized campaign renders. New admission106/248. Its public-bound trace retains raw NaN-sign differences, with exact glow/composition/output.
- C55-kira-smart-r2-color.md:918 gate-off and918 production exact,12 negative refusals,600 sanitized campaign renders. New admissions106/122 and123, both public-bound/all-stage exact. The diagnostic wrapper lacked the established process-attach/CRT initialization switches; correcting those restores trace binding. Unbound diagnostic failures are retained and never treated as port discrepancies.
- C55-kira-smart-r2-approx.md:initial864 matrix788 exact/76 mismatch; original fade unordered branch recovers854/10; original nested max comparison order/selection recovers864/0. Additional108 boundaries pass. Final production972 exact,8 negative refusals,900 sanitized campaign renders. Source/ray NaN signs remain explicit in extreme traces; glow/composition/final output are exact. Historical102/20 and55 traces are all-stage exact. Fresh107/10 improves to exact.

Every cluster preserves every previously exact Smart campaign result and every Classic result object. Final-cluster preservation counts861 Smart and900 Classic. Direct initial-to-final comparison also preserves all570 initial exact Smart and600 initial Classic objects for seeds1/106. No admitted mismatches.

Corpus before/after table at each cluster: production8 unchanged; historical T06 62 unchanged. Final both-route140 sample comparisons have zero changed samples. No rebaseline. Saved production replay8/8 passes with its retained worker binding. Historical S01 source-override replay executes1200 cases at each side under ASan/UBSan against archived F46 hashes:1159 exact/41 refusal →1162/38; all1159 exact hashes preserved, new exact102/20,102/55,103/26. This is cached-oracle replay, not new AEX rendering. Final26 fast tests and compiled54-row sanitizer test pass (one unittest46.042s). Python syntax, patch fixture reconstruction and git diff --check pass.

Final source SHA256 ac0f133785090baf85bca2b2df78979e2a268b7c43f676857822d77ea20be40d. Original AEX60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7. F46 worker6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903. Full compressed JSON, uncompressed SHA256 manifests, test logs and relevant original disassembly are under orchestra/reports/C55-kira-smart-r2/.

inference:

These bounded admission rules and general original comparison semantics reduce Smart residuals without tolerance or output-byte corrections. Extreme finite resizing can create NaNs, making original unordered control flow relevant to finite-source support. Both rejected numerical hypotheses produced new measured boundaries; the two-refutations-without-new-boundary stop condition did not occur. No new original-OLM undefined-memory bug was established. Native AE, arbitrary layouts/ramps and remaining unsupported source domains remain unproved.

changed_files:
- mac/OLMKiraKira/OLMKiraKira.cpp
- tools/emulation/probe_kirakira_filtered_C50.py
- tools/emulation/verify_kirakira_history_C50.py
- tools/emulation/fixtures/kirakira_unordered_fade_C55.patch
- tools/emulation/fixtures/kirakira_unordered_scalar_C55.patch
- Three cluster reports, this ticket report and C55-kira-smart-r2 evidence directory.

verify:

Cluster reports provide exact before/after campaigns, matrices, negative checks, paired traces, historical/corpus audits and expected counts. Final campaign smoke (287/0/13,286/0/14,289/0/11) and existing tests:

```sh
s="$PWD/orchestra/state/C55-kira-smart-r2/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 106 107; do
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/corpus$seed" > "$s/seed$seed.log" 2>&1
done
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
- Suggested follow-up: nonfinite scalar/color box-source admission, starting fresh seed107/index12 (Max) and20 (color), using gate-off/paired-stage evidence before promotion.
- Keep original rejections and native-host boundaries separate from successfully rendered compatibility.
