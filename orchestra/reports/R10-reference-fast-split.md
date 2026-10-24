status: partial
summary:
- DirectionalBlur reference scalar scatter, sequential rowdriver and pre-P05a rotation arithmetic restored alongside fast code.
- Native streaming differential harness and fuzz `--reference-build` switch added.
- DirectionalBlur reference Smart seed 1 n100: 100 exact; fast n300 hashes unchanged from P05a.
- All 303 retained corpus cases replay true; Universal fast bundle builds; native 200 small / 20 HD / 5 UHD: 675 exact comparisons in 567.336 seconds.
- RadialBlur scalar scatter restored; reference/fast default hashes match; repeated root-corpus oracle failure remains under investigation.
- P05c/P07a splits and final expanded harness acceptance remain.
facts:
- `git log` identified P05a implementation 4dd1406c (merge f05c36af), P05b merge 738aed52, P05c implementations ec6cc82c/5602e329/4ebcfd7d (merge c7e63a63), P07a implementation 651bc587 (merge 4a0623d2).
- `memory_pressure`: 61% free at the most recent check.
- `python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --small 8 --hd 0 --uhd 0`: 24 exact comparisons, zero mismatches/refusals.
- `python3 tools/fuzz/run.py --plugin olmdirectionalblur --reference-build --n 100 --seed 1 --jobs 1 --shrink-attempts 0 --scratch orchestra/state/R10-reference-fast-split/oracle-directional --corpus orchestra/state/R10-reference-fast-split/corpus-directional --report orchestra/state/R10-reference-fast-split/oracle-directional.json`: Smart 100 exact; Classic 100 mismatches.
- Same command without `--reference-build`, n300 and fast-prefixed paths: Smart 298 exact + 2 oracle budgets; Classic 4 exact + 296 mismatches. Both route output hashes match `orchestra/reports/P05a-evidence/default-1.json` on all 300 cases (600 hashes); reference n100 matches fast on both routes (200 hashes).
- `python3 orchestra/reports/R10-evidence/replay.py --plugin olmdirectionalblur`: 303/303 matches_saved across six corpus directories.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMDirectionalBlur --scratch orchestra/state/R10-reference-fast-split/release-directional`: x86_64 arm64 success.
- RadialBlur reference seed1 n100: Smart 85 exact, 14 oracle rejects, 1 oracle budget; fast n300: 275 exact, 20 rejects, 5 budgets. Both route hashes match P05b on all 300 cases; reference n100 matches fast.
- RadialBlur replay: 190/190 nested/realistic cases true; root 60/61 true on two runs. C49_seed1_case000117 original SMART_RENDER stops at RIP 0x180002cc3; reference candidate hash remains saved 6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d. A fast single-case control replays true with the same worker SHA and 60-second timeout.
- RadialBlur Universal fast bundle builds x86_64 arm64.
- DirectionalBlur locked P00b heavy 1080p timings PF8/PF16/PF32: 1.354/1.320/1.377 s; retained P05a final2: 1.411/1.504/1.462 s. Default PF8 0.435 vs 0.379 s; default PF16/PF32 essentially unchanged at 0.024/0.048 s.
inference:
- The measured default fast behavior is unchanged. Native equality is not new AE-exact evidence.
changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialScatterSIMD.h
- core/dblur_rowdriver.cpp
- core/dblur_rotate.cpp
- tools/fuzz/adapters/public.py
- tools/fuzz/run.py
- tools/perf/ref_vs_fast.py
- tools/perf/README.md
- orchestra/reports/R10-evidence/ (replay/archive scripts and compressed evidence)
- tools/fuzz/adapters/radialblur.py (extract native host build from oracle preparation)
- orchestra/reports/R10-reference-fast-split.md
verify:
- Commands above reproduce the completed checks; original oracle timeouts can vary.
- `python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur`: requested 200 small / 20 HD / 5 UHD; final result still pending.
- `python3 orchestra/reports/R10-evidence/replay.py --plugin olmdirectionalblur`: final result pending.
next:
- Complete native large-frame and corpus checks, other five reference implementations, release bundles and serialized P00b timing.
- DirectionalBlur now honors OLM_PARALLEL_MAX (default remains eight). Final 200-case small campaign: 600 exact comparisons under 1/2/8. Large campaign was built before this cap was added; do not claim its three runs used distinct partition counts.
