status: done
summary:

- Completed all 10 plugins × seeds 101–105 × 300 cases (15,000 distinct cases), sequentially with the default F46 worker and jobs=1.
- Primary routes: 14,126 exact / 2 mismatch / 791 refusal / 81 unresolved. Primary = Smart, except Smoother v1 Classic.
- Smart mismatches: DistanceGradation seed104 case207 PF8 and RadialBlur seed102 case8 PF32; both saved and replayed. Smoother v1 Classic has no mismatches.
- Saved all 5,875 mismatch witnesses across both routes; no production/framework, release-gate or ledger changes.

facts:

FACT: Source commit `038e46f6bc27213ff7432dfa060496a3c283cfd5`; branch `orch/S01-wide-mismatch-sweep`.
The default selected worker is `/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker`, SHA-256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
All 50 framework hash manifests match. Each compressed original report retains AEX, source, candidate,
worker and framework provenance plus all original case rows; `manifest.json` binds each archive's
uncompressed SHA-256 and every committed witness SHA-256. Original assets were used in MAIN by absolute path.
No reference worker was rebuilt.

FACT: All runs used max-size=256, case-timeout=10 seconds, shrink-attempts=32, shrink-seconds=10,
and the default 30-minute campaign budget. No campaign exhausted its budget.
The main loop stopped on the DistanceGradation seed105 exit=2, then resumed the remaining five plugins.
All other initial campaigns exited 0. Measurement success does not mean numerical conformance.

Primary-route table. Each cell is **E/M/R/U**: exact / raw mismatch / explicit Mac refusal /
unresolved (uncompared or Mac timeout). Initially failed framework cases are shown separately below and
replaced only by their documented successful remeasurements. E is bit-exact raw active ARGB output, with no tolerance.

| Plugin / route | 101 | 102 | 103 | 104 | 105 |
| --- | --- | --- | --- | --- | --- |
| colorkeep / smart | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmblur / smart | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmcolorkey / smart | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmdirectionalblur / smart | 288/0/9/3 | 285/0/13/2 | 286/0/13/1 | 279/0/19/2 | 293/0/7/0 |
| olmdistancegradation / smart | 280/0/9/11 | 283/0/5/12 | 283/0/5/12 | 287/1/5/7 | 278/0/8/14 |
| olmkirakira / smart | 289/0/11/0 | 287/0/13/0 | 286/0/14/0 | 294/0/6/0 | 282/0/18/0 |
| olmsmoother / classic | 221/0/79/0 | 201/0/99/0 | 204/0/96/0 | 192/0/108/0 | 210/0/90/0 |
| olmsmoother2 / smart | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| olmtoondilate / smart | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 | 300/0/0/0 |
| radialblur / smart | 270/0/27/3 | 267/1/29/3 | 267/0/29/4 | 264/0/30/6 | 250/0/49/1 |

Classic-route accounting, **E/M/R/U/N**, where N is the separately verified no-write contract (not numerical exactness):

| Plugin | 101 | 102 | 103 | 104 | 105 |
| --- | --- | --- | --- | --- | --- |
| colorkeep | 67/154/79/0/0 | 60/141/99/0/0 | 67/137/96/0/0 | 71/121/108/0/0 | 65/145/90/0/0 |
| olmblur | 24/0/276/0/0 | 20/0/280/0/0 | 22/0/278/0/0 | 14/0/286/0/0 | 20/0/280/0/0 |
| olmcolorkey | 2/298/0/0/0 | 1/299/0/0/0 | 2/298/0/0/0 | 4/296/0/0/0 | 1/299/0/0/0 |
| olmdirectionalblur | 6/285/9/0/0 | 7/280/13/0/0 | 5/282/13/0/0 | 4/277/19/0/0 | 5/288/7/0/0 |
| olmdistancegradation | 7/291/0/2/0 | 13/283/0/4/0 | 12/287/0/1/0 | 7/292/0/1/0 | 7/290/0/3/0 |
| olmkirakira | 0/34/266/0/0 | 0/49/251/0/0 | 0/42/258/0/0 | 0/40/260/0/0 | 0/45/255/0/0 |
| olmsmoother | 221/0/79/0/0 | 201/0/99/0/0 | 204/0/96/0/0 | 192/0/108/0/0 | 210/0/90/0/0 |
| olmsmoother2 | 0/0/300/0/0 | 0/0/300/0/0 | 0/0/300/0/0 | 0/0/300/0/0 | 0/0/300/0/0 |
| olmtoondilate | 0/0/0/0/300 | 0/0/0/0/300 | 0/0/0/0/300 | 0/0/0/0/300 | 0/0/0/0/300 |
| radialblur | 6/145/149/0/0 | 2/125/173/0/0 | 3/130/167/0/0 | 4/108/188/0/0 | 1/113/186/0/0 |

