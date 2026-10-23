status: partial
summary:
- Two clusters closed: finite scalar and color Gaussian source admission.
- Seed1 stays287/0/13; seed106 improves283/0/17 to286/0/14.
- Independent matrices, negative guards, sanitizer campaign/corpus replays and existing tests pass.
facts:
- Exact commands, hashes, before/after tables and trace evidence are in C55-kira-smart-r2-scalar.md and C55-kira-smart-r2-color.md.
- Color trace-wrapper initialization was corrected; case122/123 now bind to public F46 and are all-stage exact.
- Scalar approximation remains unpromoted: initial864 matrix gives788 exact/76 mismatches; cause investigation continues.
inference:
- The two finite Gaussian admission domains are supported within existing tuple restrictions; approximation needs a numerical fix.
changed_files:
- mac/OLMKiraKira/OLMKiraKira.cpp
- tools/emulation/probe_kirakira_filtered_C50.py
- Cluster reports and evidence under orchestra/reports/C55-kira-smart-r2/.
verify:
- Run exact commands in the two cluster reports, with their recorded expected results.
next:
- Continue scalar approximation investigation and validation.
