status: blocked

summary:
- Round 4 found forbidden exact→refusal changes: seed 1 case 193 Classic/Smart and case 425 Smart.
- Both base and candidate used the same calibrated offset worker; the AEX succeeded with identical hashes for these cases.
- Offset 390 completed: 2,340/2,340 public replays exact across O2, ordinary O2 and ASan/UBSan, Classic/Smart.
- Both seed-1 n=500 campaigns completed; the 9,645-condition retained gate remains incomplete. Corpus was NOT rebaselined.
- Stopped numerical work on discovering the forbidden transitions; no production, expectation, budget or guard fix was attempted.

facts:

Merged `codex/public-beta-roi` at `95b185eb` into this branch as `17015e12`.
F08/T05 were already retained; this merge did not change RadialBlur production.
Verified `candidate_source(base_source, budget=True) == production_source`.
Production differs from `before_source()`; it was not overwritten with that old epoch.
The existing promotion is from WIP `f903db04` and merge `3168b15e`.

Identity bindings:

- Base source (`95b185eb`): `66ed2aeb5132e0a5670b3801a781e8d3e5a77c142533911c9b497b1b4b30db85`.
- Candidate production: `7cc086b942e9febe858c1a451d2047224bcbda1dc6e2163d79fdf4a7da5d57ea`.
- Requested offset worker: `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
- Original AEX: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.

Worker calibration replayed 18 recorded original-AEX output hashes from Strength,
Rotation-neutral and Gain: 18/18 exact. `T01-round4-offset390.json` preserves
those hashes, all 390 independent measurements, source and build bindings.
Fuzz's separate older calibration is 4/6: its PF32 recordings used different
reference math. Therefore the old October 21 mismatch cluster is not credited
as a production improvement merely because this worker returns different bytes.
The new base/candidate campaigns use the same worker, generated inputs, parameters,
strides, header/core and existing compiler helper, with no bypass switches.
All successful paired AEX renders have identical hashes. Case 363's oracle changed
from a 10-second timeout to success; both Mac routes still refused, so it did not
create an apparent exact improvement. Other oracle differences are diagnostic text.

First forbidden change (by seed/index order):

- Unreduced case 193: PF16 Zoom, 12×8, SDR, Strength 29, Outer mode Max,
  Outer Offset 0; input/output padding 7/1 bytes (rowbytes 103/97).
- Input hash: `23bc8d8c959e32fffcdaee5ca3e8ecf56c5417ebb5d2e323a1552b12c72612c0`.
- AEX and base Classic/Smart: successful 768-byte output,
  `61419588ac096ac05cd390e83bc6a71aa4f6db1c7b50b1d36ab130dc272ccde8`.
- Candidate Classic/Smart: error 516, no output; both traces identify
  `RenderWorld:generic-world-not-admitted@5362`.
- This is an admission regression, not a differing output byte; no first pixel
  mismatch is invented for an empty refused output.

Second forbidden change:

- Unreduced case 425: PF32 Zoom, 14×18, HDR, Strength 0, Outer Add Offset 5,
  Thickness 11.962330205270554; input/output padding 16/5 bytes.
- Input hash: `7519cd8b98279da222df8e4762a09ccdf3fde98e32f4e9ee71a5f4d9e455c725`.
- AEX and base Smart: successful 4,032-byte output,
  `8405927c8b78605ecd5b76dd15eb2a7b5d0b85df52ce708a410305069cd117dc`.
- Candidate Smart: error 516, same `generic-world-not-admitted` guard.
- The previously saved *reduced* case 425 has different pixels, Offset 2 and
  Thickness 10; its Smart route remains exact. A replay of only the saved
  mismatch corpus therefore does not detect this regression or case 193.

Single before/after table: E=exact, M=mismatch, R=refusal, U=uncompared.
Retained-suite numbers count conditions; each verified condition has six public
replays. Their “before” is the immutable recorded exact output, not a fresh base
render. Fuzz “before” is the fresh `95b185eb` run unless explicitly marked saved.

| Suite / route | Before | Candidate after | Disposition |
| --- | --- | --- | --- |
| Offset 390 | Old `before_source()` Classic: 32 E / 16 M / 342 R | 390 E; 2,340 exact public replays | Completed, 0 diffs / 0 rejections |
| Retained getters | 30 E | 30 E | Completed |
| Retained topology | 252 E | 252 E | Completed |
| Retained typed | 28 E | 28 E | Completed |
| Retained independent | 384 E | 384 E | Completed |
| Retained Size topology | 180 E | 180 E | Completed |
| Retained Zoom fade | 299 E | 182 E reported | Partial |
| Retained Rotation Size/Noise independent | 96 E | Not completed | Pending |
| Retained Size range | 560 E | Not run | Pending |
| Retained Size enabled | 720 E | Not run | Pending |
| Retained Noise range | 952 E | Not run | Pending |
| Retained Seed/Thickness | 1,532 E | Not run | Pending |
| Retained Quality | 2,262 E | Not run | Pending |
| Retained Gain | 1,140 E | Not run | Pending |
| Retained Strength | 1,128 E | Not run | Pending |
| Retained NoOp | 82 E | Not run | Pending |
| Retained total | 9,645 E / 57,870 exact replays | 1,056 conditions / 6,336 exact replays reported | Gate incomplete |
| Seed 1 n=500, Classic | 85 E / 1 M / 413 R / 1 U | 137 E / 0 M / 362 R / 1 U | **1 forbidden E→R**, 1 allowed M→R; 53 R→E |
| Seed 1 n=500, Smart | 109 E / 0 M / 390 R / 1 U | 180 E / 0 M / 319 R / 1 U | **2 forbidden E→R**; 73 R→E |
| Seed 1 PF8 nonzero Outer Offset, Classic (40 cases) | 5 E / 35 R | 21 E / 19 R | 16 R→E; 0 M on either build |
| Seed 1 PF8 nonzero Outer Offset, Smart (40 cases) | 5 E / 35 R | 21 E / 19 R | 16 R→E; 0 M on either build |
| Saved corpus Classic, 35 cases | Saved: 24 M / 11 R; fresh base: 23 E / 1 M / 11 R | 23 E / 12 R | 1 allowed M→R; no fresh-base exact loss |
| Saved corpus Smart, 35 cases | Saved: 35 M; fresh base: 35 E | 35 E | No fresh-base byte changes |
| Saved PF8 Outer Offset cluster, Classic/Smart | Saved: 5 M each; fresh base: 5 E each | 5 E each | Worker/reference boundary, not a measured Offset numerical improvement |
| Existing RadialBlur smoke tests | Base shares failing Thickness string assertion; full base run stopped | 10 pass / 1 failure | Existing static UI assertion; 8 numerical/host smoke tests passed |

The first full gate process exited 1 on a runner aggregation `KeyError: 'matrix'`
after completing Offset 390 and reporting 6,336 retained replays. Ninety-six old
Rotation Size/Noise rows omit that field. Fixed only the counter label, then
restarted with `--jobs 2`; stopped that restart at the forbidden fuzz finding
(last progress: 84 Offset conditions, 504 replays). No numerical failure was
reported in the retained prefix. The retained suite counts above conservatively
include only complete, reported chunks from the first run, not unreported work
or duplicate restart work. Full retained success is NOT claimed.

`validate_radialblur_tests_T01.py` invokes existing tests without changing their
assertions. The one failure is the old exact string
`PF_Precision_HUNDREDTHS, 0, 0,\n\t                     THICKNESS_DISK_ID`.
That string is absent in both base and candidate. The fresh base smoke run was
stopped after its first test passed; the archived hash-bound October tests were
not started. The numerical public suite coverage comes from the gate above.

policy:

Each allowed mismatch→refusal observed this round is listed separately:

- Saved reduced `seed1_case000425_df3690c920ab.json`, Classic: M→R. Prior Round 3
  trace proves `RenderWorld:generic-world-not-admitted@5362`; fresh same-worker
  base/candidate replay confirms the transition, and AEX succeeds.
- Seed-1 full campaign case 425, Classic: M→R, same guard. Base differs by
  520 bytes / 157 words; first difference byte 16 / word 4, expected `361a813f`,
  actual `08dd733f`. AEX succeeds; candidate returns no frame.

These are permitted by Round 4, but cannot excuse the three exact→refusal routes.
None is attributed to the work budget. All named cases are Zoom; the new budget
term is Rotation-only. No estimated-work-vs-cap claim is made. Cap stays
350,000,000. `tests/fuzz_corpus/radialblur` is unchanged; the experimental
rebaseline-tool edit was discarded without running it on the corpus.

inference:

Broadening Offset admission changes dispatch before the existing generic
world/SDR gate. Case 193 exposes odd typed row strides; case 425 uses HDR pixels.
The generic gate can thus reject inputs that the F08 Zoom path rendered exactly.
The guard and transitions are measured facts; pinpointing each constituent
predicate and choosing a general dispatch/world fix is follow-up work.
No guard bypass, expected-value modification, or repair experiment followed
identification of the exact regressions.

changed_files:

- `tools/emulation/probe_radialblur_offset_promote_20261002.py`: bounded process execution with `--jobs 2`, isolated temporary render/config directories, NoOp fixture process isolation, per-suite counts and independent checkpoints. Default `matrix` label handles the old 96-row schema; full rerun remains unverified.
- `tools/fuzz/run_radialblur_baseline_T01.py`: selects a historical candidate source for the unchanged fuzz runner, without modifying production or MAIN.
- `tools/emulation/validate_radialblur_tests_T01.py`: invokes existing smoke/archived tests and records failures without rewriting expectations.
- `tools/emulation/package_radialblur_offset_evidence_T01.py`: packages the completed measurements and derives counts from the recorded rows.
- `orchestra/reports/T01-round4-*.json` and `.log`: complete paired fuzz/corpus evidence, Offset 390, partial gate logs, smoke results and summary; every artifact is below 2 MB.
- `orchestra/reports/T01-round4-witnesses/seed1_case000193.json` and `seed1_case000425.json`: unreduced inputs with the measured base results, outside the regression corpus.
- `orchestra/reports/T01-radial-offset-promote.md`: this report.
- Upstream F12/ticket files arrived only through the requested merge; no edits to other plugins, release gates, production or forbidden-action lists this round.

verify:

Shortest reproduction, from the worktree root (fresh destination directories).
Base replay should exit 0 and match both saved witness results. Candidate replay
should exit 1: case 193 loses Classic/Smart exact, case 425 loses Smart exact;
all four candidate routes return 516. The saved base Classic case 425 is a mismatch.

```sh
export TMPDIR="$PWD/orchestra/state/T01-radial-offset-promote/recheck"
mkdir -p "$TMPDIR"
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
python3 tools/fuzz/run_radialblur_baseline_T01.py \
  --baseline-revision 95b185eb --baseline-scratch "$TMPDIR" \
  --plugin radialblur --worker "$worker" --jobs 2 \
  --replay orchestra/reports/T01-round4-witnesses \
  --scratch "$TMPDIR/base-work" --report "$TMPDIR/base.json" \
  > "$TMPDIR/base.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --worker "$worker" --jobs 2 \
  --replay orchestra/reports/T01-round4-witnesses \
  --scratch "$TMPDIR/after-work" --report "$TMPDIR/after.json" \
  > "$TMPDIR/after.log" 2>&1
