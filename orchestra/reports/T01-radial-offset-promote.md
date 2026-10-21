status: blocked

summary:
- Completed Round 6: Offset 390/390 exact (2,340 public replays) and retained 9,645/9,645 unchanged (57,870 replays), zero diffs/new rejections.
- Completed seed 1 n500 and fresh seed 2 n300 with --jobs 2; all 339 base-exact fuzz routes retain identical bytes.
- Four refusal→mismatch routes are outside Round 4's enumerated allowed set; none is a base-exact loss. Overall acceptance is not claimed.
- Replayed all 35 corpus cases against base and candidate; corpus-only transitions are allowed, but rebaselining is withheld because the whole campaign does not meet the allowed-set condition.
- Production remains the accepted Round-5 repair; this round changes only verification tools, reports and logs.

facts:

All requested measurements finished. The long gates were not stopped on the
unlisted transitions: Round 6 says to stop only on a forbidden change. A policy
clarification was requested during the run; no answer had arrived at report time.
The four unlisted transitions are not silently treated as allowed or mislabeled
as exact→non-exact. No corpus expectations, production code, ledger, release
gates, MAIN files or reference workers were changed in this round.

Bindings:

- Measured production / starting commit: `f842ed7d`; source SHA-256
  `bbe3731138805156ed487136e70dad5c39731fc560a284956b9f47e44d0297d8`.
- Measured base: `95b185eb`; source SHA-256
  `66ed2aeb5132e0a5670b3801a781e8d3e5a77c142533911c9b497b1b4b30db85`.
