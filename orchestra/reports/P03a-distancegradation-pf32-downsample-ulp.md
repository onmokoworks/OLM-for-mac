status: done
summary:
- Restored the original embedded IPP square-root block arithmetic in DistanceGradation's EDT helper.
- All four reduced T15b Smart witnesses now match the original AEX exactly.
- Realistic odd-even seeds 2026/2027, n150 each: 292 exact, 0 mismatches, 2 P03b refusals, 6 unavailable.
- Paired pre-normalization intermediates and independent row-alignment probes match exactly.
- Default n300 has no regressions; all 382 corpus cases replay true; historical unit failures are unchanged.

facts:

Base: `bccd2e6f013e1964c8223542ad2ff2cd72a1c40c`, branch
`orch/P03a-distancegradation-pf32-downsample-ulp`. Read AGENT_GUIDE, the
DistanceGradation ledger row, GOTCHAS, compatibility plan, T15b and P02b.
No MAIN, AEXCompat, oracle binary, release-gate or ledger edit; no oracle rebuild.

Identities:

- Original AEX: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- F52c: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- F46: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
- Patched core: `ad3857f6b0b2af3afa42509ccb6d240763118234395a6ced557cb31888d75bb8`.

### First differing boundary

`P03a-evidence/probe.py` directly executes original `cvResize` (`0x1812aef70`)
and precise distance transform (`0x1812b15a0`) on the 12x8 witness's mask,
expanded to 96x64. The existing WindowsOpenCVRuntime supplies TLS/FLS and
allocation imports; **no OpenCV numerical operation is detoured**. A preliminary
probe with incomplete TLS initialization faulted at `0x181187e41`; switching to
the existing runtime scaffold resolved that setup error.

Measurements, recorded in `stages.json`, `compare.log` and
`core-before-comparison.json`:

- Expanded mask: 0 differences, SHA256
  `4f82651c45ed9ee1618d79fe515731efe7b84c717a8f2fce268d979c118446e7`.
- Original distance field: SHA256
  `21dbb396c1a4efacce9730fc444577b747f49b755eedaebc2499520196278242`.
- Baseline core, compiled from the base commit: 229/6144 differing words.
  First index 216 (x24,y2): original LE `fda5c240`, baseline `fea5c240`.
- Original resized field before normalization: SHA256
  `39d88fca61153c7007952c5fa35be6d63e6de3756b858f822c93e4595978070b`.
  Baseline arithmetic leaves 4/96 differing words, first (x5,y5):
  original `48994f41`, baseline `49994f41`.
- Applying the existing row-combine interpolation to the **original distance
  field** gives 0/96 differences. The resize formula is therefore unchanged.
- Patched production core pre-resize distance: 0/6144 differences.
- Eight independent sparse masks, widths 15/16/17/31/32/33/61/65, including
  unaligned row starts and scalar tails: 0/2215 differences against the actual
  embedded distance-transform function (`stage-matrix.json`).

### Binary arithmetic

`static.txt` records the actual `FUN_181449920` instructions and disassembly
hash. The entry aligns its destination with scalar SQRTSS, then handles 16
floats per block. Its regular path is:

```
r = RSQRTPS(squared)
p = float(squared * r)
c = float(float(r * p) - 3)
root = float(c * float(p * -0.5))
```

If any lane produces an exceptional exponent (zero input here gives a NaN
intermediate), **all sixteen lanes** fall back to SQRTPS. Tails use SQRTPS/SS.
The IplImage allocation uses alignment 4, so row starts depend on width.
The patch retains the existing squared-distance calculation and reproduces this
block traversal and separate FLOAT32 operations. It changes no threshold,
normalization, resize, dimension reconstruction, writer or admission rule.

The direct trace (`sqrt-trace.json`) observes 64 calls of width 96. RSQRTPS
initial estimates in this retained Unicorn environment equal FLOAT32
`1 / sqrtf(squared)`, including cases that differ from rounding
`1 / sqrt(double(squared))`. This distinction is measured, not an assumed
hardware approximation. The latter candidate estimate did not match; captured
register values established the corrected boundary. No two failed hypotheses
without a new boundary occurred.

