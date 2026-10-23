status: partial
summary:
- Two clusters closed: active Alpha approximation and Gaussian Length1.
- Seed1 Smart exact254→258→260, mismatch0, refusal46→40.
- Fresh seeds, previous exact outputs, corpus monotonicity and sanitizer checks pass.
facts:
- Full measurements, hashes and commands: C22-kira-smart-r5-approximation.md and C22-kira-smart-r5-length1.md.
inference:
- Bounded CPU-emulation closures; other numeric families remain unproven.
changed_files:
- See both cluster reports for complete file lists.
verify:
- Run the length1 report commands; expect seed1 260/0/40, seed11 268/0/32, replay8/8.
next:
- Continue scalar brightness/max approximation as the third cluster.