- Reference worker: `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`,
  SHA-256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`.
- Original AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Both candidate measurement switches were unset. F08/T05 and the Round-5 repair
  were already present; no additional merge or source replacement was needed.

`probe_radialblur_offset_promote_20261002.py --jobs 2` exited 0. It calibrated
18/18 recorded original-AEX hashes before using the worker, then used the existing
compiler helpers for ordinary O2, O2 with `-fno-fast-math -ffp-contract=off`, and
ASan/UBSan. Classic and Smart both match for all 390 Offset conditions. Every
retained route matches its recorded raw hash, error and callback metadata on
all three builds. The 19,290 recorded per-route errors are all zero. Total
candidate public gate replays: **60,210**, all exact.

E=exact, M=mismatch, R=refusal, U=uncompared. Retained-suite "before" means the
recorded previously-exact oracle; Offset "before" is the runner's measured
Classic build from `c841d478bf7b4ee7d1c29ccffef091d127bd40bb`. Fuzz and measured
corpus "before" mean `95b185eb`, using the same current worker as "after".
The subset/corpus rows overlap other rows and must not be added to a total.
Seed-1 counts below incorporate the explicitly recorded AEX timeout rechecks.

| Suite / route | Before | After | Candidate replays / cases |
| --- | --- | --- | --- |
| Recorded-AEX worker calibration | 18 recorded hashes | 18 exact | 18 AEX replays |
| Offset 390 (historical pre-Offset Classic) | 32 E / 16 M / 342 R | 390 E, both routes / all builds | 2,340 |
| Retained getters | 30 E | 30 E | 180 |
| Retained topology | 252 E | 252 E | 1,512 |
| Retained typed | 28 E | 28 E | 168 |
| Retained independent | 384 E | 384 E | 2,304 |
| Retained size_topology | 180 E | 180 E | 1,080 |
| Retained zoom_fade | 299 E | 299 E | 1,794 |
| Retained rotation_size_noise_independent | 96 E | 96 E | 576 |
| Retained size_range | 560 E | 560 E | 3,360 |
| Retained size_enabled | 720 E | 720 E | 4,320 |
| Retained noise_range | 952 E | 952 E | 5,712 |
| Retained seed_thickness | 1,532 E | 1,532 E | 9,192 |
| Retained quality | 2,262 E | 2,262 E | 13,572 |
| Retained gain | 1,140 E | 1,140 E | 6,840 |
| Retained strength | 1,128 E | 1,128 E | 6,768 |
| Retained noop | 82 E | 82 E | 492 |
| Retained total | 9,645 E | 9,645 E; 0 new rejections | 57,870 |
| Seed 1 n500 classic | 85 E / 1 M / 413 R / 1 U | 138 E / 2 M / 359 R / 1 U | 500 |
| Seed 1 n500 smart | 109 E / 390 R / 1 U | 184 E / 2 M / 313 R / 1 U | 500 |
| Seed 2 n300 classic | 63 E / 3 M / 234 R | 88 E / 3 M / 209 R | 300 |
| Seed 2 n300 smart | 82 E / 1 M / 217 R | 116 E / 2 M / 182 R | 300 |
| Corpus 35, measured base classic | 23 E / 1 M / 11 R | 23 E / 1 M / 11 R | 35 |
| Corpus 35, measured base smart | 35 E | 35 E | 35 |
| Corpus saved Classic | 24 M / 11 R | 23 E / 1 M / 11 R | 35 |
| Corpus saved Smart | 35 M | 35 E | 35 |
| Seed 1 PF8 Outer Offset != 0, each route | 5 E / 35 R | 21 E / 19 R | 40 per route (subset) |
| Seed 2 PF8 Outer Offset != 0, each route | 3 E / 16 R | 8 E / 11 R | 19 per route (subset) |
| Existing RadialBlur smoke tests | 10 pass / 1 existing failure | 10 pass / same 1 failure | 11 tests |

All four fuzz runs completed their requested counts with zero framework errors.
No base-exact route changed bytes. The PF8 Outer Offset slot-6 subset has zero
mismatches before and after with this calibrated worker; 16 additional seed-1
cases and 5 seed-2 cases become exact on each route. This is an admission
improvement, not a claim that all historically saved mismatch clusters were
caused by Offset: F08 and the reference-worker epoch also differ from old corpus
provenance. The adapter's older six-case calibration remains 4/6; the two old
PF32 bindings are not used as acceptance truth. The independent 18/18 recorded
calibration is the worker qualification for this ticket.

Timeout resolution (original campaign JSON remains untouched):

- Seed1 #421 was exact on base, but AEX hit the 10-second subprocess deadline in
  the candidate campaign. Both Mac raw hashes were already identical to base.
  A 120-second-deadline replay completed AEX in 10.740 seconds and proved both
  base/candidate routes exact: `ed17fb5a4d3aff849edf404db5f8a10f5850c36a5aefc3f607e2b2fd8ff92be7`.
- Seed1 #363 hit the AEX deadline in both campaigns. The longer replay completed
  in 9.707 seconds: base remains refusal, candidate is exact on both routes,
  `c8aeb32a63c24343b2e130fcf192b426e02193345159f9c66500eceed8142e4b`.
- Thus raw seed1 after counts 136 E/2 M/359 R/3 U Classic and
  182 E/2 M/313 R/3 U Smart resolve to the table. The comparator verifies input,
  source/worker bindings and every available original Mac hash before applying
  these additional observations. It does not rewrite campaign results or corpus.
- Unreduced #193 Classic/Smart and #425 Smart remain exact, including a fresh
  shared-oracle witness replay. #425 Classic remains the base's known mismatch.

First unlisted mismatch and remaining unlisted routes (fresh AEX succeeded with
intact output guards and clean sessions; every base guard is
`RenderZoomTyped:unadmitted-zoom-profile@2851`):

- Seed1 #89 Classic: PF32 17×21, nonfinite input, 827 differing bytes / 328 words,
  first byte 0; expected word `00000000`, actual `4623c1ff`.
  AEX `a4199f925d9557c8512c6a1fb087e88493b3888d77545a5fc55347a9fe9dc470`;
  Mac `1b3f15cd7c85c74a5e2cf37ebbbd1183d61b9bfdbc44e3462fd5991c5a70c6fa`.
- Seed1 #89 Smart: same 827 bytes, first byte 0, same AEX/Mac hashes.
- Seed1 #459 Smart: PF32 nonfinite input, 1,220 differing bytes / 375 words,
  first byte 64; expected `0000807f`, actual `4623c1ff`.
  AEX `a142bf9afaf09317a4a1ebdb90c8304690c633bd54fdee0d12674ea03b9ef753`;
  Mac `3472225128e8d27cd696247395b0eb5c36bc334181bedcccc0fb393abe3cfb1e`.
- Seed2 #217 Smart: PF32 72×1, nonfinite input, 142 differing bytes / 47 words,
  first byte 34; expected `0000807f`, actual `0000c07f`.
  AEX `ec8f1ac97a7e30ea21379c0c868161092a4bb6632a9a5f9b3ec85bd670ead978`;
  Mac `b1533640d1c92cc3426bb75856e342b78ce84516f5a767d6b8bd546d9abdb582`.

policy:

- **0 mismatch→refusal transitions** in either current fuzz campaign or measured
  corpus comparison. The earlier Classic #425 policy refusal is no longer present:
  the accepted Round-5 repair restores its base M→M behavior.
- **0 exact→non-exact or exact-hash changes** after the timeout witnesses.
- **4 refusal→mismatch transitions** are outside the enumerated allowed set.
  No approval is inferred from absence of an answer. The full measurement work is
  complete, but this report does not promote these new wrong outputs as accepted.

All 35 saved corpus files differ from the fresh replay result, but their measured
base/candidate route states and successful hashes are unchanged. Relative to saved
results, 58 route states move M→E, one stays M→M, and 11 stay R→R. Rebaseline was
not invoked; no corpus file was changed. This separates evidence collection from
changing saved expectations while the campaign has unlisted transitions.

The existing smoke runner exited 1: 11 tests, 10 pass, one pre-existing failure
`test_windows_control_types_and_ui_ranges_are_preserved`. It expects Thickness
`PF_Precision_HUNDREDTHS, 0, 0`; production has `0x40`. Round 5 already reproduced
that same assertion on `95b185eb`; neither source nor expectation changed here.
Generic, Type3 and budget sanitizer/world-contract checks passed. This is bounded
CPU-AEX/fake-SDK-host evidence, not new native Windows UCRT, native AE, GPU,
ROI/downsample or arbitrary-input conformance.

inference:

The Round-5 fallback preserves the base-exact cases, but its call to the current
`RenderZoomTyped` can also use the expanded generic Offset classifier.
`RenderWorld` checks SDR for generic admission; the inner `use_generic_baseline`
checks `IsGenericBaselineWorldPair` without that SDR check. On the three nonfinite
inputs, this appears to bypass the older `unadmitted-zoom-profile` refusal. This
is a source-level explanation consistent with the measured guards, not a new
instrumented internal-path proof. No numerical fix is attempted in this acceptance
round. The boundary warrants a follow-up preserving the base-exact odd-stride/HDR
cases while keeping newly unproven nonfinite profiles refused.

changed_files:

- `tools/fuzz/compare_radialblur_round6_T01.py`: base-relative transitions, exact
  hash retention, explicit unlisted transitions and hash-bound timeout rechecks.
- `tools/fuzz/verify_radialblur_round6_witnesses_T01.py`: reproducible unreduced
  seed/index witnesses against one shared AEX result and both source revisions.
- `tools/emulation/summarize_radialblur_round6_T01.py`: completed gate/suite,
  fuzz-route and corpus transition summary; saved corpus is read from `f842ed7d`.
- `orchestra/reports/T01-round6-*.json` and `T01-round6-*.log`: complete measured
  evidence, small normalized logs and artifact hashes. Each file is below 2 MB.
- `orchestra/reports/T01-radial-offset-promote.md`: this report.

verify:

From the worktree root, use a fresh scratch directory. These are the actual
commands with the scratch prefix changed from `round6` to `round6-recheck` and
report output moved into that scratch directory. Run long commands in background
with the shown logs. Gate and fuzz runners receive `--jobs 2`; the targeted
witness and smoke runners execute sequentially.

```sh
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
worker=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker
binding=/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/offset-timeout-reference-build.json
export TMPDIR="$PWD/orchestra/state/T01-radial-offset-promote/round6-recheck"
mkdir -p "$TMPDIR"
"$py" -u tools/emulation/probe_radialblur_offset_promote_20261002.py \
  --worker "$worker" --worker-build "$binding" --jobs 2 \
  --output "$TMPDIR/gates" --report "$TMPDIR/gates.json" > "$TMPDIR/gates.log" 2>&1 &
