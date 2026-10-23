status: partial
summary:
- One cluster closed: active Alpha box approximation.
- Seed1 Smart exact254→258, mismatch0, refusal46→42. Fresh seed10 exact243→252.
- Prior exact cases persist; all sample changes toward exact; sanitizer checks pass.
facts:
- Full measurements, hashes, stage boundaries and commands: [approximation report](C22-kira-smart-r5-approximation.md).
inference:
- Bounded CPU-emulation closure; other numeric families remain unproven.
changed_files:
- See the approximation report for this cluster's complete file list.
verify:
- Run the approximation report commands; expect seed1 258/0/42, seed10 252/0/48, replay8/8.
next:
- Continue the ticket toward three clusters or its stopping condition.
