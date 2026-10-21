status: blocked

summary:
- Round 3 attributes Classic error 516 to `RenderWorld:generic-world-not-admitted@5362`.
- This is NOT the candidate work-budget guard; the explicit “Any other guard … stop” condition applies.
- Original AEX succeeds for this witness; Smart matches its raw output, Classic refuses.
- No long gates or corpus rebaseline were started in Round 3; promotion remains unverified.
- Merged the latest upstream ticket update, preserving the existing F08/T05/Offset source unchanged.

facts:

`git merge --no-edit codex/public-beta-roi` created merge `748737f4`, incorporating
upstream `512b36eb`. Only the ticket text changed in this merge. F08 and T05 were
already incorporated by merge `3168b15e`. Production SHA-256 remains
`7cc086b942e9febe858c1a451d2047224bcbda1dc6e2163d79fdf4a7da5d57ea`.
The prior round verified that source equals the budget-enabled Offset semantic
candidate applied to upstream, rather than replacement with `before_source()`.

Ran the existing replay with `--jobs 2` (command under verify): exit 1,
`replay_complete`, one completed witness, `replay_matches_saved=false`.
The replay report omits the adapter's returned guard list. Added a bounded probe
that calls the existing adapter directly and retains that list. It uses the
existing public build helper and flags, without bypasses or numerical changes.
The direct probe exited 0 and recorded:

- Witness: `tests/fuzz_corpus/radialblur/seed1_case000425_df3690c920ab.json`.
  PF32 Zoom, 14x18, Outer Offset 2 in Add mode, Strength 0,
  input padding 16, output padding 5; input SHA-256
  `31569c7ee40e978d70ed1118016d90920a7df7f52e5c65339bfd249ded586cad`.
- Classic: error 516, no output frame, guard
  `RenderWorld:generic-world-not-admitted@5362`, callback counts `0 0 0 0 0 1 1`.
- AEX: `status=ok`, guards intact, session clean, output SHA-256
  `87fd3782a620116260a596081f06a29f0a4e2615dee460dc52ecbd456b56174f`.
- Smart: error 0, raw exact to that AEX output, no refusal trace;
  callback counts `1 32 32 1 1 1 1`.
- Saved Classic was a successful mismatch: 111 differing bytes / 36 words,
  first word 20 (byte 80), expected `6401c23d`, actual `d83b493e`.
  Its saved output hash was
  `e6fc9f007de8a3a8427b8626113abb2d35e7520b1f83ade411b925850aa67945`.
- Trace evidence: `orchestra/reports/T01-radial-offset-refusal-trace.json`,
  7,443 bytes, SHA-256
  `59c3bf7c88b8bcb160090b6f8d1792ec2f21df6e531a527363c255885fc532c2`.