wait $!

for seed in 1 2; do
  n=500; limit=10
  if [ "$seed" = 2 ]; then n=300; limit=20; fi
  "$py" -u tools/fuzz/run_radialblur_baseline_T01.py \
    --baseline-revision 95b185eb --baseline-scratch "$TMPDIR/base$seed-source" \
    --plugin radialblur --n "$n" --seed "$seed" --jobs 2 --budget-minutes 120 \
    --case-timeout "$limit" --worker "$worker" --scratch "$TMPDIR/base$seed" \
    --corpus "$TMPDIR/base$seed-corpus" --report "$TMPDIR/seed$seed-base.json" \
    > "$TMPDIR/base$seed.log" 2>&1 &
  wait $!
  "$py" -u tools/fuzz/run.py --plugin radialblur --n "$n" --seed "$seed" \
    --jobs 2 --budget-minutes 120 --case-timeout "$limit" --worker "$worker" \
    --scratch "$TMPDIR/after$seed" --corpus "$TMPDIR/after$seed-corpus" \
    --report "$TMPDIR/seed$seed-after.json" > "$TMPDIR/after$seed.log" 2>&1 &
  wait $!
done
"$py" -u tools/fuzz/verify_radialblur_round6_witnesses_T01.py \
  --worker "$worker" --scratch "$TMPDIR/witnesses" --report "$TMPDIR/witnesses.json" \
  > "$TMPDIR/witnesses.log" 2>&1 &