Every primary-route mismatch is listed below. Word indices are zero-based in packed active ARGB. PF32 values include exact IEEE-754 bits; these are not tolerance comparisons. Original and reduced observations are distinct.

| Plugin | Seed / case | Depth | Input | Geometry | First word | Mac | Reference | Differing words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| olmdistancegradation | 104 / 207 | 8 | original | 140×159 | 93 | `0xc4` (196) | `0xc5` (197) | 2558 |
| olmdistancegradation | 104 / 207 | 8 | shrunk | 140×159 | 93 | `0xc4` (196) | `0xc5` (197) | 2558 |
| radialblur | 102 / 8 | 32 | original | 1×217 | 120 | `0x3eb5863d` (0.35453978180885315) | `0x3f0ee30a` (0.55815184116363525) | 2 |
| radialblur | 102 / 8 | 32 | shrunk | 1×54 | 116 | `0x3d658b04` (0.056040778756141663) | `0x3de58a2a` (0.1120799332857132) | 12 |

- Shrunk input: [tests/fuzz_corpus/olmdistancegradation/seed104_case000207_S01.json](../../tests/fuzz_corpus/olmdistancegradation/seed104_case000207_S01.json); SHA-256 `6a36dc40634dcb8207dc87489bb9db4bd5032c661fbdad4f07e961c3068fd1e8`. Shrink attempts=6, accepted=0. No global minimality claim.

- Shrunk input: [tests/fuzz_corpus/radialblur/seed102_case000008_S01.json](../../tests/fuzz_corpus/radialblur/seed102_case000008_S01.json); SHA-256 `f64f749d8872b98ec8b436ac961052a69d3ffe699cfa847fbb9925d682e25a9f`. Shrink attempts=32, accepted=5. No global minimality claim.

FACT: ColorKeep seed101 initially omitted 30 Classic witnesses at the runner's 2,000,000-byte corpus cap.
A scratch retention loop moved completed corpus files to each run's `retained/` directory every three seconds;
all later initial campaigns retained every reported witness. ColorKeep seed101 was rerun with a 64,000,000-byte cap:
its full summary matched the initial summary (Smart 300 exact; Classic 67 exact, 154 mismatch, 79 refusal),
and all 154 witnesses were retained. Both initial and rerun reports are committed. The primary table uses the rerun.

FACT: DistanceGradation seed105 cases 50 and 123 lost their original result rows when shrinking raised
`PermissionError: [Errno 1] Operation not permitted` at `os.killpg` in `tools/fuzz/core.py:35`.
The initial report has 298 numerical case rows plus 2 framework-error rows (exit=2); it is preserved unchanged.
A bounded follow-up invoked the unchanged `run_one` for exactly those two indices with the same generation,
worker, timeout and default shrinking. Both returned Smart exact / Classic mismatch, with saved witnesses.
The final table substitutes those two recovered rows; it does not count them as new distinct cases.
The recovery report and exact [recovery procedure](S01-wide-mismatch-sweep/retry-procedure.md) are committed.
No orphaned worker/candidate from the failed run remained when checked.

FACT: Saved witness counts (all mismatching routes, including Classic):

| Plugin | Saved cases |
| --- | ---: |
| colorkeep | 698 |
| olmcolorkey | 1490 |
| olmdirectionalblur | 1412 |
| olmdistancegradation | 1443 |
| olmkirakira | 210 |
| radialblur | 622 |

FACT: Every committed witness was loaded with the existing `core.load_corpus` and its matching adapter:
5,875/5,875 input SHA-256 and geometry/byte-length checks passed. Every initially mismatching route remains
mismatching in its saved reduced result. The two primary witnesses were additionally replayed with their
hash-bound worker; see the committed replay reports. Other Classic witnesses were structurally validated,
not all rerendered after export.

FACT: `memory_pressure` was run before each plugin (therefore between plugins). Captured system-wide free percentages (trailing spaces trimmed in committed logs):

| Plugin | Free % |
| --- | ---: |
| colorkeep | 52% |
| olmblur | 53% |
| olmcolorkey | 54% |
| olmdirectionalblur | 47% |
| olmdistancegradation | 53% |
| olmkirakira | 48% |
| olmsmoother | 50% |
| olmsmoother2 | 49% |
| olmtoondilate | 50% |
| radialblur | 50% |

Actual campaign command pattern (from the worktree root; P is each plugin and S is 101 through 105):

```sh
D="$PWD/orchestra/state/S01-wide-mismatch-sweep/$P/seed$S"
mkdir -p "$D"
python3 tools/fuzz/run.py --plugin "$P" --n 300 --seed "$S" --jobs 1 \
  --scratch "$D/work" --report "$D/report.json" --corpus "$D/corpus" > "$D/run.log" 2>&1
```

