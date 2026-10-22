status: partial

summary:
- First cluster closed: scalar Alpha box-mode opacity materialization and Smart admission.
- Seed1 Smart improves134/0/166→171/0/129; fresh seed5 improves127/0/173→172/0/128.
- Baseline exact outputs preserved,600 sanitized campaign routes pass, corpus changes only toward exact.
- Work continues on non-unit Alpha Strength; no claim of three-cluster completion.

facts:
- Full measured commands, hashes, first divergence and before/after tables: [Opacity cluster](C07-kira-smart-r2-opacity.md).
- Machine evidence: `reports/fuzz/olmkirakira_smart_C07_opacity.json`.

inference:
- The measured opacity correction closes one bounded scalar branch; remaining numerical families are independent.

changed_files:
- See the exact list in `C07-kira-smart-r2-opacity.md`.

verify:
- Run the commands in `C07-kira-smart-r2-opacity.md`; expected seed1=171 exact/0 mismatch/129 refusal, seed5=172/0/128,600 sanitizer-clean routes and strict replay8/8.

next:
- Continue the ticket loop with non-unit Alpha Strength and preserve the excluded Gaussian Length1 witness.
