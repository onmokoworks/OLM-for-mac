status: blocked

summary:
- Merged `codex/public-beta-roi` at `e3f887b5` into this branch (merge `3168b15e`), preserving F08 and T05.
- The merged WIP source equals `candidate_source(current upstream source, budget=True)` byte for byte.
- Stopped on a corpus Classic route changing from successful mismatch to refusal (516); no corpus rebaseline performed.
- Offset validation reached 108 conditions / 648 exact replays; the 390-condition and 9,645-condition completion gates remain unproven.
- The production candidate remains for review, NOT approved promotion; removed the unverified WIP completion capture and its active pointer.

facts:

1. `git merge codex/public-beta-roi` completed without conflicts. A Python comparison of
   `probe_radialblur_offset_20261002.candidate_source(git show codex/public-beta-roi:mac/OLMRadialBlur/OLMRadialBlur.cpp)`
   against production returned `True`. Production differs from `before_source()`;
   it was not overwritten with the historical source. SHA-256:
   - merged upstream source: `66ed2aeb5132e0a5670b3801a781e8d3e5a77c142533911c9b497b1b4b30db85`
   - candidate production: `7cc086b942e9febe858c1a451d2047224bcbda1dc6e2163d79fdf4a7da5d57ea`
   - original AEX: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
   - requested offset worker: `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`

2. Ran the WIP promotion runner using the cache worker and its
   `offset-timeout-reference-build.json` (full command below). Its historical
   Strength, Rotation-neutral, and Gain calibration passed 18/18 recorded AEX
   hashes. The runner built production through the existing `noop.build` helpers
   in O2, ASan/UBSan, and default-contract modes, plus the historical comparison
   build; compiler flags were not invented. Last completed progress checkpoint:
   108/390 conditions, 648 exact Classic/Smart replays across three builds.
   This is a lower bound from the retained log, not a claim about unfinished
   cases. No retained-suite replays had started. Stopped its process tree after
   the corpus refusal was identified. See `T01-radial-offset-validation-partial.log`.

3. Ran `tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur`
   with the specified offset worker. All 35 corpus cases completed; saved-result
   equality was false. The complete 48,603-byte replay is committed as
   `T01-radial-offset-corpus-replay.json` (SHA-256
   `2681e1715f63ca1205d1b8474ec1b94ba2cc3cd95a3eb702441f3c7f968d5cde`).

   | Route | Saved status | Observed status | Cases |
   | --- | --- | --- | ---: |
   | Classic | mismatch | exact | 23 |
   | Classic | mismatch | refusal | 1 |
   | Classic | refusal | refusal | 11 |
   | Smart | mismatch | exact | 35 |

   First adverse transition:
   `tests/fuzz_corpus/radialblur/seed1_case000425_df3690c920ab.json`, Classic.
   PF32 Zoom, 14x18, Outer Offset slot 6 = 2, Add mode, Strength = 0,
   input padding 16 bytes, output padding 5 bytes, saved profile `hdr` with
   binary pixel reduction. Input SHA-256:
   `31569c7ee40e978d70ed1118016d90920a7df7f52e5c65339bfd249ded586cad`.
   Saved Classic returned 0 and hash
   `e6fc9f007de8a3a8427b8626113abb2d35e7520b1f83ade411b925850aa67945`;
   it differed in 111 bytes / 36 words, first word 20 (byte 80), expected
   `6401c23d`, actual `d83b493e`. Current Classic returns 516 with no raw frame;
   callback counts remain `0 0 0 0 0 1 1`. Current Smart returns 0 and matches
   the current worker hash `87fd3782a620116260a596081f06a29f0a4e2615dee460dc52ecbd456b56174f`.
   Therefore the ticket's requirement that every changed route move toward
   exact is not satisfied. `rebaseline_corpus.py` was NOT run; no expectations
   or corpus inputs/results were changed.

4. Reference qualification limitation discovered while recording results:
   the fuzz adapter's own six retained calibration hashes match only 4/6 with
   the requested worker. Both PF32 anchors differ (Zoom actual
   `40c57843a01558219e98bb52b6a9f4be10e6389081f84c7f195e2c36eac2235d`,
   expected `37eb1d2bcead7fd3e88543878f90ff6c36f1f1f65cf6a694a1385423d1f022bc`;
   Rotation actual `8d77e834eea39e4c429d37daa74db8569251b8de5d72265762e456327dcf0c57`,
   expected `20a8738362accff3c21b7a40f5c9215bf57e99635aa813cbf7828eee3b072c07`).
   The saved corpus used containment worker `3cb4855b...`; 29/35 oracle frame
   hashes changed in this replay. The table records observed statuses under
   the new worker, not verified cross-worker numerical improvements. The
   Classic success-to-refusal transition is independent of oracle pixel values.

5. Started the requested `--n 500 --seed 1` campaign with default remaining
   fuzz options, separate scratch/corpus destinations, and the requested worker.
   Terminated it on the stop condition. Last logged checkpoint: 325 completed,
   299 AEX successes, 23 AEX rejects, 3 AEX budgets; 86 both-route-exact,
   86 Classic exact / 238 refusal / 1 uncompared, 115 Smart exact / 209 refusal /
   1 uncompared, 0 pixel mismatch cases. No completed 500-case report exists.
   See `T01-radial-offset-fuzz-partial.log`. In the completed saved-corpus replay,
   PF8 cases with nonzero Outer Offset slot 6 number 5; their 10 routes all changed
   mismatch -> exact with this worker. A full seed-1 cluster comparison is NOT
   established by the interrupted campaign.

