status: partial

summary:
- Two clusters closed: scalar Alpha box opacity and non-unit Strength.
- Seed1 Smart improves134/0/166→171/0/129→197/0/103; seed5 improves127/0/173→172/0/128→193/0/107.
- Each cluster preserves baseline exact outputs, passes600 sanitized campaign routes, and changes corpus samples only toward exact.
- Work continues on finite HDR/signed input admission; no claim of three-cluster completion.

facts:
- Full measured commands, hashes, first divergence and before/after tables: [Opacity cluster](C07-kira-smart-r2-opacity.md).
- Machine evidence: `reports/fuzz/olmkirakira_smart_C07_opacity.json`.
- Second-cluster commands, hashes and first divergences: [Strength cluster](C07-kira-smart-r2-strength.md), with `reports/fuzz/olmkirakira_smart_C07_strength.json`.

inference:
- The scalar Alpha box pipeline covers declared Strength/Opacity ranges on finite SDR inputs; other numerical families remain independent.

changed_files:
- See the exact lists in the two cluster reports.

verify:
- Run the commands in `C07-kira-smart-r2-strength.md`; expected seed1=197 exact/0 mismatch/103 refusal, seed5=193/0/107,600 sanitizer-clean routes and strict replay8/8.

next:
- Continue with finite HDR/signed input refusals; preserve the excluded Gaussian Length1 witness.
