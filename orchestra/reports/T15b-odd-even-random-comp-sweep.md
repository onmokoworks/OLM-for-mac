status: partial
summary:
- Completed seeds 2026/2027, n150 each, all ten plugins: 2677 E / 4 M / 5 R / 314 U.
- Added opt-in independent odd/even sizing, calibrated F52c completion bounds, and expanded test-host CLI size bounds; production code and acceptance rules are unchanged.
- All four admitted mismatches are DistanceGradation scaled PF32 field cases; all nine failures have reduced, separately labelled witnesses and source pointers.
- Standard replay matches all 38 saved cases on both routes (Classic only for Smoother v1); 100 default inputs / 200 route results are identical before/after.
- Conformance acceptance remains partial: the four admitted mismatches are not exact. No tolerance, final-byte correction, admission bypass, oracle rebuild, or release-gate change.

facts:

Starting commit `9f4fa21e3f327be6942cb9651c7955c64f013486`, branch
`orch/T15b-odd-even-random-comp-sweep`. Read AGENT_GUIDE, GOTCHAS, the relevant
ledger decision rows, compatibility plan, T15 and P02i/P02j reports. Original
AEX files are read from MAIN; MAIN and AEXCompat sources were not modified.
F52c worker SHA256:
`4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
Per-plugin AEX/candidate/source hashes are in `T15b-evidence/*-provenance.json`;
the final harness manifest is `framework-sha256.json`.

## Sampler and measured bounds

`--size-sampler odd-even-v1` is opt-in. Width and height use independent parity
draws, tiny/prime anchors (including 1, 2, 3), and independently selected size
bands. `--max-size` bounds width; optional `--size-max-height` bounds height.
Parameters/pixels are generated at those dimensions before realistic-v1 applies
its sampled ROI, request, padding, aspect and downsample. The existing
realistic-v1 sampler is unchanged. All three depths, all five symmetric ratios
1/1, 1/2, 1/3, 1/4, 1/8, and asymmetric X=1/2,Y=1/3 are present for every plugin.
Full-comp square/wide/tall/one-pixel-strip cases are present for every plugin.

For the 1920x1080-ceiling campaigns, widths are odd in 142/300 cases and heights
in 144/300; there are 11 square cases and 26 one-pixel strips. KiraKira has
142/140 odd widths/heights, 12 squares and 24 strips. Smoother2 has 142/139,
11 squares and 26 strips. These are observations, not forced parity balancing.
See `counts.json` for joint parity, depth, seed, downsample and shape coverage.

Calibration actually runs each original route at each depth with default
parameters, a fixed varying four-pixel SDR pattern, full output, zero padding,
and unit downsample/aspect. It probes squares from 1 through 4096 with bracket
refinement and separately tests 1920x1080. The retained oracle rejects dimensions
beyond 1920x1080, even before execution. PF32 full-HD Smart requests exhaust its
data arena; Smoother v1 does not advertise PF32. Complete trials, raw-output
hashes, statuses and measured seconds are in `*-calibration.json`.

**Bounded measurement limitation:** the bounds below are the largest tested
successful sizes in this calibration, not a proof of a global maximum across
all rectangular dimensions, inputs or controls. Timing is non-monotonic:
Smoother2 PF8 620x620 took 9.9716 s, 622x622 took 1.8669 s, 623x623 took 6.1539 s,
and 624x624 timed out. The ten-second timeout is never extended. Parameters in
the randomized sweep can time out below the calibrated ceiling. A denser
rectangular performance search remains follow-up work if a literal global
maximum is required.

| Plugin | PF8 largest tested success (s) | PF16 (s) | PF32 (s) |
|---|---|---|---|
| colorkeep | 1920x1080 (0.2145) | 1920x1080 (0.1994) | 1080x1080 (0.1970) |
| olmblur | 1920x1080 (3.5381) | 1920x1080 (3.6476) | 1080x1080 (1.8984) |
| olmcolorkey | 1920x1080 (0.8853) | 1920x1080 (0.6843) | 1080x1080 (0.2513) |
| olmdirectionalblur | 1920x1080 (0.0504) | 1920x1080 (0.0859) | 1080x1080 (0.0933) |
| olmdistancegradation | 1920x1080 (1.7485) | 1920x1080 (1.2451) | 1080x1080 (0.9041) |
| olmkirakira | 1080x1080 (5.4255) | 1080x1080 (5.4243) | 1080x1080 (5.2498) |
| olmsmoother | 1920x1080 (3.2620) | 1920x1080 (3.3512) | unsupported at 1x1 |
| olmsmoother2 | 623x623 (6.1539) | 623x623 (6.1559) | 623x623 (6.2177) |
| olmtoondilate | 1920x1080 (0.5499) | 1920x1080 (0.6165) | 1080x1080 (0.2296) |
| radialblur | 1920x1080 (0.0572) | 1920x1080 (0.0976) | 1080x1080 (0.0886) |

## Sweep counts

E = byte-and-rectangle exact against the valid original route. M = admitted
pixel/rectangle mismatch. R = Mac refusal while the original completes. U = no
valid original comparison (never counted exact). All final U cases are oracle
failures; the preliminary Mac test-host exit-64 failures were rerun after the
host bound was expanded. Smart is the counted route except Smoother v1 Classic.

| Plugin | E/M/R/U | 2026 | 2027 | Full-comp ceiling |
|---|---|---|---|---|
| olmcolorkey | 285/0/0/15 | 142/0/0/8 | 143/0/0/7 | 1920x1080 |
| olmdirectionalblur | 295/0/1/4 | 148/0/1/1 | 147/0/0/3 | 1920x1080 |
| colorkeep | 300/0/0/0 | 150/0/0/0 | 150/0/0/0 | 1920x1080 |
| olmblur | 300/0/0/0 | 150/0/0/0 | 150/0/0/0 | 1920x1080 |
| olmtoondilate | 300/0/0/0 | 150/0/0/0 | 150/0/0/0 | 1920x1080 |
| olmsmoother2 | 157/0/0/143 | 81/0/0/69 | 76/0/0/74 | 623x623 |
| olmsmoother | 188/0/0/112 | 92/0/0/58 | 96/0/0/54 | 1920x1080 |
| olmdistancegradation | 288/4/2/6 | 144/1/1/4 | 144/3/1/2 | 1920x1080 |
| olmkirakira | 297/0/1/2 | 149/0/0/1 | 148/0/1/1 | 1080x1080 |
| radialblur | 267/0/1/32 | 131/0/0/19 | 136/0/1/13 | 1920x1080 |

| Plugin | odd/odd | odd/even | even/odd | even/even |
|---|---|---|---|---|
| olmcolorkey | 67/0/0/6 | 69/0/0/0 | 67/0/0/4 | 82/0/0/5 |
| olmdirectionalblur | 72/0/0/1 | 66/0/1/2 | 71/0/0/0 | 86/0/0/1 |
| colorkeep | 73/0/0/0 | 69/0/0/0 | 71/0/0/0 | 87/0/0/0 |
| olmblur | 73/0/0/0 | 69/0/0/0 | 71/0/0/0 | 87/0/0/0 |
| olmtoondilate | 73/0/0/0 | 69/0/0/0 | 71/0/0/0 | 87/0/0/0 |
| olmsmoother2 | 36/0/0/37 | 38/0/0/31 | 29/0/0/37 | 54/0/0/38 |
| olmsmoother | 49/0/0/24 | 40/0/0/29 | 49/0/0/22 | 50/0/0/37 |
| olmdistancegradation | 70/1/2/0 | 65/2/0/2 | 70/0/0/1 | 83/1/0/3 |
| olmkirakira | 73/0/0/1 | 68/0/0/0 | 66/0/0/0 | 90/0/1/1 |
| radialblur | 67/0/0/6 | 63/0/0/6 | 58/0/1/12 | 79/0/0/8 |

| Plugin | 1/1 | 2/2 | 3/3 | 4/4 | 8/8 | 2/3 |
|---|---|---|---|---|---|---|
| olmcolorkey | 43/0/0/4 | 54/0/0/1 | 44/0/0/3 | 51/0/0/3 | 52/0/0/1 | 41/0/0/3 |
| olmdirectionalblur | 45/0/0/2 | 54/0/0/1 | 46/0/1/0 | 53/0/0/1 | 53/0/0/0 | 44/0/0/0 |
| colorkeep | 47/0/0/0 | 55/0/0/0 | 47/0/0/0 | 54/0/0/0 | 53/0/0/0 | 44/0/0/0 |
| olmblur | 47/0/0/0 | 55/0/0/0 | 47/0/0/0 | 54/0/0/0 | 53/0/0/0 | 44/0/0/0 |
| olmtoondilate | 47/0/0/0 | 55/0/0/0 | 47/0/0/0 | 54/0/0/0 | 53/0/0/0 | 44/0/0/0 |
| olmsmoother2 | 24/0/0/23 | 25/0/0/30 | 30/0/0/17 | 29/0/0/25 | 28/0/0/25 | 21/0/0/23 |
| olmsmoother | 30/0/0/17 | 34/0/0/21 | 29/0/0/18 | 30/0/0/24 | 32/0/0/21 | 33/0/0/11 |
| olmdistancegradation | 46/0/1/0 | 55/0/0/0 | 47/0/0/0 | 45/3/0/6 | 51/1/1/0 | 44/0/0/0 |
| olmkirakira | 45/0/0/2 | 55/0/0/0 | 47/0/0/0 | 54/0/0/0 | 52/0/1/0 | 44/0/0/0 |
| radialblur | 40/0/1/6 | 52/0/0/3 | 45/0/0/2 | 46/0/0/8 | 51/0/0/2 | 33/0/0/11 |

The second table is **full-comp width parity / height parity**. The third table
uses X/Y denominator labels: `2/3` means downsample X=1/2, Y=1/3; `4/4` means
X=Y=1/4. Every cell is E/M/R/U. Raw per-case parameters, geometry, input hash,
output hashes, first differences and refusal traces are in `*-cases.jsonl`.

Unavailable results (314 total): ColorKey 14 original guard rejections + 1 wall
timeout; DirectionalBlur 4 timeouts; Smoother v1 112 unsupported-PF32 rejections;
Smoother2 143 VCRUNTIME exception-owned-string allocation failures (51/49/43
at three recorded addresses); DistanceGradation 5 original OpenCV Median
assertions + 1 timeout; KiraKira 1 OpenCV resize assertion + 1 IPP exception;
RadialBlur 26 original invalid-memory-write failures + 6 timeouts. None are
silently reclassified as candidate correctness. First diagnostics are retained
in `counts.json` and all diagnostics in the per-case files.

## Each mismatch and each Mac-only refusal

No production change was made. The failure domain and source boundary are
identified below; an exact original intermediate arithmetic cause is **not**
claimed for DistanceGradation. Source pointers distinguish an observed refusing
guard from an investigation target.

### DistanceGradation: four admitted PF32 scaled-field mismatches

All four reduce to Inside, Linear, no blur, finite/binary source samples, with
non-unit downsample. Thus the original generated `nonfinite`, Gaussian and
Bilateral profiles are not sufficient causal classifications. Each original
case and its independently reduced witness are saved. The first differing
four-byte words below are **little-endian raw hex**, not decimal tolerances.

| Seed:index | Initial sampled size | Reduced size | First byte (reduced) | Original / Mac word | Differing words |
|---|---|---|---|---|---|
| 2026:16 | 365x64 | 365x64 | 0 | 24ea213f / 25ea213f | 7613 |
| 2027:54 | 246x175 | 61x43 | 9360 | 8c3ba33e / 8a3ba33e | 1 |
| 2027:99 | 422x256 | 211x128 | 2400 | 8ab2ae3e / 89b2ae3e | 5 |
| 2027:118 | 12x8 | 12x8 | 1040 | c291c33e / c091c33e | 4 |

First initial mismatch: seed 2026/index 16, full comp 1459x256, sampled 365x64,
PF32, X=Y=1/4; byte 0 original `24eaa13e`, Mac `25eaa13e`, 8785 differing bytes /
8767 differing words. Input after reduction SHA256:
`96301ebda0b68a3237fc27de995142dc926c9ed47b107df654f7cb3fdeec3156`.
The 365x64 witness did not accept the attempted geometric crops, but accepted
parameter and binary-pixel simplification. Reductions are bounded greedy
searches, not global-minimum claims.

`probe_T15b_boundaries.py` changes only downsample to 1/1 and full comp to the
unchanged sampled dimensions, preserving pixels, parameters, ROI and padding.
**All four reduced mismatches become Smart exact.** Results are in
`olmdistancegradation-boundaries.json`.

Source investigation pointers: `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2141`
reconstructs dimensions; `:1245` dispatches the field helper;
`core/olmdistancegradation_fieldgen.cpp:114` expands the mask and performs EDT,
`:125` begins the linear-resize path, `:138` combines float rows, and `:159`
normalizes the result. The smallest retained witness is 12x8 at 1/8. The
emulator comparisons expose final raw output, not paired intermediate fields.
The evidence narrows the boundary to scaled field staging; it does not justify
changing sqrt, normalization, resize arithmetic, or final words in isolation.
This respects the ledger's ban on broad EDT/writer retuning from residuals.

### Five Mac-only refusals

- **DirectionalBlur 2026:87**: first sampled 3x350, PF32 nonfinite, 1/3; original
  succeeds, Mac 516 at `RenderWorld:pf32-neutral-nonfinite-input@1815`.
  Reduced **1x5**, 40 attempts. Input SHA256
  `bf4827a4b5918b5c2622958cbc3b0c952908aecb9a521e8c984949c8b9ea8ac8`.
  The guard at `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:1815` explicitly
  requires finite input for the neutral path. Replacing only four nonfinite
  source lanes with 0.5 makes Smart exact; Classic remains a mismatch in that
  diagnostic variant. This is a nonfinite-admission gap, not a proven size bug.
- **KiraKira 2027:15**: first sampled 2x43, PF32 nonfinite, 1/8, output [0,5,1,13];
  original succeeds, Mac 516 at `SmartRender:tuple-or-source@2933`.
  Reduced **1x1**, 5 attempts. Pixel words are alpha 0.5, red 0.14362265,
  green 0.73575038, blue qNaN `0x7fc12345`; input SHA256
  `4a8eeadc8cded383cbe411bbf5eeab49939600224db5f3312851c08f897dc9fa`.
  Channel=5, Blur Mode=2. Admission composes the finite and Alpha exceptions
  at `mac/OLMKiraKira/OLMKiraKira.cpp:2925`; the finite color check at `:2128`
  excludes the NaN. Replacing only blue with 0.5 makes Smart exact (Classic
  still refuses). This is the nonfinite color pipeline boundary.
- **DistanceGradation 2026:19**: first sampled 1x5, PF32 HDR, 1/1, Gaussian
  Size=2696, Power=2.8936142765928246. Original succeeds, Mac -1 at
  `RenderBits:pf32-smart-bounded-sdr@2163`. Reduced **1x1**, 40 attempts, retaining
  HDR RGB up to 7.34663724899292, Gaussian 2696 and Power 1.236701784574103.
  Input SHA256 `f3571d6827cdf833d95a32f911e2ed95e3b6b0eac1fc245ed805503a5f27023d`.
  The extended-range predicates at `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2057`
  do not admit this Power/blur combination. Setting only Power=1 enters the
  existing Linear normalization at `:2159` and becomes exact, with the same
  HDR pixels and odd padding. This rules out odd padding as a sufficient cause.
- **DistanceGradation 2027:143**: PF32 nonfinite Bilateral-0, same guard `:2163`.
  Reduced **3x1**, 25 attempts. Input SHA256
  `181ded9e2c876487879862f34d12d74431a97f7af3c348b92bf63d1067ee6681`.
  The nonfinite restriction at `:2052` only permits the unblurred admission
  predicate; Bilateral is excluded there even at radius zero. Replacing only
  nonfinite lanes by 0.5 makes Smart exact. No filter or admission rule changed.
- **RadialBlur 2027:104**: first sampled 30x19, PF32 nonfinite, 1/1, Rotation;
  Mac 516 at `RenderRotationTyped:generic-size-variation-topology@3762` while
  original succeeds. Reduced **1x4**. `BuildRadialSizeFactorPlaneAEX` at
  `mac/OLMRadialBlur/OLMRadialBlur.cpp:1798` rejects nonfinite alpha before
  component labelling; `:3762` reports that failed topology construction.
  Replacing only the one nonfinite alpha lane by 0.5 makes Smart exact; RGB,
  parameters and geometry stay fixed. Classic still refuses in that variant.

All refusal boundary experiments retain full before/after results in
`*-nonfinite-boundary.json` or `olmdistancegradation-boundaries.json`. They
change test inputs, not production source or acceptance. No two failed repair
hypotheses were pursued; the stop condition was not triggered.

## Default regression, corpus replay and commands actually run

Before editing generation, captured hashes of 300 default cases per plugin
(seeds 2026/2027), including all parameters/metadata and input pixel hashes.
`test_sizes` confirms all 3000 are identical after the changes. It also checks
parity/tiny/prime/strip coverage and embedded/procedural replay, including
legacy procedural replay when the caller enables the new sampler.

The preliminary ColorKey/DirectionalBlur square campaigns and first wide
ColorKeep/DirectionalBlur runs exposed test hosts' old 256-pixel command-line
caps. Those preliminary files are scratch only and not part of the final
3000 counts. Expanded the host CLI bound to 4096; production world/admission
checks remain in place. Every default generated dimension remains <=256.
`verify_sizes_T15b.py` builds both the former 256-bound host and current host
without modifying production files, then compares seed 2026/n10 **complete
result objects on both routes**, using F52c. All are identical; zero
exact-to-nonexact transitions. These are bounded regression results, not a
claim of rerunning every historical corpus.

| Plugin | Default counted-route before E/M/R/U | After | Both-route objects identical |
|---|---|---|---|
| colorkeep | 10/0/0/0 | 10/0/0/0 | True |
| olmblur | 10/0/0/0 | 10/0/0/0 | True |
| olmcolorkey | 10/0/0/0 | 10/0/0/0 | True |
| olmdirectionalblur | 10/0/0/0 | 10/0/0/0 | True |
| olmdistancegradation | 9/0/0/1 | 9/0/0/1 | True |
| olmkirakira | 10/0/0/0 | 10/0/0/0 | True |
| olmsmoother | 6/0/0/4 | 6/0/0/4 | True |
| olmsmoother2 | 10/0/0/0 | 10/0/0/0 | True |
| olmtoondilate | 10/0/0/0 | 10/0/0/0 | True |
| radialblur | 10/0/0/0 | 10/0/0/0 | True |

Commands actually run, with logs redirected inside this ticket:

- `python3 tools/fuzz/sweep_T15b.py --plugin NAME --jobs 1` for every plugin;
  final run n150 per seed. At most two serial plugin drivers ran concurrently;
  neither used more than one emulator/build process at a time.
- `tools/fuzz/validate_T15b.sh NAME ...` for all ten plugins. This runs the
  before/after checks, saves depth anchors, and invokes standard `run.py
  --replay --geometry realistic --jobs 1` with the saved size ceiling.
- `python3 tools/fuzz/probe_T15b_boundaries.py` for all six DistanceGradation
  reduced witnesses; every input-only boundary changed the Smart result to exact.
- `PYTHONPATH=tools/fuzz python3 -m unittest test_sizes test_geometry
  test_framework test_route_oracles`: **31 tests, OK, 1 skipped**. The complete
  small log is committed at `T15b-evidence/unit-tests.log`.
- `python3 tools/fuzz/summarize_T15b.py`; `git diff --check`: passed.

The separate labelled corpus is
`tests/fuzz_corpus/<plugin>/T15b-odd-even-realistic/`: **38 cases** = all nine
reduced failures plus 29 successful depth anchors (Smoother v1 only 8/16).
Every original oracle call for these saved witnesses finishes within ten
seconds. No timeout witness is saved. Standard replay reports
`replay_matches_saved: true` for all ten plugins, **38/38**. It compares both
routes except geometry-qualified Smoother v1, whose original has only Classic.
A matching saved mismatch/refusal establishes reproducibility, not acceptance.
Old corpus expectations were not edited. All generated builds were removed;
scratch finished at about 7.2 MiB, far below 5 GiB. No background process was left.

inference:

- P02i/P02j geometry fixes survive this broader campaign; their remaining
  failures are original-oracle limitations and a distinct nonfinite neutral
  admission guard, respectively.
- DistanceGradation has a scaled-field arithmetic/staging gap. The four
  independently reduced linear/no-blur witnesses and their exact unit-scale
  controls isolate a useful boundary, but do not identify the original first
  differing intermediate instruction. A numerical kernel patch is not yet
  justified as a clear local size/rounding repair.
- The five Mac-only refusals require source-domain/parameter interaction work,
  not removal of a geometry cap. Bypassing them would not satisfy exactness.
- Smoother2's 143 unavailable results limit the meaningful ROI coverage; they
  cannot be promoted by the successful Mac output alone.
- The opt-in sampler and harness changes preserve sampled default behavior;
  no all-input or native-AE exactness claim is made. Four admitted mismatches
  mean this ticket does not pass the all-admitted-exact acceptance bar.

changed_files:

- `tools/fuzz/sizes.py`, `run.py`, `core.py`: versioned size sampling, CLI,
  procedural corpus reconstruction.
- `tools/fuzz/adapters/{public,radialblur,olmdirectionalblur,olmsmoother2}.py`:
  optional generation dimensions and test-host bounds.
- `tools/fuzz/harnesses/{blur,colorkeep,distancegradation,kirakira,smoother,toondilate}_main.cpp`:
  only test-host CLI upper bounds.
- `tools/fuzz/{sweep_T15b,verify_sizes_T15b,probe_T15b_boundaries,summarize_T15b,test_sizes}.py`,
  `validate_T15b.sh`, `README.md`.
- `tests/fuzz_corpus/*/T15b-odd-even-realistic/*.json` (38).
- `orchestra/reports/T15b-evidence/*` and this report.
- No production plugin/core, release gate, ledger, oracle source/binary or MAIN change.

verify:

Read-only expectation check, from the worktree (does not regenerate saved results):

```sh
export TMPDIR="$PWD/orchestra/state/T15b-odd-even-random-comp-sweep"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
export OLM_FUZZ_TEST_SCRATCH="$TMPDIR"
mkdir -p "$TMPDIR"
PYTHONPATH=tools/fuzz python3 -m unittest test_sizes test_geometry test_framework test_route_oracles > "$TMPDIR/recheck-units.log" 2>&1
for plugin in olmcolorkey olmdirectionalblur colorkeep olmblur olmtoondilate olmsmoother2 olmsmoother olmdistancegradation olmkirakira radialblur; do
  maximum=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["maximum"])' "orchestra/reports/T15b-evidence/$plugin-summary.json")
  python3 tools/fuzz/run.py --plugin "$plugin" --geometry realistic --jobs 1     --size-sampler odd-even-v1 --max-size "$maximum"     --replay "tests/fuzz_corpus/$plugin/T15b-odd-even-realistic"     --scratch "$TMPDIR/recheck-$plugin" --report "$TMPDIR/recheck-$plugin.json"     > "$TMPDIR/recheck-$plugin.log" 2>&1 || exit 1
done
git diff --check
```

Expected: 31 tests OK/one skipped; all ten replay reports true, 38 cases total,
including the four saved DistanceGradation mismatches and five refusals. Rebuild
and recalculate the complete campaign if desired with `sweep_T15b.py --plugin
NAME --jobs 1`, then `validate_T15b.sh NAME` and `summarize_T15b.py`; these
commands intentionally regenerate ticket evidence. Existing calibration files
pin the measured generation ceilings for reproducibility. Wall-time availability
can vary; preserve and report changes instead of rewriting them as exact.

next:

- Proposed **DistanceGradation scaled PF32 field** ticket: obtain paired original
  mask/expanded EDT/resized field/normalization words for the 12x8 and 61x43
  witnesses, locate the first arithmetic divergence, and fix general code.
  Preserve the four saved failures and exact unit-scale controls; do not apply
  a final-word correction or a tolerance.
- Proposed **DistanceGradation extended-source admission interactions** ticket:
  HDR Power+Gaussian and nonfinite Bilateral-0, starting from both reduced
  refusal witnesses and their exact boundary controls.
- Proposed **DirectionalBlur nonfinite neutral**, **KiraKira nonfinite color
  box**, and **RadialBlur nonfinite-alpha size topology** tickets. Reconstruct
  original arithmetic before broadening admission.
- Proposed **oracle ROI/exception coverage** ticket: Smoother2's VCRUNTIME
  failures first; retain ColorKey guard corruption, original Median assertions,
  KiraKira exceptions and RadialBlur invalid writes as separate limitations.
  No oracle rebuild was permitted here.
- A denser rectangular/input-dependent calibration is required to establish
  stronger maximum-size claims than this bounded largest-tested-size search.
