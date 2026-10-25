# N02-olmcolorkey-nightly-20261025: fix olmcolorkey mismatches / Mac-only refusals found by the 2026-10-25 overnight fuzz

## Facts
- The overnight run (`tools/fuzz/nightly.sh --hours 7`, about 670k observations across 10 plugins) retained reduced witnesses in `orchestra/reports/nightly-20261025/witnesses/`, and the table is in `summary.txt`. Take the ones for **olmcolorkey**: their `plugin` field, or the file names listed in summary.txt.
- M = admitted mismatch; R = Mac refusal where the original renders (black in AE).

## Do
- Replay each olmcolorkey witness with standard `tools/fuzz/run.py --replay` and the matching sampler flags. Each must reproduce; if one does not, report it.
- For each distinct signature: find the cause from the disassembly/decomp and the paired intermediates (follow the earlier tickets for this plugin: P02/P03/P04/C01), and fix it in the general path. Keep the R10 reference/fast split, and keep the earlier fixes intact.
- If the original behaviour on a case is undefined (it reads memory it never set), document it in `notes/KNOWN_ORIGINAL_BUGS.md` the same way P06a did, instead of fixing it.

## Acceptance
- Every witness is exact, or is documented as an original bug.
- For each sampler that showed a failure, run 3 fresh seeds n200 (with the same sampler flags): 0 mismatches and 0 Mac-only refusals.
- Default fuzz seed 1 n300 shows no exact→non-exact.
- All corpora replay true (add the witnesses as a labelled set; **record both routes**).
- `tools/perf/ref_vs_fast.py --plugin olmcolorkey` is clean.

## Rules
- Use 1-2 processes. Change only olmcolorkey sources and its plugin-only helpers. Do not touch the release gate or ledger. Build AEXCompat workers only as described in BRIEF.md. The stop rule applies.