Reference qualification: worker SHA-256
`93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
This round again reproduces 4/6 fuzz calibration anchors; both PF32 anchors
still differ from the containment-worker recordings. The prior round's separate
historical Strength/Rotation-neutral/Gain calibration was 18/18. Thus Smart
exact here means exact to the requested offset worker; cross-worker numerical
improvements are not established. Original AEX identity is retained in the JSON.

One consolidated before/after table follows. Historical and partial observations
are explicitly identified; no completed seed-1 n=500 after-result exists.
E = exact, M = mismatch, R = refusal, U = uncompared.

| Suite / route | Before | After candidate | Round 3 evidence / limitation |
| --- | --- | --- | --- |
| Offset 390 conditions, three builds, Classic/Smart | Historical 390 exact reported in brief; not independently completed here | Prior round reached 108/390, 648 exact replays | Not resumed: non-budget guard stop |
| Retained 9,645 conditions, three builds, Classic/Smart | Historical 57,870 exact public replays | Not run to completion | Not resumed: non-budget guard stop |
| Saved corpus, Classic, 35 cases | 24 M, 11 R | Prior round: 23 E, 12 R | One M→R freshly confirmed; guard above |
| Saved corpus, Smart, 35 cases | 35 M | Prior round: 35 E | Witness Smart freshly exact; worker qualification limitation applies |
| Saved corpus PF8 Outer Offset ≠0, both routes | 5 cases / 10 M routes | Prior round: 10 E routes | No new cluster-wide replay; not cross-worker proof |
| Seed 1 n=500, Classic | Completed baseline: 62 E, 24 M, 413 R, 1 U | Prior partial 325: 86 E, 0 M, 238 R, 1 U | Full after campaign not run; populations differ |
| Seed 1 n=500, Smart | Completed baseline: 74 E, 35 M, 390 R, 1 U | Prior partial 325: 115 E, 0 M, 209 R, 1 U | Full after campaign not run; populations differ |

Table sources: `reports/fuzz/radialblur_20261021.json` (baseline completed 500;
AEX 461 success, 32 reject, 7 budget),
`orchestra/reports/T01-radial-offset-corpus-replay.json`,
`orchestra/reports/T01-radial-offset-fuzz-partial.log`,
`orchestra/reports/T01-radial-offset-validation-partial.log`, and the fresh trace.
The old round's detailed provenance remains in this report at commit `16bcc808`.

policy:

The allowed work-budget exception does not apply. The measured guard returns
before `CheckedRadialGenericBudget`; no estimated work was measured and no
estimate-versus-cap claim is made. The code's work cap remains 350,000,000.
No expectations, corpus entries, production guards, or budget were changed.

inference:

The broadened Offset control admission reaches the generic world/layout check.
For this PF32 witness the output rowbytes are 14×16+5 = 229, incompatible with
the world pair check's pixel alignment requirement. This explains a layout
rejection consistent with the measured guard; the guard itself is proven by
trace. No guard-bypass experiment or source fix was attempted after the stop.
The new budget term is Rotation-only, whereas this witness is Zoom; the trace
independently rules out the budget-exception hypothesis.

changed_files:

- `tools/fuzz/probe_radialblur_offset_refusal_T01.py`: reproducible direct adapter trace capture, disposable build cleanup.
- `orchestra/reports/T01-radial-offset-refusal-trace.json`: bounded measured evidence.
- `orchestra/reports/T01-radial-offset-promote.md`: this Round 3 report.
- `orchestra/tickets/T01-radial-offset-promote.md`: upstream Round 3 instruction, via requested merge only.
- Production remains the existing committed Offset candidate with F08/T05; no production edits this round.

verify:

From this worktree, the direct probe should exit 0 and report Classic 516 with
`RenderWorld:generic-world-not-admitted@5362`, Smart exact, and the AEX hash above.
The replay command should exit 1 because saved results differ. Both commands
use MAIN assets and the cache worker read-only, and direct logs to ticket scratch.
The probe removes its regenerable build directory even on failure.

```sh
export TMPDIR="$PWD/orchestra/state/T01-radial-offset-promote/round3"
mkdir -p "$TMPDIR"
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
python3 tools/fuzz/probe_radialblur_offset_refusal_T01.py \
  --worker "$worker" \
  --corpus tests/fuzz_corpus/radialblur/seed1_case000425_df3690c920ab.json \
  --scratch "$TMPDIR/direct-trace-work" \
  --report "$TMPDIR/direct-trace-recheck.json" \
  > "$TMPDIR/direct-trace-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --worker "$worker" \
  --replay tests/fuzz_corpus/radialblur/seed1_case000425_df3690c920ab.json \
  --jobs 2 --scratch "$TMPDIR/trace-work" --report "$TMPDIR/trace-recheck.json" \
  > "$TMPDIR/trace-recheck.log" 2>&1
git diff --check
```

Actual direct-probe execution used the same arguments with report destination
`orchestra/reports/T01-radial-offset-refusal-trace.json` and log
`$TMPDIR/direct-trace.log`; the existing replay used `$TMPDIR/trace.json` and
`$TMPDIR/trace.log`. Scratch after disposable build cleanup: 93 MiB, below 5 GiB.

next:

Orchestrator decision/follow-up ticket required for the non-budget world/layout
refusal. Preserve the witness and do not rebaseline it as an exact improvement.
Resolve the PF32 reference calibration boundary, then complete the Offset 390,
retained 9,645, existing RadialBlur tests, and seed-1 n=500 before claiming
promotion. The current promotion runner also needs a reviewed `--jobs 2`
implementation for those long gates; it currently runs serially.