Actual ColorKeep recovery command:

```sh
D=orchestra/state/S01-wide-mismatch-sweep/rerun-colorkeep101
python3 tools/fuzz/run.py --plugin colorkeep --n 300 --seed 101 --jobs 1 \
  --scratch "$D/work" --report "$D/report.json" --corpus "$D/corpus" \
  --corpus-max-bytes 64000000 > "$D/run.log" 2>&1
```

FACT: Final scratch usage was 207 MiB (below 5 GiB); no disposable `run_*` build directories remained. Campaign, retention, recovery and replay processes all exited.

inference:

INFERENCE: The two primary witnesses warrant separate DistanceGradation and RadialBlur fix/triage tickets.
This measurement does not establish their root causes. Classic mismatches are independent measured data,
not automatically the same causes as Smart mismatches. Finite seeded coverage and local CPU emulation
against the fake SDK host do not establish all-input or native AE/Windows equivalence. Time-budget and
uncompared counts can vary with machine contention; they are not evidence of pixel equality.

changed_files:

- `orchestra/reports/S01-wide-mismatch-sweep.md` (this report).
- `orchestra/reports/S01-wide-mismatch-sweep/`: 50 compressed original campaign reports, the initial ColorKeep
  report, recovery report/procedure, two replay reports, manifest, integrity audit/procedure, campaign log and ten memory-pressure logs.
- `tests/fuzz_corpus/{colorkeep,olmcolorkey,olmdirectionalblur,olmdistancegradation,olmkirakira,radialblur}/seed*_case*_S01.json`:
  5,875 saved mismatch JSON files. Formatting was compacted without changing parsed contents.
- No code, release gate, ledger, MAIN or emulator-source edits; no push.

verify:

The [evidence integrity audit](S01-wide-mismatch-sweep/audit-procedure.md) passed: 50 campaigns, 15,000 distinct cases, 5,875 hash-checked witnesses and two identical replays. Its exact command and expected result are included there.

Run from this worktree root. The following replays should exit 0 with `replay_matches_saved: true` and retain
Smart `mismatch` with the reduced first words shown above. Scratch stays inside this ticket.

```sh
mkdir -p orchestra/state/S01-wide-mismatch-sweep/verify
python3 tools/fuzz/run.py --plugin olmdistancegradation --jobs 1 \
  --replay tests/fuzz_corpus/olmdistancegradation/seed104_case000207_S01.json \
  --scratch orchestra/state/S01-wide-mismatch-sweep/verify/dg-work \
  --report orchestra/state/S01-wide-mismatch-sweep/verify/dg.json \
  > orchestra/state/S01-wide-mismatch-sweep/verify/dg.log 2>&1
python3 tools/fuzz/run.py --plugin radialblur --jobs 1 \
  --replay tests/fuzz_corpus/radialblur/seed102_case000008_S01.json \
  --scratch orchestra/state/S01-wide-mismatch-sweep/verify/radial-work \
  --report orchestra/state/S01-wide-mismatch-sweep/verify/radial.json \
  > orchestra/state/S01-wide-mismatch-sweep/verify/radial.log 2>&1
```

To repeat the whole sweep, use the campaign command pattern for all ten plugins and seeds 101–105,
sequentially with `--jobs 1`; add `--corpus-max-bytes 64000000` and a fresh scratch destination to avoid
repeating the initial retention-cap loss. Expected: 50 complete 300-case campaigns, primary numerical
mismatches at the two retained cases. Shrink histories and timeout/refusal totals are bounded wall-time observations,
not guaranteed byte-identical rerun artifacts.

next:

- DistanceGradation: investigate seed104 case207 PF8, preserving its Smart mismatch and the original/retained 140×159 input.
- RadialBlur: investigate seed102 case8 PF32, using the retained 1×54 witness and original 1×217 case separately.
- Framework follow-up: investigate timeout cleanup `os.killpg` PermissionError in the two saved DG error traces.
- Route-specific Classic triage can use the 5,875 retained cases without conflating Classic and Smart oracles.

orchestrator note (merge curation):
- The 5,873 Classic-route witnesses were moved out of `tests/fuzz_corpus/` into
  `orchestra/reports/S01-wide-mismatch-sweep/classic-witnesses.tar.gz`
  (SHA-256 `c01f2080ecff1cc09fea294f1fc45b7aeacde594c9543bbfef5dc7bf1b78889d`; also at
  `~/.cache/olm-emu/S01-classic-witnesses/`). Reason: AE always takes the Smart route for these
  SmartFX plugins, so Classic mismatches are not shipping-relevant; keeping them in the corpus would add
  69 MB and thousands of expected-mismatch replays. Extract with `tar xzf` from the repo root.
- Only the two primary (Smart) witnesses stay in the corpus.