### Public verification

The four corrected Smart output SHA256 values equal the unchanged original
AEX values in `witness.json.gz`. The corpus updates change only those four
candidate result expectations plus an explanatory field. Input pixels,
parameters, geometry, original hashes, and Classic expectations are preserved;
the historical mismatches remain in T15b's evidence.

Realistic campaign: `python3 orchestra/reports/P03a-evidence/sweep.py` runs the
same sampler, maximum width 1920 / height 1080, seeds 2026/2027, 150 cases each,
serially with F52c. Result: **292 exact / 0 mismatch / 2 refusal / 6 unavailable**.
The two refusals are precisely seed2026:index19 and seed2027:index143 at
`RenderBits:pf32-smart-bounded-sdr@2163`, reserved for P03b. Unavailable comprises
5 oracle rejections and 1 budget expiry. They are not counted exact.

Default `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1
--shrink-attempts 0` ran before and after with F46. Both runs have 290 Smart
exact comparisons and 10 unavailable original Smart results; Classic has 10
exact and 290 historical mismatches. Across 600 candidate route results, all 597 available output hashes are
unchanged, and the same 3 refusals have no output hash, with **0 exact-to-non-exact
regressions**. The raw summary also records 3 Smart refusals among unavailable
oracle cases; these are not Mac-only refusals. Full results are compressed in
`baseline.json.gz` and `candidate.json.gz`.

All corpus replays pass: **147/147 default, 226/226 P02b realistic, 9/9 T15b odd-even realistic** (382 total), each `replay_matches_saved: true`, through
standard `run.py` with each corpus's hash-bound worker. The verification driver
was edited while its shell was running; this interrupted it between corpus
commands with a shell read-offset/quote error. The final script passes `sh -n`;
the remaining two replay commands were resumed directly, without repeating
completed measurements.

Framework unit tests before/after: 31 tests, OK, 1 skipped. Plugin discovery
before/after: 140 tests, 15 failures, 59 errors. These are existing historical
failures, not a green full suite. Full logs are retained in the evidence.

inference:

- The T15b downsample dependency exposed larger all-positive distance blocks,
  reaching the IPP Newton path that the previous scalar square root omitted.
  Final-byte tuning or changing the resize coefficient is unnecessary.
- These are bit-exact original-AEX/retained-Unicorn results. Native Windows
  RSQRTPS estimates and native AE are not measured here; no native-hardware
  equivalence claim is made.

changed_files:

- `core/olmdistancegradation_fieldgen.cpp`: original block square-root staging.
- Four T15b DistanceGradation corpus JSONs: corrected Smart expectations.
- `orchestra/reports/P03a-evidence/`: reproducible probes, verification scripts,
  static excerpt, logs, comparisons and compressed campaign evidence.
- This report.

verify:

From this worktree, all temporary output remains under this ticket's scratch:

```sh
sh orchestra/reports/P03a-evidence/verify.sh
python3 orchestra/reports/P03a-evidence/sweep.py
python3 orchestra/reports/P03a-evidence/summarize.py
```

Expected: direct core/resize comparisons and the 8-mask matrix have zero
word differences; the four Smart witnesses are exact; sweep has 292/0/2/6 as
above, allowing oracle timeout variability without counting it exact. Historical
unit failures stay unchanged. All three corpus reports must have `replay_matches_saved: true` (147 + 226 + 9 cases); default exact-to-non-exact regressions must be zero.

Scratch measured 8.9 MiB before cleanup, below the 5 GiB limit; regenerable
build outputs were removed. No
background process remains. `git diff --check` and final script syntax checks pass.

next:

- P03b owns the two remaining nonfinite/HDR refusals.
- Native RSQRTPS/AE validation remains a separate compatibility boundary.
