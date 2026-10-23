status: partial
summary:
- Closed nonfinite Alpha Gaussian admission; seed105 improves282/0/18 →283/0/17.
- Seed1 remains287/0/13; fresh seed106 remains282/0/18; no prior exact output changes.
- Color approximation and nonfinite Alpha approximation are still under investigation.
facts:
- See `C50-kira-smart-r1-gaussian.md` and its committed machine evidence for commands, hashes, counts and sanitizer/corpus results.
inference:
- The remaining seed1 refusals are original rejections, not successful-reference mismatches.
changed_files:
- Gaussian source predicate, independent matrix tool, reports and evidence described in the cluster report.
verify:
- Run the exact reproduction commands in `C50-kira-smart-r1-gaussian.md`; expected seed1 287/0/13, seed105 283/0/17, seed106 282/0/18.
next:
- Continue the two remaining clusters within this ticket.
