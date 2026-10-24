status: done
summary:
- Restored ColorKey Smart local-coordinate reads and input-sized neighborhood staging with output-sized classification.
- Realistic seed 1: 91 exact, 0 mismatches/refusals, 9 unavailable; fresh seed 20261024: 89 exact, 0 mismatches/refusals, 11 unavailable.
- Default seed 1/n300 stays 300 exact; all 11 pre-existing corpus cases now Smart exact; Classic results unchanged in all 511 comparisons.
- Added eight labelled realistic regressions; ASan/UBSan replay is 8/8 exact and matches saved results.
- Unit tests retain the same 23 passed, 38 failed, 4 errors; historical failures are listed in evidence.

facts:

Starting commit: `ad12dc148133d5551e7b14cf32d465d3db2fb000`, branch
`orch/P02i-colorkey-geometry`. Read AGENT_GUIDE, the ColorKey ledger decision
row, compatibility plan, emulator GOTCHAS, T15 report/evidence, P02h/P02d reports and F52c geometry
host code. No oracle rebuild, MAIN write, installed-bundle change, release-gate
edit, ledger edit, other-plugin edit, or Classic behavior change.

AEX SHA256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
F52c worker SHA256: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
Candidate SHA256: `c2ad72f8fc141e8293661f7196102957c889c8168eaf32c0a24c594bc6e45217`.
Full source/host identities: [after-provenance.json](P02i-evidence/after-provenance.json).

### Original addressing and staging

Read MAIN's `decomp/OLMColorKey.aex.c.txt`, functions `0x180009000`,
`0x1800094b0`, `0x180009960`, `0x1800085b0`, `0x1800113c0` and `0x1800117c0`.
The typed workers allocate three temporary worlds using **input** width/height;
the classifier receives the **output** extent. Thin/distance/blur operate on the
input-sized planes. The pixel address helpers compute data + y*rowbytes +
x*pixelbytes, without world origin correction. The non-origin Iterate suite
callback supplies source/destination pixels at those local coordinates.
F52c negotiates output bounds, assigns the result origin, and sets its local
extent to `[0,0,output_width,output_height]`.

`disassemble.py` independently reads the original PE bytes. Retained
[disassembly](P02i-evidence/original-disassembly.txt) confirms input dimensions
at `0x180009581/9585`, `95a4/95a8`, `95c6/95ca`, output extent at `95db`, and
the local-address helpers. Static-source hashes are in `summary.json`. The retained F52c Iterate source
was also checked: its batching differs from MAIN, but its local source/destination
address calculation is identical.

Implementation: Smart normalizes only its private world descriptors, copies
the input, allocates full input-sized output staging, and limits initial matte
classification to the negotiated output dimensions. The existing distance and
writer arithmetic then executes on the input-sized plane. Commit copies active
output rows at local `(0,0)` and preserves destination padding. Existing checkin
before commit/exception behavior is retained. Parameter admission remains in
place; input extent/aspect/origin do not add Mac-only geometry restrictions.
Classic retains its previous path and default arguments.

### Measurements

Commands actually run: `python3 orchestra/reports/P02i-evidence/measure.py before`
and `... measure.py after`, serially with `OLM_TEST_JOBS=1`, TMPDIR inside this
ticket, F52c, ten-second case timeouts. Each ran both routes over all 11 existing
corpus files recursively, realistic seeds 1/20261024 n100, and default seed 1
n300. Raw per-case results are [before.jsonl](P02i-evidence/before.jsonl) and
[after.jsonl](P02i-evidence/after.jsonl); counts and unit failure lists are in
[summary.json](P02i-evidence/summary.json).

| Smart set | Before E/M/R/U | After E/M/R/U |
|---|---:|---:|
| realistic seed 1, n100 | 50/18/23/9 | 91/0/0/9 |
| realistic seed 20261024, n100 | 48/25/16/11 | 89/0/0/11 |
| default seed 1, n300 | 300/0/0/0 | 300/0/0/0 |
| existing corpora, 11 | 9/1/1/0 | 11/0/0/0 |

U is classified by the oracle first. All 20 U cases reject because **the original
render corrupts an output pixel guard**, identically before/after. They are
excluded from numerical acceptance, not counted as Mac exact. The candidate
returns successfully in all 200 realistic cases. There are no timing exclusions.
All default result objects and all 511 Classic route result objects are identical
before/after, including their historical Classic mismatches/refusals.

