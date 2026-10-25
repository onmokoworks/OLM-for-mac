status: done
summary:
- Blur: six independent pass tasks; [report and timing table](P07d-evidence/blur.md).
- ColorKey: eight classifier row ranges with private Lab caches; [report and timing table](P07d-evidence/key.md).
- DistanceGradation: independent Smart shading rows; [report and timing table](P07d-evidence/dg.md).
- All three retain sequential reference builds and pass their independent numerical, sanitizer and performance checks. Historical unit failures remain unchanged.

facts:
- `tools/perf/ref_vs_fast.py --plugin PLUGIN --jobs 1`: caps1/2/8, Blur675 exact, ColorKey675 exact, DistanceGradation669 exact plus6 matching refusals; zero native mismatches before and after each change. First mismatch: none.
- `orchestra/reports/P07d-evidence/verify.py PLUGIN LABEL`: required default/realistic-v1/realistic-v2/odd-even campaigns total2502 Smart exact and48 original-AEX rejects/unavailable cases (including5 budgets), no Smart mismatches or Mac-only refusals. All637 corpus records replay true.
- Per-plugin thread scripts: 50 forced-cap cases and50 TSan cases each, no sanitizer reports. Per-plugin concurrent scripts: 90 exact runs each, four-render elapsed times improve versus sequential at1080p.
- Unit module statuses and recorded failure/error labels are identical before/after. See [label comparison](P07d-evidence/unit-failure-label-comparison.json); this is not a claim that the historical suites pass.
- All performance/profile runs held the shared benchmark lock; numerical differential runs were not used for timing claims. Timings may be load-affected.
- Candidate bundles and the fresh DistanceGradation baseline are registered under `~/.cache/olm-emu/P07d-{blur,key,dg,dg-before}` with full hashes in per-plugin reports/cache manifests. No AEX worker was rebuilt, no release gate/ledger/MAIN edits, no push or history rewrite.
- One corrected DistanceGradation scratch-name setup error is explicitly recorded in its report. Generated builds were removed; logs/results and durable bundles are retained.

inference:
- Independent task ownership preserves measured bytes while reducing single-frame latency. No new native-AE or previously undeclared numerical profile is claimed.

changed_files:
- core/olmblur_parallel_parts.h
- mac/OLMColorKey/OLMColorKey.cpp
- mac/OLMDistanceGradation/OLMDistanceGradation.cpp
- tools/perf/ref_vs_fast.py
- orchestra/reports/P07d-evidence/ and this report

verify:
Exact recheck commands and expected results are in each linked report. Run them serially with `OLM_TEST_JOBS=1`; build/fuzz limits and the shared timing lock remain required. The standard driver now selects caps1/2/8 for all three plugins.

next:
- Orchestrator review/merge. No required ticket work remains. Historical unit evidence/assets and mixed-alpha DistanceGradation field profiling are separate follow-ups.
