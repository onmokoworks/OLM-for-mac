status: done
summary:
- Restored radius-two IPP vector arithmetic and the missing PF16 Smart Bilateral filtering stage.
- All six N02 refusals are now Smart byte-exact; focused final validation: 1737 exact, 0 mismatches, 0 Mac-only refusals, 63 original timeouts.
- Default seed 1 n300 has 290 Smart exact, 8 original rejects, 2 original timeouts, and no baseline exact-to-non-exact regressions.
- All 461 retained cases are Smart-exact; both routes recorded. ref_vs_fast: 669 exact, 6 matching refusals, 0 mismatches.

facts:

Base: `41369ff07d1a785849597fe57f9b294cc0b3deb0`, branch
`orch/N03-distancegradation-bilateral-refusals`.
Original AEX SHA256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
F54b SHA256: `e9d99f8af2dc5582e4f2faa71211b5ec2af405d26598f483768e3406034deb10`.
Final production source SHA256:
`816a4ec2e5fc2c9c59e1396314c4dd6097bf530671885bc13aaef28ca84635da`.

Oracle scope is the original CPU AEX under Unicorn versus production Mac
EffectMain through the existing fake SDK host. No native AE/Windows or
all-input claim. No worker rebuild, MAIN modification, release-gate/ledger
change, other plugin change, push, stash, or history rewrite.

**Original nightly witnesses.** `N03-evidence/capture.py` runs F54b resident
Smart watches at IPP entry RVA `c2f0`, preserving original inputs and geometry.
All six baseline Mac calls refused; all six final calls succeed with zero
differing output words. Five enter IPP. `ac576b49` has Blur Mode 1 / Size 0 and
no IPP memory witnesses. Three other 1x1 witnesses have Bilateral Size 0,
which selects radius one. The remaining witnesses are radius two at 6x17 and
radius 2740 at 1x1. Captured IPP input is zero for all four 1x1 Bilateral cases.
The generic watch named `output` observes RDX, which at this ABI is the row
stride, **not an output pointer**; it is not used as output evidence.

**Radius-two boundary.** `leaf_trace.py` replays the F54b-captured 6x17 field
and an independent seed-26026 17x9 field through original IPP init `18000c280`
and filter `18000c2f0`, without arithmetic detours. Full arithmetic operand
streams, first-site snapshots, and all pre-division sums are retained. The
6x17 trace has 79 distinct arithmetic sites / 102 scalar divisions; the 17x9
trace has 231 sites / 60 scalar-or-vector divisions. Loader instruction counts
were 84304 and 55241 respectively.

`stages.py` instruments temporary copies of baseline and final production code:
- Baseline independent field: 57 differing output words. First word original
  LE `dc62493f`; first-output details and baseline bits are in `stages.json`.
- First vector block: baseline differs in 11/48 range weights, one numerator
  lane, and one denominator lane. Final code matches all 48 range weights,
  all three broadcast spatial weights, and both four-lane sums.
- Across the 153 independent pixels, baseline has 68 unmatched numerator/
  denominator pairs; final has zero. Pair multisets account for IPP temporary
  tile order; ordered final output is separately byte-compared and exact.
- All 102 nightly pixels' paired sums and ordered final output match both
  baseline and final. This witness's refusal was admission, not scalar math.
- Expanded direct-original matrix: 37 shapes / 4094 float words, zero differences,
  including widths 15/16/17/18/31/32/33 and heights 1/4/5/9.

Original `1806b7660..1806b7921` establishes the vector rule: range exponent
`(difference*difference)*-0.5f`, vector exponential `180ba5780`, distance-four
L/R/T/B traversal, squared-distance group order 1,4,2, and center added last.
Scalar ordering remains 4,2,1 with its existing distinct numerator/denominator
center positions. Products/additions preserve separate FLOAT32 rounding.
`disasm.txt` and `disassemble.py` retain/regenerate both bodies.

**Zero-field kernels.** `zero_trace.py` captures the original spatial tables,
range weights, and pre-division sums. Radius one has four captured range weights
of LE `0000803f`; numerator/denominator are `00000000` / `98455b40`.
Radius 2740's complete table has 23585590 words including the leading range
coefficient, with 150 nonzero words (149 spatial taps plus that coefficient).
Its table SHA256 is
`787279a0a1a405329b3f8fcc41736d548bc9bbd8d84154da8fb5431f7c6a61e9`.
The first generic range weight is `0000803f`; numerator/denominator are
`00000000` / `dd0fc940`. Both radii's sums and outputs match Mac exactly.
The complete table is streamed to gzip, not retained as a large in-memory dump.

