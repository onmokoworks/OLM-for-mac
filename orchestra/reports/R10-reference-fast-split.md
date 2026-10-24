status: partial
summary:
- DirectionalBlur reference scalar scatter, sequential rowdriver and pre-P05a rotation arithmetic restored alongside fast code.
- Native streaming differential harness and fuzz `--reference-build` switch added.
- DirectionalBlur reference Smart seed 1 n100: 100 exact; fast n300 hashes unchanged from P05a.
- Full-size native checks and corpus replay in progress; other plugin splits and release/performance acceptance remain.
facts:
- `git log` identified P05a implementation 4dd1406c (merge f05c36af), P05b merge 738aed52, P05c implementations ec6cc82c/5602e329/4ebcfd7d (merge c7e63a63), P07a implementation 651bc587 (merge 4a0623d2).
- `memory_pressure`: 61% free at the most recent check.
- `python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --small 8 --hd 0 --uhd 0`: 24 exact comparisons, zero mismatches/refusals.
- `python3 tools/fuzz/run.py --plugin olmdirectionalblur --reference-build --n 100 --seed 1 --jobs 1 --shrink-attempts 0 --scratch orchestra/state/R10-reference-fast-split/oracle-directional --corpus orchestra/state/R10-reference-fast-split/corpus-directional --report orchestra/state/R10-reference-fast-split/oracle-directional.json`: Smart 100 exact; Classic 100 mismatches.
- Same command without `--reference-build`, n300 and fast-prefixed paths: Smart 298 exact + 2 oracle budgets; Classic 4 exact + 296 mismatches. Both route output hashes match `orchestra/reports/P05a-evidence/default-1.json` on all 300 cases (600 hashes); reference n100 matches fast on both routes (200 hashes).
inference:
- The measured default fast behavior is unchanged. Native equality is not new AE-exact evidence.
changed_files:
- core/dblur_rowdriver.cpp
- core/dblur_rotate.cpp
- tools/fuzz/adapters/public.py
- tools/fuzz/run.py
- tools/perf/ref_vs_fast.py
- tools/perf/README.md
- orchestra/reports/R10-evidence/replay.py
- orchestra/reports/R10-reference-fast-split.md
verify:
- Commands above reproduce the completed checks; original oracle timeouts can vary.
- `python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur`: requested 200 small / 20 HD / 5 UHD; final result still pending.
- `python3 orchestra/reports/R10-evidence/replay.py --plugin olmdirectionalblur`: final result pending.
next:
- Complete native large-frame and corpus checks, other five reference implementations, release bundles and serialized P00b timing.
- DirectionalBlur's original fast row partitions currently ignore OLM_PARALLEL_MAX; running with 1/2/8 does not yet exercise distinct partition counts. Do not claim that thread-limit acceptance is complete.