wait $!
"$py" -u tools/fuzz/verify_radialblur_round6_witnesses_T01.py --seed 2 --indices 217 \
  --worker "$worker" --scratch "$TMPDIR/witnesses-seed2" \
  --report "$TMPDIR/witnesses-seed2.json" > "$TMPDIR/witnesses-seed2.log" 2>&1 &
wait $!
"$py" tools/fuzz/compare_radialblur_round6_T01.py \
  --before "$TMPDIR/seed1-base.json" --after "$TMPDIR/seed1-after.json" \
  --witnesses "$TMPDIR/witnesses.json" --report "$TMPDIR/seed1-comparison.json"
"$py" tools/fuzz/compare_radialblur_round6_T01.py \
  --before "$TMPDIR/seed2-base.json" --after "$TMPDIR/seed2-after.json" \
  --report "$TMPDIR/seed2-comparison.json"

"$py" -u tools/fuzz/run_radialblur_baseline_T01.py --baseline-revision 95b185eb \
  --baseline-scratch "$TMPDIR/corpus-base-source" --plugin radialblur \
  --replay tests/fuzz_corpus/radialblur --jobs 2 --budget-minutes 60 --case-timeout 20 \
  --worker "$worker" --scratch "$TMPDIR/corpus-base" --report "$TMPDIR/corpus-base.json" \
  > "$TMPDIR/corpus-base.log" 2>&1 &
wait $!
"$py" -u tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur \
  --jobs 2 --budget-minutes 60 --case-timeout 20 --worker "$worker" \
  --scratch "$TMPDIR/corpus-after" --report "$TMPDIR/corpus-after.json" \
  > "$TMPDIR/corpus-after.log" 2>&1 &
wait $!
"$py" tools/fuzz/compare_radialblur_round6_T01.py \
  --before "$TMPDIR/corpus-base.json" --after "$TMPDIR/corpus-after.json" \
  --report "$TMPDIR/corpus-comparison.json"
"$py" tools/emulation/validate_radialblur_tests_T01.py --report "$TMPDIR/tests.json" \
  > "$TMPDIR/tests.log" 2>&1 &
wait $!
git diff --check
```

Expected: gate exit 0, 18 calibration successes, 390 exact, 57,870 retained
replays; both fuzz seeds complete with zero framework errors; comparison exits
1 with `FORBIDDEN 0 / UNLISTED 3` for seed1 and `FORBIDDEN 0 / UNLISTED 1` for
seed2. Corpus replay exits 1 because saved results are stale, while the measured
base/candidate corpus comparator exits 0. Smoke exits 1 for only the same UI
assertion. AEX wall budgets can vary; the recorded raw campaign counts and the
longer-deadline witness counts remain separate. Do not suppress a new changed
hash or classify a new timeout as exact without an original-AEX observation.

For a fast evidence-only audit, rerun `python3 tools/emulation/summarize_radialblur_round6_T01.py`
against the committed reports: expected `SUMMARY 9645 57870 FORBIDDEN 0 UNLISTED 4`.
This audit does not render. `git diff --check` passes. New disposable builds and
frames are removed after packaging; ticket scratch stays well below 5 GiB.

next:

Resolve the four unlisted nonfinite refusal→mismatch routes, or obtain an explicit
policy decision for that transition. Keep #193 Classic/Smart and #425 Smart exact
while doing so. Then rerun acceptance and invoke `tools/fuzz/rebaseline_corpus.py`
only once every changed route is allowed. The completed 9,645 gate now provides
full evidence, rather than an interrupted retained-suite claim. Investigate the
pre-existing Classic mismatches and stale Thickness UI assertion separately.