The first large-radius diagnostic was terminated after discovering the shared
loader's reversed fast-hook bounds (trampoline `90000000` exceeds callback-end
`82100000`), which caused a Python callback on every instruction. The committed
probe narrows only that instance's host callback hook, checks normal return,
and reruns original arithmetic unchanged. The original loader and worker were
not edited. Its callback counts are explicitly not guest instruction counts.
An additional F54b indirect-body watch attempt was unhookable: the worker
reports that those bodies have no direct call sites. Those empty captures are
retained as a limitation, not evidence that a body was skipped.

**Additional PF16 cause found by the campaign.** Odd-even seed 26033 exposed
cases 121 and 172, both also failing on the untouched baseline:

| Case | Geometry | Baseline differing output words | First output word (original / Mac, LE) |
|---|---|---:|---|
| 121 | 100x4, downsample 1/2 x 1/3 | 36 | word 12: `ea22` / `e822` |
| 172 | 878x11, requested rectangle 702,4–758,5 | 7 | word 16: `b645` / `b745` |

`pf16_witness.py` captures the original typed field at the public memcpy boundary
(caller RVA `1171c65`). Case 121 has 40 differing staged words, first word 3:
original `a725`, Mac `a825`. `pf16_input.py` separately captures IPP input:
all 400 and 9658 FLOAT32 words match Mac's pre-filter field scaled by 32768.
Thus the field generation itself is exact at that measured boundary.

The previous Smart implementation skipped PF16 Bilateral. The original filters
its [0,32768] FLOAT32 plane before packing. Filtering even equal values can move
a half-integer packing tie by one FLOAT32 ULP. Applying the general IPP path at
that scale fixes both complete public outputs, all 400 staged words in case 121,
and all 878 captured staged words in case 172. Only one row was captured for
case 172; equality of its uncaptured typed rows is not claimed. The two explicit
inputs, baseline/final outputs, pre-filter captures and typed traces are retained.

**Acceptance execution and final-source binding.** Commands actually run:

- `sh orchestra/reports/N03-evidence/campaigns.sh v1` and
  `sh orchestra/reports/N03-evidence/campaigns.sh 'v2 odd'`, with jobs 1 and at most
  two active render/build processes. Each sampler ran seeds 26031/26032/26033,
  n200, all three depths. The wrapper forces only Blur Mode 5; other sampling
  remains unchanged. Odd-even uses max width 1920 / max height 1080.
- The initial full campaign identified the two PF16 mismatches above. After the
  PF16 fix, `python3 orchestra/reports/N03-evidence/revalidate.py` rebuilt the
  final Mac source and regenerated every input. It asserts full input hashes,
  parameters and geometry, then compares both output hashes to the **captured
  original AEX hashes**. It does not replace/recompute an original expectation.
  Original reports and their hashes remain alongside the final validation.

| Sampler | Seed | Final Smart exact | Original timeouts | Smart mismatch / Mac-only refusal |
|---|---:|---:|---:|---|
| realistic-v1 | 26031 | 196 | 4 | 0 / 0 |
| realistic-v1 | 26032 | 195 | 5 | 0 / 0 |
| realistic-v1 | 26033 | 192 | 8 | 0 / 0 |
| realistic-v2 | 26031 | 199 | 1 | 0 / 0 |
| realistic-v2 | 26032 | 196 | 4 | 0 / 0 |
| realistic-v2 | 26033 | 195 | 5 | 0 / 0 |
| odd-even-v1 | 26031 | 192 | 8 | 0 / 0 |
| odd-even-v1 | 26032 | 185 | 15 | 0 / 0 |
| odd-even-v1 | 26033 | 187 | 13 | 0 / 0 |

Totals: 1737 Smart exact, 63 uncompared original timeouts. Classic separately:
56 exact / 1744 mismatch. These are not Smart passes and were not repaired here.

- Standard `tools/fuzz/run.py --plugin olmdistancegradation --worker
  /Users/onmk/.cache/olm-emu/worker-F54b/aex-guest-worker --jobs 1 --seed 1 --n 300
  --shrink-attempts 0 --budget-minutes 90` (scratch/report/corpus under this ticket):
  Smart 290 exact, 8 original rejects, 2 original timeouts. Three Mac refusals
  coincide with original rejection; zero Mac-only refusals. Classic 10 exact /
  290 mismatch. Final-source revalidation preserves these comparable results.