6. Reviewed the Offset, budget, and planes probes, existing public test helpers,
   `tests/test_radialblur_*`, and `tests/test_olmradialblur_*`.
   The runner's `offset.retained_cases()` is the existing cumulative 9,645-case
   union (NoOp adds 82 to the preceding 9,563). It would perform 57,870 retained
   replays. Those replays, separate historical tests, budget/plane probes, and a
   packaged Xcode build were not completed/run after the stop condition.
   Historical current-capture source identity is not updated to imply a pass.

7. Removed the previous worker's 3,869,794-byte unverified completion capture
   `reports/radialblur_offset_public_20261002.json`, restored the current-capture
   pointer to upstream's NoOp epoch, and removed the tracked machine-specific
   `aex` symlink. The promotion runner already resolves AEX via an absolute MAIN
   path when needed; fuzz uses MAIN in place. No MAIN/cache/emulator edits, no
   release-gate edits, no push, and no history rewrite. Scratch was 93 MiB after
   removing 35 disposable compiled executables, dSYM bundles, and interrupted
   fuzz build/work directories. `git diff --check` passed.

inference:

- The measured refusal blocks promotion and rebaselining under the ticket's
  explicit stop rule. Its attribution to Offset admission, F08 dispatch, or an
  already-existing upstream limitation is UNCONFIRMED: no pre-promotion replay
  of this single witness was performed after the stop condition.
- The two failing fuzz calibration anchors show that the 18 passing historical
  anchors do not establish worker equivalence for the fuzz corpus. Do not count
  its 58 improved routes as proven numerical fixes without resolving that boundary.
- No claim of 390/390, 9,645 preserved cases, native AE equivalence, or completed
  500-case fuzz coverage is made. The old worker's reported completion counts
  were not accepted as fresh evidence.

changed_files:

- `mac/OLMRadialBlur/OLMRadialBlur.cpp`: retained WIP Offset semantic candidate, automatically merged with F08/T05; blocked pending verification.
- `tools/emulation/probe_radialblur_offset_promote_20261002.py`: retained WIP reproduction runner, used without edits.
- `aex`: removed WIP absolute symlink.
- `reports/radialblur_offset_public_20261002.json`: removed unverified WIP capture.
- `tools/emulation/radialblur_current_public_20261001.py`: reverted WIP capture-pointer change to upstream.
- `orchestra/reports/T01-radial-offset-promote.md`
- `orchestra/reports/T01-radial-offset-corpus-replay.json`
- `orchestra/reports/T01-radial-offset-validation-partial.log`
- `orchestra/reports/T01-radial-offset-fuzz-partial.log`
- Other upstream files arrived only through the explicitly requested merge.

verify:

Run from this worktree; use fresh output paths on repeated runs. The first command
rechecks the blocking witness (expected replay difference/nonzero exit, Classic
516, Smart exact under this worker, calibration 4/6). The directory replay is
expected to reproduce the table above. These commands read MAIN assets in place.

```sh
export TMPDIR="$PWD/orchestra/state/T01-radial-offset-promote"
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
python3 tools/fuzz/run.py --plugin radialblur --worker "$worker" \
  --replay tests/fuzz_corpus/radialblur/seed1_case000425_df3690c920ab.json \
  --scratch orchestra/state/T01-radial-offset-promote/recheck-work \
  --report orchestra/state/T01-radial-offset-promote/recheck.json \
  > "$TMPDIR/recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --worker "$worker" \
  --replay tests/fuzz_corpus/radialblur \
  --scratch orchestra/state/T01-radial-offset-promote/recheck-corpus-work \
  --report orchestra/state/T01-radial-offset-promote/recheck-corpus.json \
  > "$TMPDIR/recheck-corpus.log" 2>&1
```

Exact long-run commands used (stopped, NOT expected-pass evidence). Resume only
after the orchestrator resolves the blocking witness/reference boundary:

```sh
python3 tools/emulation/probe_radialblur_offset_promote_20261002.py \
  --worker "$worker" \
  --worker-build /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/offset-timeout-reference-build.json \
  --output "$TMPDIR/merged-validation" --report "$TMPDIR/merged-validation.json" \
  > "$TMPDIR/merged-validation.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --worker "$worker" --n 500 --seed 1 \
  --scratch orchestra/state/T01-radial-offset-promote/merged-fuzz-work \
  --report orchestra/state/T01-radial-offset-promote/merged-fuzz500.json \
  --corpus orchestra/state/T01-radial-offset-promote/merged-fuzz-corpus \
  > "$TMPDIR/merged-fuzz500.log" 2>&1
```

next:

- Follow-up: replay the single PF32 odd-output-stride witness on upstream F08 and
  the Offset candidate to attribute the new refusal; do not edit its expectation.
- Reconcile the fuzz containment-worker PF32 hashes with the requested offset
  worker before treating corpus status improvements as numerical proof.
- Then complete 390 Offset cases and 57,870 retained replays, the requested tests,
  and all 500 seed-1 cases. Rebaseline only if every changed route moves toward exact.
