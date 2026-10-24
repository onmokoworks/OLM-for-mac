status: partial
summary: |
  Added header-only GCD row helper with task cap and sequential fallback.
  Threaded KiraKira's profiled forward/reverse warp rows; arithmetic is unchanged.
  50 forced-cap comparisons and 50 TSan cases passed; full campaigns are in progress.
  Existing blur-driver migrations are deferred pending their own exact-hash validation.
facts:
  - Base commit: c101e2880a4b423e5e285c36baf120cbedd609b3.
  - P00b before matrix: 66/66 ok. After default/corpus05: 12/12 ok.
  - Default fuzz seed 1 n300: Smart exact 287; 13 AEX-and-Mac Smart refusals; 0 Smart mismatches.
  - scripts in orchestra/reports/P07a-evidence contain the exact reproducible commands.
  - threads.py: 50 cases, task caps 1/2/8 identical SHA-256; 50 TSan cases passed.
  - concurrent.py: four kernel renders in one process, 3 repeats per cap, identical output.
  - warp_bench.py: 256x256 serial 0.000412923 s vs cap8 0.000235240 s.
  - memory_pressure checks: 62%, 57%, 58% free. Scratch below 8 MiB at checkpoint.
inference: |
  Independent warp rows provide useful single-frame acceleration without splitting
  ordered reductions. No equivalence claim is made for other plugins or native AE.
changed_files:
  - core/olm_parallel.h
  - core/kirakira_warp.h
  - orchestra/reports/P07a-parallel-helper-kirakira.md
  - orchestra/reports/P07a-evidence/*
verify: |
  python3 orchestra/reports/P07a-evidence/threads.py
  Expected: 50 forced-cap cases and 50 TSan cases passed.
  python3 orchestra/reports/P07a-evidence/verify.py
  Expected: recorded Smart statuses retained; campaigns not yet all completed.
next: |
  Finish realistic-v1/v2, odd-even, corpus replay and original-header comparison;
  retain final evidence, register candidate bundle and delete regenerable builds.
