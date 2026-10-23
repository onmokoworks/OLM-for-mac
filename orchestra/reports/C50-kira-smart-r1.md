status: partial
summary:
- Closed Alpha Gaussian and color approximation clusters; seed105 improves282/0/18 →285/0/15.
- Seed1 remains287/0/13; fresh seed106 remains282/0/18; no prior exact output changes.
- Nonfinite Alpha approximation remains under investigation.
facts:
- See `C50-kira-smart-r1-gaussian.md`, `C50-kira-smart-r1-color.md` and their committed machine evidence for commands, hashes, counts and sanitizer/corpus results.
inference:
- The remaining seed1 refusals are original rejections, not successful-reference mismatches.
changed_files:
- Source admission and IPP resize-edge correction, matrix/trace tools, reports and evidence described in the cluster reports.
verify:
- Run the exact reproduction commands in `C50-kira-smart-r1-gaussian.md`; expected seed1 287/0/13, seed105 285/0/15, seed106 282/0/18.
next:
- Continue the remaining Alpha approximation cluster within this ticket.
