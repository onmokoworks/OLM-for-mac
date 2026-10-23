# F43 double-pow diagnosis (blocked)

These are diagnostic experiments, not a double-precision implementation or a
library API. The AMD-derived candidate files are generated only in F43 scratch.
The existing F28 comparator executes the pinned UCRT DLL directly under Rosetta;
the native arm64 producer supplies deterministic inputs and Apple survey values.
The AMD candidates themselves run on x86_64. This does **not** qualify a native
arm64 replacement.

`results.json` retains actual results and source/binary identities. The first four
campaigns each use the F28 100,000,000-pair sequence, in both modes. The final two
experiments use only witness 3. Counts include NaN payload/sign differences.
No tolerance, lookup correction, or expected result is used in the candidate
arithmetic. Witness operands select diagnostic inputs only.

Experiments:

- `baseline`: unmodified pinned AMD double pow.
- `top20`: compare the top 20 bits with `TOP20_EXP_MAX` rather than the top 32.
- `scaled`: combine the scaled head and correction with FMA in the subnormal path.
- `combined`: apply both preceding changes.
- `tail-fma`: combined, plus fused accumulation of `y * log_lo` with the residual
  from `y * log_hi`.
- `horner`: combined, plus Horner evaluation of the exp polynomial, keeping the
  coefficients unchanged.

The last two hypotheses do not fix witness 3 in either mode. The ticket's stop
rule applies. No candidate was promoted. In particular, fewer mismatches is not
an equivalence result. See `orchestra/reports/F43-ucrtmath-double.md` for commands,
remaining work, and the distinction between observations and interpretations.

`--witness 1`, `2`, or `3` reproduces individual retained operands. Apple survey
comparisons are omitted in this mode because the third stream word is a dummy;
only actual UCRT/AMD comparisons are retained. Full random and `--ranges` use the
unchanged F28 native producer. The script validates the DLL hash and clean AMD
commit, uses bounded pipes and at most two mathematical processes, and checks
both process statuses and exact input count. A mismatch is recorded, not a
nonzero process exit; `check_results.py` verifies the expected **nonzero** counts.

This is OLM-internal oracle tooling. No Microsoft binary, table, or disassembly
is included. Future UCRT-derived sin/cos/exp implementations must go in
`ucrtmath/ms/`, marked OLM-internal and not publishable standalone, per F42.