- `default_baseline.py` compiles pinned baseline production code and evaluates
  all 600 Mac route calls against the same captured original hashes: 300 baseline
  exact route calls, zero exact-to-non-exact transitions, including final-source
  revalidation. Two initial harness builds failed on include-path assumptions;
  the committed script fixes those and completed successfully.
- `replay.py` replays all 461 retained corpus files using their original samplers,
  recording both original and Mac routes. `revalidate_replay.py` binds all those
  original output hashes to the final source: Smart 461 exact (454 exact retained,
  seven refusal→exact); Classic 123 exact retained and 338 mismatches retained.
  No saved corpus expectations were rewritten. Saved-result equality is false
  where refusals improved or recorded provenance differs; it is not a regression.
- `tools/perf/ref_vs_fast.py --plugin olmdistancegradation --jobs 1 --scratch
  orchestra/state/N03-distancegradation-bilateral-refusals/ref-vs-fast` completed
  its default 200 small / 20 HD / 5 UHD cases at thread caps 1/2/8:
  669 exact comparisons, 6 matching refusals, 0 mismatches.
- Final Python syntax checks and `git diff --check` pass.

Compressed reports retain all per-case results, both routes, build/source hashes,
first mismatches, original exclusions and failed intermediate findings.
`N03-evidence/summary.json` distinguishes initial campaigns from final validation.

inference:

The demonstrated PF32 radius-two discrepancy had two causes: vector exponential
selection and reduction grouping. Correcting only the former, as in N02, was
insufficient. PF16's additional discrepancy was the missing pre-pack filtering
stage, demonstrated with exact pre-filter inputs and unequal typed fields.

Bilateral's field derives from the recovered mask/EDT independently of later
source-channel composition. Admission reuses that composition and existing UCRT
Power; it does not redefine either. Finite-field zero spatial taps can be omitted
without changing the order of nonzero additions. This is a general arithmetic
rule, not a coordinate-specific or final-byte correction. Finite sampling does
not establish all-input compatibility; original timeouts remain unverified.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`: IPP radius-two vector arithmetic,
  PF16 Smart scaling/filtering, and Bilateral/Power/source admission.
- `orchestra/reports/N03-evidence/`: reproducible probes, explicit PF16 witnesses,
  original/Mac intermediate captures, campaigns, replays and compressed results.
- `orchestra/reports/N03-distancegradation-bilateral-refusals.md`.

verify:

From this worktree, serialized commands below stay within the process limit:

```sh
export TMPDIR="$PWD/orchestra/state/N03-distancegradation-bilateral-refusals"
mkdir -p "$TMPDIR"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
sh orchestra/reports/N03-evidence/campaigns.sh > "$TMPDIR/campaigns.log" 2>&1
sh orchestra/reports/N03-evidence/verify.sh > "$TMPDIR/verify.log" 2>&1
python3 orchestra/reports/N03-evidence/revalidate.py > "$TMPDIR/revalidate.log" 2>&1
python3 orchestra/reports/N03-evidence/revalidate_replay.py > "$TMPDIR/replay-final.log" 2>&1
python3 orchestra/reports/N03-evidence/collect.py > "$TMPDIR/summary.log" 2>&1
git diff --check
```

Expected: zero Smart mismatches and Mac-only refusals in completed comparable
campaign/default cases; zero default baseline regressions; all 461 retained Smart
cases exact; the direct 37-case matrix and final intermediate checks exact;
ref_vs_fast zero mismatches. Original timeout counts can vary with shared-machine
load and must remain explicit exclusions. Old saved refusal expectations stay
unchanged. Baseline diagnostics intentionally retain the documented failures.

next:

Retry the 63 focused original timeouts with an appropriate larger per-case budget.
Classic's recorded legacy mismatches and native AE/Windows validation remain
separate follow-ups. No further change is required for the demonstrated six
refusals or the two newly captured PF16 discrepancies.

Final housekeeping: regenerable native build directories were deleted; scratch
remains below 50 MiB. No ticket render/build process remains. All evidence and
reproduction scripts are committed with this report; the durable F54b oracle
continues to reside in its existing registered cache location.