```

Exact full-campaign commands used, with `$TMPDIR` set to
`$PWD/orchestra/state/T01-radial-offset-promote/round4`:

```sh
python3 tools/fuzz/run_radialblur_baseline_T01.py \
  --baseline-revision 95b185eb --baseline-scratch "$TMPDIR" \
  --plugin radialblur --n 500 --seed 1 --jobs 2 --budget-minutes 180 \
  --worker "$worker" --scratch "$TMPDIR/fuzz-base-work" \
  --corpus "$TMPDIR/fuzz-base-corpus" --report "$TMPDIR/fuzz-base.json" \
  > "$TMPDIR/fuzz-base.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 2 \
  --budget-minutes 180 --worker "$worker" --scratch "$TMPDIR/fuzz-after-work" \
  --corpus "$TMPDIR/fuzz-after-corpus" --report "$TMPDIR/fuzz-after.json" \
  > "$TMPDIR/fuzz-after.log" 2>&1
```

Both exited 0 (`complete`, 500 measurements); this means measurement succeeded,
not acceptance. Counts and forbidden transitions must be checked as above.
Corpus commands were the same baseline/current entrypoints, replacing campaign
options with `--replay tests/fuzz_corpus/radialblur`, and using
`corpus-{base,after}-work`, `corpus-{base,after}.json` and corresponding logs.
Both completed all 35 cases and exited 1 because saved results changed.

Gate invocation used the MAIN venv and existing build helper flags:

```sh
probe_python='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$probe_python" -u tools/emulation/probe_radialblur_offset_promote_20261002.py \
  --worker "$worker" \
  --worker-build /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/offset-timeout-reference-build.json \
  --output "$TMPDIR/gates" --report "$TMPDIR/gates.json" --jobs 2 \
  > "$TMPDIR/gates.log" 2>&1
"$probe_python" tools/emulation/validate_radialblur_tests_T01.py \
  --report "$TMPDIR/tests.json" > "$TMPDIR/tests.log" 2>&1
git diff --check
```

Expected gate target after a future fix: 390 exact independent conditions plus
9,645 retained, 60,210 public replays, no diffs/rejections. This round did NOT
reach that target. Restart used `gates-complete` output/report/log names.
Evidence packaging, before scratch cleanup, was
`"$probe_python" tools/emulation/package_radialblur_offset_evidence_T01.py`.
Round 4 raw frames and regenerable builds were deleted after evidence packaging.
Remaining ticket scratch is 93 MiB (below 5 GiB). All scratch writes were confined
to the ticket directory; retained
artifacts contain hashes/parameters and compressed small witness input only.

next:

A follow-up ticket must preserve the base-exact Zoom dispatch for case 193 and
unreduced case 425 while retaining the general Offset arithmetic restoration.
Do not merge this as accepted production or rebaseline the corpus yet. After the
fix, replay these two witnesses, then finish the 390/9,645 gates and repeat the
paired seed-1 n=500 check. Existing corpus-only replay is insufficient. Review
legacy source-hash/UI test bindings separately without editing numerical expectations.
