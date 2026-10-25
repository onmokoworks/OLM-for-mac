status: partial
summary:
- Blur completed; [report and timing table](P07d-evidence/blur.md).
- ColorKey completed, including locked performance and concurrent checks: [report](P07d-evidence/key.md).
- DistanceGradation has not been modified.
facts: Blur 675 native exact comparisons, 850 AEX Smart exact, 139 matching replays. ColorKey 675 native exact, 827 AEX Smart exact plus 23 AEX rejects, 44 matching replays. Both TSan50 without reports and unchanged historical unit outcomes.
inference: Independent task scheduling preserves observed bytes; Blur and ColorKey performance acceptance is complete.
changed_files: core/olmblur_parallel_parts.h; mac/OLMColorKey/OLMColorKey.cpp; tools/perf/ref_vs_fast.py; orchestra/reports/P07d-evidence/; this report.
verify: Exact commands and expected results are in the linked per-plugin reports.
next: Work on DistanceGradation next. The ticket remains partial until its independent acceptance is complete.
