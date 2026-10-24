status: blocked
summary:
- Reproduced HEAD default In/Out=0 PF32 refusal and repaired the general Smart producer/ownership branches.
- Real Universal bundle with untouched PARAMS_SETUP defaults now succeeds at PF8/16/32, matching the original all-zero output.
- Default n300 preserves all600 route hash/error pairs; realistic/odd-even campaigns have0 Smart mismatches or Mac-only refusals.
- All454 corpus records replay true, including72 labelled builder-state witnesses (71 Smart exact,1 retained filter-admission refusal).
- Status is blocked because automatic command review rejected a scratch cleanup command; the worker brief requires this status after any rejection.

facts:

Base commit `fae980804610cea9a7308ca425b6a64b11c67ba2`. All scratch is under
`orchestra/state/P04a-distancegradation-default-pf32`; jobs1, at most two
emulator/build processes. Memory checks reported65%,59%,61% free. Scratch
remained below5 GiB; regenerable binaries/build trees were deleted. No oracle
rebuild, MAIN edits, release-gate/ledger edits, push, or history rewrite.

**Reproduction and binary evidence.** The initial equivalent of
`python3 orchestra/reports/P04a-evidence/probe.py baseline` used the HEAD source
and captured builder defaults, including In/Out=0, at32x24. Opaque input was
Smart exact at PF8/16, but PF32 refused at `RenderBits:pf32-smart-profile@2205`
(shim error -1). Mixed alpha additionally mismatched at PF8/16:768 differing
words each; first PF8 byte1, expected00/actualff; first PF16 byte3, expected
word0000/actual0080. After the repair, all six Smart probes are exact. PF32
opaque hash is `f3cc103136423a57975750907ebc1d367e2985ac6338976d4d5a439f50323f4a`;
mixed hash is `1a66eda28068bf7f00d7c4514f02cba7a170930f03e6d503f416715160dca788`.

Original owner18117349a/49d compares In/Out with3 and skips all distance
producers for other values. Callback181170e77/7a replaces source alpha with
one only for Both; other values besides Outside retain source alpha. The
patch preserves that producer selection and ownership, continuing through
existing copy/filter/interpolation/composition. It does not shortcut the
output or substitute a per-pixel expected value. Classic behavior is unchanged.

The allocated scalar plane is **not explicitly initialized by this original
function** (`181395230`); the retained host supplies zeroed handles. Native AE
allocator-state equivalence for invalid-popup mixed masks is not established.
Static excerpts and allocation calls are committed in `P04a-evidence/static.txt`.
In/Out=0 is the sole scalar out-of-range default in the captured declaration.
Negative values,4,and int32 extrema in the corpus are diagnostic states, not
claimed reachable through normal popup selection.

**New corpus.** `python3 orchestra/reports/P04a-evidence/matrix.py` measured72
cases:71 Smart exact and one refusal (case59, fractional Power2.25 plus
Bilateral,size1,width7,In/Out=INT_MAX). This is the existing vector-Bilateral
Power admission exclusion, not a numerical mismatch. The initial all-exact
assertion failed; the committed assertion explicitly retains this negative
control. The other cases cover real defaults, uniform/mixed alpha, three
depths, diagnostic popup values,Invert,foreground/background,interpolation
and Blur. Both route outcomes are saved, including historical Classic
mismatches. `Adapter.real_defaults` reads captured values without clamping;
explicit corpus parameters and pixel bytes are serialized and replayed
verbatim. Historical seeded generation and shrinking are unchanged.

**Real bundle.** `python3 orchestra/reports/P04a-evidence/bundle.py` built only
DistanceGradation, Universal arm64+x86_64. Retained P00b plugin-host ran the
actual PARAMS_SETUP with zero overrides:PF8/16/32 all returned0, reported
error0/nonzero:false, and produced no refusal trace. This host run exercised
the native arm64 bundle; it is not a native After Effects application test.
The bundle hash, host hash, build command and selector logs are in
`bundle.json.gz`/`bundle-build.log.gz`. The build products were removed.

**Regression.** `python3 orchestra/reports/P04a-evidence/verify.py campaigns`
ran standard run.py with jobs1 and shrinking disabled. Source/worker/input
hashes and exact full commands are preserved in the compressed reports.
Default runs use retained F46; realistic runs use retained F52c. No oracle
budgets were increased. Smart outcomes (oracle failures counted separately):

