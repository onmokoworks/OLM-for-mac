status: blocked
summary:
- All five T15b refusals plus DistanceGradation seed909/index16 are now Smart byte-exact.
- Four realistic campaigns:1155 exact,0 mismatch,0 refusal,45 unavailable; all2400 default candidate hash/error pairs are unchanged.
- Strict corpus replay matches1300/1301 records; the retained oracle repeatedly fails on the pre-existing RadialBlur C49 case117.
- That case's candidate still matches its saved successful original hash; its expectation and oracle remain unchanged.
- Framework tests pass; historical plugin unit failure/error names remain unchanged before/after.

facts:

Base `e3384af7`, branch `orch/P03b-nonfinite-hdr-admission`. Read AGENT_GUIDE,
GOTCHAS, the four plugin ledger decision rows, compatibility plan, T15b and
P03a reports. All commands used this worktree's
`orchestra/state/P03b-nonfinite-hdr-admission` for scratch and `TMPDIR`.
Runs used jobs1, with at most two simultaneous emulator/build processes.

The default campaigns use the retained F46 worker, SHA256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
Geometry witnesses and realistic campaigns use retained F52c, SHA256
`4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
Corpus replay honors each corpus's original hash-bound worker. Original AEX,
candidate, and source hashes are preserved in every probe's provenance.

### Original operations and implementation

**DirectionalBlur.** Decoding the original `180001ec0` rotation and
`180001000` prepass confirms `UCOMISS; JP` routes unordered alpha into the
nonzero arithmetic branch (`1800020fc`, `18000103b`). `1800015c1` uses
`MAXSS(destination, contribution)`; PF32 writeback at `180006c21/2c/34`
uses `MINSS(gain * RGB, 1)`, selecting 1 for unordered input. Coordinate
`CVTTSS2SI` conversions remain controlled by finite geometry; the neutral
source lanes do not become indices. The existing core already preserves SSE
operand order, generated-invalid NaN sign, and these comparisons. Only Smart
neutral admission now accepts nonfinite input.

An initial diagnostic that removed the finite check for both owners made Smart
exact but exposed a Classic mismatch: 17/20 words, first byte14, original word
`00000000`, candidate `0000803f`. The production change preserves the Classic
finite-input check. This is an owner boundary, not a tolerated mismatch or a
per-pixel correction. `directional-admission-olmdirectionalblur.json.gz` retains
that rejected all-owner experiment; `final-olmdirectionalblur.json.gz` records
the final Smart exact / Classic refusal behavior.

**DistanceGradation.** Original `1811749a0` scales alpha by255 through
`18117c580` before thresholding the byte mask above1. The new direct conversion
probe runs that original OpenCV body without numerical detours. Across51
samples at widths1/7/17, infinities/NaNs and positive int32 overflow become
byte0; finite threshold neighbors retain the nearest-even boundary. Reached
instructions include scalar `1811e404c CVTSS2SI` and vector
`1811e400e/4012 CVTPS2DQ`. These are rounding conversions, not CVTT truncation.
The existing mask predicate agrees on all51 ownership decisions.

The finite mask feeds the existing radius-one Bilateral implementation even
for public radius0. Source RGB enters the later composition, not the filter.
The original callback `181170f8b MULSS XMM6,XMM2` and foreground multiplication
preserve generated-invalid sign; C19's existing helper already implements it.
The patch admits nonfinite source to the existing radius-one Bilateral tuple.
For finite HDR Box/Gaussian, admission uses the same locally normalized Power
copy already used for scalar Bilateral/unblurred Power. Rendering keeps the
actual exponent and UCRT operation. No field/filter/Power/writer arithmetic is
changed. Existing nonfinite Gaussian and other unproven tuples stay refused.

Seed909/index16 is the same finite HDR Gaussian + fractional Power family
(Power2.5597627148580075, Gaussian size11). Its input SHA256 is
`e8b1cde4bf99609a74bb0b8dfcaa1823492d403f125011c426b1ccb3ef41be43`.
The baseline and candidate used identical input despite the first probe's
larger adapter size ceiling; the committed probe explicitly restores the
default256 ceiling for this case. Smart output is now
`23203f7c6e984044b9b6f8538091d0a2bce989ec6583446115f38a6fa306f90a`,
equal to the original.

**KiraKira.** Original clamp `181156740` compares against1, uses `CMOVAE`,
then `18115676a MAXSS(value,+0)`. NaN therefore becomes positive zero,
positive infinity becomes1, negative infinity becomes0. Thirteen direct
original-function samples, including signaling/quiet NaNs, confirm these raw
results. The recovered color box aggregation/composition already clamps at
these boundaries; PF32 writes floats, so no new float-to-int rule is needed.
Admission expands only the existing full-resolution/approximated color box
tuples. Gaussian/scalar source checks and all parameter/world checks remain.
No internal-filter NaN-payload equality is claimed from final-output equality.

**RadialBlur.** Original `18000817c` zeroes XMM6; `1800081d0 COMISS zero,alpha`
and `1800081d3 SETB` include unordered alpha in the component mask.
Thirteen direct instruction samples confirm the predicate `!(alpha <= 0)`:
NaN/+infinity are visible, -infinity and signed zero are not. Replacing the
finite rejection and ordered `alpha > 0` with that predicate restores general
component labeling. Existing later SSE arithmetic is unchanged.

Static excerpts are in `*-static.txt`. Direct results are in `leaves.json`
and `dg-conversion.json`. No numerical oracle detours were added.

### Witnesses and independent boundary checks

`python3 orchestra/reports/P03b-evidence/probe.py --label final` builds the four
current production hosts and compares both public owners against the original.
All six Smart results are exact; all Classic expectations are preserved.
Full output hashes and rectangles are in `final-*.json.gz`. In particular the
DirectionalBlur original/candidate hash is
`5e90ce8ddd97f4d587f99dbaff6b28eb5e9904a69c652a3dc3757b71681e3f77`.

`directional_matrix.py` tests36 independently selected lane/value cases:
36 exact. `matrix.py PLUGIN` tests each ARGB lane with signed zeros, infinities,
quiet/signaling NaNs, HDR/signed finite values, and finite extrema. KiraKira
44/44 and RadialBlur44/44 are exact. DistanceGradation has67 exact and21
retained refusals across88 cases, zero admitted mismatch; the negative controls
cover still-excluded Gaussian nonfinite/alpha-overflow inputs. These refusal
controls are distinct from the ticket's six corrected witnesses.

### Regression verification

The exact commands used for every default before/after campaign were:

```sh
python3 tools/fuzz/run.py --plugin NAME --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/SHORT-default-PHASE" --corpus "$TMPDIR/SHORT-corpus-PHASE" --report "$TMPDIR/SHORT-default-PHASE.json"
python3 orchestra/reports/P03b-evidence/sweep.py NAME
python3 orchestra/reports/P03b-evidence/replay.py NAME
```

All stdout/stderr was redirected to corresponding scratch logs. DirectionalBlur
replays were initially invoked directly through `run.py`; their three command
variants are reproduced by `replay.py`. The sweep runs realistic-v1 plus
odd-even-v1, seeds2026/2027, n150 each, maximum1920x1080 (KiraKira1080x1080).

Measured Smart realistic E/M/R/U counts:

| Plugin | Exact | Mismatch | Refusal | Unavailable |
| --- | ---: | ---: | ---: | ---: |
| DirectionalBlur | 296 | 0 | 0 | 4 |
| DistanceGradation | 294 | 0 | 0 | 6 |
| KiraKira | 298 | 0 | 0 | 2 |
| RadialBlur | 267 | 0 | 0 | 33 |

Default before/after Smart exact counts are respectively298/298,290/290,
287/287,276/276. Across all four plugins, **2,400 candidate route hash/error
pairs are unchanged**, including every previously exact output. DirectionalBlur,
DistanceGradation and KiraKira also preserve every route status. RadialBlur has
an oracle-availability swap: index62 goes uncompared→exact; index280 goes
exact→uncompared because its original worker reaches the10-second timeout.
Neither candidate hash changes. A separate bounded recheck leaves both original
calls unavailable, while again preserving both candidate hashes. Those rechecks
are not counted exact. All raw campaign results and the availability recheck
are retained; no timeout budget was extended.

Strict whole-result corpus replay:

| Plugin | Corpus groups | Matching records |
| --- | --- | ---: |
| DirectionalBlur | default83 + P02j200 + T15b4 | 287/287 |
| DistanceGradation | default147 + P02b226 + T15b9 | 382/382 |
| KiraKira | default8 + T06 62 + other reductions41 + P02c272 + T15b4 | 387/387 |
| RadialBlur | default61 + P02d180 + T15b4 | 244/245 |

**Blocking acceptance condition:** `tests/fuzz_corpus/radialblur/C49_seed1_case000117.json`
does not freshly replay true. Its unchanged, hash-bound F46 original stops
before returning at`0x180002cc3` in both the full corpus run and a standalone
retry with the same saved60-second limit. Candidate output remains
`6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d`,
identical to the saved successful original output. Input SHA256 is
`67378d354211b3009ba733219bacca6ec7f68b26997e636aafc7b525a79f859a`.
The earlier `C49-radial-smart-r9.md` already records the same60 fresh +1
uncompared replay limitation. This is not a newly introduced pixel mismatch.
Nevertheless the ticket's literal all-corpora-true acceptance is unmet, so this
report is **blocked**, not done. The oracle was not rebuilt, its budgets were
not raised, and the historical expectation was not relaxed. Full failure and
standalone-retry results are retained.

The standalone retry command was:

```sh
python3 tools/fuzz/run.py --plugin radialblur --jobs 1 --replay tests/fuzz_corpus/radialblur/C49_seed1_case000117.json --scratch "$TMPDIR/radial-c49-recheck" --report "$TMPDIR/radial-c49-recheck.json"
```

Framework units before/after:31 tests, OK, one skipped. Plugin unit discovery
before/after uses `python3 -m unittest discover -s tests -p 'test_PLUGIN_*.py'`.
Existing failures remain: DirectionalBlur102 tests/19 failures/44 errors;
DistanceGradation140/15/59; KiraKira134/17/44; RadialBlur197/25/54.
Failure/error test-name sets are identical before/after. These suites are not
reported as green; complete logs are retained. The framework invocation is
`PYTHONPATH=tools/fuzz python3 -m unittest test_sizes test_geometry test_framework test_route_oracles`.

inference:

- Three refusals were stale source-domain gates around already recovered
  arithmetic; RadialBlur also omitted the original unordered mask comparison.
- Mask/filter and later source composition are separate operations in
  DistanceGradation, allowing the restored Bilateral admission without changing
  its numerical kernel.
- These are retained-Unicorn CPU AEX results. They do not establish native
  Windows ISA/UCRT or native AE behavior for arbitrary inputs.
- No two distinct failed repair hypotheses without a new boundary occurred.

changed_files:

- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- Five T15b reduced corpus JSONs: only Smart result expectations and explanatory
  notes change. Inputs, parameters, geometry, original hashes and Classic
  expectations are preserved.
- `orchestra/reports/P03b-evidence/`: serial probe/replay/verification scripts,
  static excerpts, logs, compressed raw results and SHA256 manifest.
- This report.

verify:

From the worktree, run `sh orchestra/reports/P03b-evidence/verify.sh` (serial;
optionally supply plugin names). Expected: six Smart witnesses exact, no
admitted matrix mismatch, no realistic mismatch/refusal, no changed prior-exact
candidate bytes, unchanged historical unit failure names. Known current failure:
RadialBlur default corpus returns exit1 / `replay_matches_saved:false` for C49
case117; the other corpus groups return true. This failure is deliberately not
suppressed by the verification script. Oracle timeout availability may vary and remains separately reported.
`summarize.py` checks actual before/after candidate hashes and distinguishes
unchanged candidate output with an unavailable fresh oracle from a numerical
regression. Baselines are retained in compressed evidence for fresh worktrees.

The unchanged original instructions can be rerun with MAIN's emulation venv:
`python orchestra/reports/P03b-evidence/leaves.py` and
`python orchestra/reports/P03b-evidence/dg_conversion.py`.
Expected:26 leaf cases and51 mask-ownership comparisons, all assertions pass.

Final housekeeping: `git diff --check`, shell syntax and Python AST checks pass.
Largest measured scratch sample:31MiB (below5GiB); regenerable build trees/corpora were removed.
All started process sessions have exited. Evidence occupies2.8MiB; logs and
reports remain in scratch and the committed evidence directory. Text logs and
disassembly excerpts have trailing whitespace normalized; raw JSON results are
unchanged. Evidence logs are explicitly tracked despite repository ignore rules.

next:

- Follow-up required for the retained F46 C49 case117 execution-stop boundary
  before strict all-corpus acceptance can pass. Preserve its successful saved
  reference; do not replace it with an unavailable result.
- No new numerical work is proposed for the six ticket witnesses.
- Classic DirectionalBlur nonfinite ownership remains a separate task; the
  known Classic mismatch was not admitted by this change.
- Nonfinite Gaussian/other unadmitted families and native AE/UCRT validation
  remain outside this bounded result.