The reduced T15 pixels witness originally differs first at byte 0 (`ff` original,
`00` Mac), with 10 differing bytes; now Smart exact. The T15 PF16 refusal
originally returns Mac 516 while the original succeeds; now Smart exact. The
original T15 saved expectations remain untouched. `witnesses.py` saves their
fixed expectations plus one refusal and one mismatch witness at each depth in
`tests/fuzz_corpus/olmcolorkey/P02i-realistic/` (8 cases). Standard replay with
ASan/UBSan reports `replay_matches_saved: true`, 8/8 Smart exact; both route
results match saved expectations. See [sanitized-replay.json](P02i-evidence/sanitized-replay.json).

Unit command: ticket-local venv Python `-m pytest -q tests/test_olmcolorkey*.py`.
Before: **38 failed, 23 passed, 4 errors, 1 subtest passed** (13.20 s).
After: **38 failed, 23 passed, 4 errors, 1 subtest passed** (12.99 s).
Failure/error node sets are identical and listed individually in `summary.json`.
Examples: absent untracked handoff/report assets and SDK paths, obsolete
ParamsSetup source parser, stale source hashes, and old hostless mock missing
`distance_step_x/y` (including the historical generic ROI test). No existing
unit expectation was rewritten. Initial collection failed for missing pytest,
Pillow and pefile; a ticket-local venv with pytest/pillow/numpy/unicorn/capstone/
pefile resolved collection before the reported runs. `git diff --check` passes.

inference:

- Output-origin translation and output-sized neighborhoods were independent
  causes of Smart geometry differences. Restoring the original staging removes
  the observed mismatch/refusal classes without changing numerical kernels.
- The original raw blur writer iterates input dimensions even for a smaller
  destination; this is consistent with the 20 original guard corruptions.
  Private full-size staging avoids reproducing memory corruption. Numerical
  equivalence is claimed only where the oracle produces valid guarded output.
- These measurements meet the ticket's bounded acceptance. Native AE host
  Iterate semantics and arbitrary geometry/settings beyond these seeds remain
  broader compatibility work, not established by emulator conformance. The
  negotiated host clips outputs to input bounds; outputs larger than the input
  retain a bounds guard and are outside this measured domain.

changed_files:
- `mac/OLMColorKey/OLMColorKey.cpp`
- `tests/fuzz_corpus/olmcolorkey/P02i-realistic/*.json` (8)
- `orchestra/reports/P02i-evidence/`: measurement/witness/disassembly scripts,
  before/after results and provenance, summary, disassembly and sanitizer replay
- `orchestra/reports/P02i-colorkey-geometry.md`

verify:

From this worktree, serially (no changes to MAIN required):

```sh
export TMPDIR="$PWD/orchestra/state/P02i-colorkey-geometry"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P02i-evidence/measure.py verify > "$TMPDIR/verify.log" 2>&1
OLM_COLOR_TRIAGE_SANITIZE=1 ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 \
UBSAN_OPTIONS=halt_on_error=1 python3 tools/fuzz/run.py \
  --plugin olmcolorkey --geometry realistic --jobs 1 \
  --replay tests/fuzz_corpus/olmcolorkey/P02i-realistic \
  --scratch "$TMPDIR/verify-replay" --report "$TMPDIR/verify-replay.json" \
  > "$TMPDIR/verify-replay.log" 2>&1
# With pytest, pillow, numpy, unicorn, capstone, pefile installed in a local venv:
"$TMPDIR/venv/bin/python" -m pytest -q tests/test_olmcolorkey*.py \
  > "$TMPDIR/verify-unit.log" 2>&1
git diff --check
```

Expected: verify campaign now includes 19 corpus files (the original 11 + new 8),
all Smart exact; realistic 91/89 exact and 9/11 original guard failures; default
300 exact. Sanitized replay matches all 8 saved cases. Units retain the failure
set above in this worktree environment. `measure.py before` was run at the
starting source; rerunning that label on the changed source is not a baseline.
Scripts generate evidence under `P02i-evidence`; logs and builds stay ticket-local.

next:
- No remaining P02i acceptance item. Follow-up: native AE ROI/Iterate verification
  and explicit original guard-corruption ownership; do not hide those U cases.
- Repair stale historical ColorKey unit harnesses/assets in a separate ticket,
  including the old Smart ROI expectation that assumes translated source reads.
