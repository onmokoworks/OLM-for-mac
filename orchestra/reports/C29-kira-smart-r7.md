status: partial
summary:
- Two clusters closed separately: scalar Highlight Gaussian and Alpha box canonical-NaN seeds.
- Seed1 Smart269/0/31 →272/0/28 →274/0/26, no mismatch or previous-exact regression.
- Fresh-seed, sanitizer and corpus monotonicity checks pass for each cluster.
facts: See [scalar Highlight](C29-kira-smart-r7-scalar-highlight.md) and [Alpha NaN seed](C29-kira-smart-r7-nan-alpha.md) reports for commands, hashes, first divergences and counts.
inference: These are bounded CPU-emulation closures; remaining refusals are unproved.
changed_files: Listed in the linked cluster reports.
verify: Run each report at its cluster commit. Current seed1=274/0/26, seed18=276/0/24; final matrices562 exact; saved corpus8/8; zero sample changes away from exact.
next: Investigate the four Approximation residuals for the third cluster.