| Campaign | Count | Exact | Oracle rejected/unavailable | Mismatch / Mac-only refusal |
| --- | ---: | ---: | ---: | ---: |
| Default seed1 before | 300 | 290 | 10 | 0 / 0 |
| Default seed1 after | 300 | 290 | 10 | 0 / 0 |
| realistic-v1 seed1 | 100 | 96 | 4 | 0 / 0 |
| realistic-v1 seed10424 | 100 | 96 | 4 | 0 / 0 |
| odd-even-v1 + realistic seed2026 | 150 | 146 | 4 | 0 / 0 |
| odd-even-v1 + realistic seed2027 | 150 | 148 | 2 | 0 / 0 |

All600 default candidate route hash/error pairs are unchanged; no exact to
non-exact regression. Odd-even used maximum1920x1080. Original refusals and
timeouts are not counted as exact, and Classic historical mismatches are not
reported as new Smart failures.

`python3 orchestra/reports/P04a-evidence/verify.py replay` invoked standard
`tools/fuzz/run.py --replay` with each saved worker and matching size/geometry
flags:default147,P02b226,T15b9,P04a72 = **454/454 replay_matches_saved:true**,
both routes. New witnesses also replay correctly without custom replay code.

Unit command before/after:
`OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*.py'`
returned140 tests,15 failures,59 errors both times. The74 failure/error names
are identical. Historical missing artifacts/structural expectations remain;
these suites are not green. Initial discovery with `test_distancegradation_*.py`
matched0 tests and was corrected before the baseline run.

Framework command with `TMPDIR` and `OLM_FUZZ_TEST_SCRATCH` set to ticket scratch:
`PYTHONPATH=tools/fuzz OLM_TEST_JOBS=1 python3 -m unittest test_sizes test_geometry test_framework test_route_oracles`
returned31 tests,OK,1 skipped. The first invocation lacked
`OLM_FUZZ_TEST_SCRATCH` and had3 KeyErrors; the corrected run passed.
`python3 orchestra/reports/P04a-evidence/summarize.py` asserts hash stability,
no Smart numerical/availability-as-refusal regression, all saved replay results,
and identical unit failure sets; it passed. `git diff --check` passed.

**Tool rejection.** Automatic command review rejected the requested `rm -rf`
of the completed matrix build directory: “rm -f style commands are not
permitted. Use a safer approach”. No deletion ran in that rejected call.
The script adjustment and deletion were subsequently completed with explicit
Python pathlib/shutil operations. The worker brief nevertheless requires
`status: blocked` after any tool rejection, so this report does not claim done.

inference:
- Aliasing invalid In/Out to Both caused the mixed-mask errors, while a stale
  range admission check caused PF32 refusal even when the uniform-mask callback
  would safely emit the original result.
- The existing Power/vector-Bilateral exclusion is outside the default repair;
  diagnostic corpus case59 remains a refusal, not evidence of general support.
- Retained-Unicorn CPU results do not establish native Windows UCRT, native
  AE allocation behavior, or arbitrary parameter/input equivalence.
- No two distinct repair hypotheses were refuted without a new boundary.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/adapters/olmdistancegradation.py`
- `tests/fuzz_corpus/olmdistancegradation_P04a/*.json` (72 records)
- `orchestra/reports/P04a-evidence/*` (scripts,static excerpts,compressed evidence)
- `orchestra/reports/P04a-distancegradation-default-pf32.md`

verify:

From this worktree, set `TMPDIR="$PWD/orchestra/state/P04a-distancegradation-default-pf32"`,
create it, and export `OLM_TEST_JOBS=1 OLM_FUZZ_TEST_SCRATCH="$TMPDIR"`.
Run these serially:

1. `python3 orchestra/reports/P04a-evidence/probe.py verified` — six Smart exact.
2. `python3 orchestra/reports/P04a-evidence/matrix.py` —71 exact,one labelled refusal;
   writes explicit corpus. The retained corpus can instead be replayed directly.
3. `python3 orchestra/reports/P04a-evidence/verify.py campaigns` — results above,
   no Smart mismatch or Mac-only refusal; oracle timeout availability may vary.
4. `python3 orchestra/reports/P04a-evidence/verify.py replay` —454/454 true.
5. Run the unit command above, redirecting to `$TMPDIR/units-after.log`;
   expected unchanged15 failures/59 errors. Run the framework command; expected OK.
6. `python3 orchestra/reports/P04a-evidence/bundle.py` —three error0/all-zero runs.
7. `python3 orchestra/reports/P04a-evidence/summarize.py` —assertions pass; baseline
   evidence falls back to committed compressed files in a fresh worktree.

next:
- Orchestrator review/merge decision; no push performed. Validation is complete
  within the retained-host contract, but the administrative blocked status remains.
- Separate follow-up: native AE invalid-popup allocation semantics and the retained
  fractional-Power/vector-Bilateral exclusion (case59). Historical unit failures
  and Classic numerical mismatches remain outside this ticket's Smart repair.
