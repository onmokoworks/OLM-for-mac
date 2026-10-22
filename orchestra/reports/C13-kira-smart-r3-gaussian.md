status: done

summary:
- Closed non-unit Strength/opacity controls for the bounded scalar Alpha directional Gaussian Smart pipeline.
- Seed1 improves219/0/81→222/0/78; seed6 improves227/0/73→230/0/70; seed7 improves225/0/75→227/0/73.
- Previous exact Smart and all Classic campaign records persist;900 sanitized campaign routes and600 independent production conditions pass.
- All70 corpus inputs retain status/bytes;140 arithmetic route replays change0 samples; strict replay8/8.
- Length1, Highlight, approximation and non-SDR Gaussian inputs remain excluded. This is the ticket's third closed cluster.

facts:

Base `37c11c85`, branch `orch/C13-kira-smart-r3`. Machine evidence: `reports/fuzz/olmkirakira_smart_C13_gaussian.json`.
Final Mac source SHA256 `643a6d545a22e3aabf0003ea0b0d661e942b502ff5a29c23b1cfb290e32c07f8` binds to the production campaigns, matrices, final traces and audits. Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; unchanged retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Original/worker use the same absolute MAIN/retained paths documented in earlier cluster reports. No external rebuild, MAIN write, release-gate/ledger/other-plugin change, push or install.

| n300/jobs2 | Before E/M/R | After E/M/R | AEX Smart output/reject |
|---|---|---|---|
| seed1 |219/0/81|222/0/78|287/13|
| seed6 |227/0/73|230/0/70|291/9|
| seed7 |225/0/75|227/0/73|287/13|

The previous cluster's final campaigns supply the loop's same-revision remeasurement. Alpha/Mode3 had9 successful-oracle refusals across source profiles, versus8 Channel6/Mode2 cases. New seed1 exact indices67/195/216; seed6 indices155/191/296; seed7 indices62/261. No framework errors or admissions without an original output.

First divergent stages and general recovery:

1. Independent case166: PF32 7×11, Strength537%, scalar directional Gaussian. Source is exact. Seed first differs at word0: AEX `0253b83c`, Mac `0153b83c`;39 seed words differ. Final44 words/44 bytes differ, first word5 AEX `3aa64e3f`, Mac `3ba64e3f`. The original full caller/outer writer binds to public Smart. Reusing the original integer→float percentage multiplication,0.001f clamp and float powf constructor restores every captured high-level/helper stage and final output.
2. Independent case27: PF8 1×1, Strength97%. Source and seed happen to match, but the old strength==1 helper condition skips the tiny Gaussian path. First ray word0 is AEX `7c7b3d3e`, Mac `0000803f`; all4 output bytes differ, first `e7` versus `ff`. The corrected scalar Gaussian helper eligibility restores the ray, glow, composed and final output; original public binding passes.
3. The original Alpha constructor `18114edf0`, percentage builder `18114e860` and aggregation `18114fd90` are shared before/after the blur-mode dispatch. Their C07 recovered operations apply unchanged to this Gaussian branch: float percentage multiplication, clamped float powf, actual Brightness Gain even at Strength0, and reciprocal normalization for PF8 as well as the other depths. No Gaussian coefficient, warp, filter arithmetic or final-byte correction was changed.

The production predicate is deliberately narrower than the initial gate-off experiment: Alpha with no approximation, Mode3, no Highlight, and each active directional Length2–1000. It reuses the existing scalar workspace/budget/rotation/geometry/layout/default-ramp checks and finite SDR source requirement. Strength0–1000%, Glow0–10000%, Source0–100% are now admitted. Existing box recovery and Classic admission are preserved. The helper flag now recognizes the recovered scalar Gaussian constructor beyond unit Strength; percentage fields are materialized only after controlling parameters have been read on both public routes.

Gate-off experiment:288 control conditions are exact under ASan/UBSan. Its generated source is reproducible from the20-line `tools/emulation/fixtures/kirakira_gaussian_controls_C13.patch` against this cluster's base, and its hash matches the retained matrix. Final production independently repeats those288 conditions, another288 with default ramps/gains/rotations, and24 length-boundary conditions:600 exact comparisons. The first two matrices share generated source samples with varied settings; they are not claimed as600 unique pixel arrays. Geometries1×1/7×11/9×7, depths8/16/32, both merges, Strength{0,1,40,97,100,101,537,1000}, independent source/glow percentages, random colors, odd strides, Gain1/1.25/100 and rotations−31/0/22/359/45000000 are covered. The length matrix adds2/3/50/1000 at1×1 with Strength1/537.

Eight one-away cases refuse under sanitizers: Length1, Highlight1, approximation, unsupported channel, out-of-range Strength/Glow/Source and HDR Alpha. Existing Gaussian Length1 retains exactly its earlier one-word diagnostic mismatch at word217/byte868, AEX `5cf1563f`, Mac `5df1563f`; production refuses. The diagnostic test's PASS means preservation of that counterexample, not exact output.

| Corpus inputs | Before→after | Rebaseline |
|---|---|---|
| production8 + historical62 |70/70 identical production status and output|none needed|
| arithmetic140 routes |0 changed samples|none|

All900 final Smart campaign cases independently rerender under ASan/UBSan and agree with the ordinary builds. Every previous exact Smart result and all Classic records are unchanged. All70 production corpus comparisons pass; strict replay8/8. The25 fast tests pass; compiled generic sanitizer passes54 internal rows including HD in44.047 seconds. `git diff --check` passes.

inference:

The shared original constructor/builder/aggregation and public-bound first-stage traces support extending the recovered scalar operations to directional Gaussian. The independent matrices and preserved base outputs support the bounded promotion; they do not prove arbitrary native AE/UCRT, nonfinite/HDR Gaussian input, custom ramps, ROI/downsample, Gaussian Highlight or Length1. Host float powf imports remain explicitly distinct from native Windows UCRT.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/fixtures/kirakira_gaussian_controls_C13.patch`
- `reports/fuzz/olmkirakira_smart_C13_gaussian.json`
- `orchestra/reports/C13-kira-smart-r3-gaussian.md`
- `orchestra/reports/C13-kira-smart-r3.md`

verify:

```sh
s="$PWD/orchestra/state/C13-kira-smart-r3/recheck-gaussian"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 37c11c85:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 6 7; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 6 7 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
cp "$s/before.cpp" "$s/candidate.cpp"
patch "$s/candidate.cpp" < tools/emulation/fixtures/kirakira_gaussian_controls_C13.patch > "$s/patch.log"
python3 tools/emulation/probe_kirakira_smart_C07.py --source "$s/candidate.cpp" --family gaussian-controls --gate-off --require-exact --scratch "$s/gateoff" --report "$s/gateoff.json" > "$s/gateoff.log" 2>&1
for family in gaussian-controls gaussian-ramps gaussian-lengths; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
for index in 27 166; do
  "$py" tools/emulation/probe_kirakira_smart_C07.py --source "$s/before.cpp" --family gaussian-controls --trace-index "$index" --gate-off --scratch "$s/trace-before-$index" --report "$s/trace-before-$index.json" > "$s/trace-before-$index.log" 2>&1
  "$py" tools/emulation/probe_kirakira_smart_C07.py --family gaussian-controls --trace-index "$index" --require-exact --scratch "$s/trace-after-$index" --report "$s/trace-after-$index.json" > "$s/trace-after-$index.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family gaussian-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --family gaussian-length1 --scratch "$s/length1" --report "$s/length1.json" > "$s/length1.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --family gaussian-length1 --gate-off --scratch "$s/length1-diagnostic" --report "$s/length1-diagnostic.json" > "$s/length1-diagnostic.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/arithmetic" --report "$s/arithmetic.json" > "$s/arithmetic.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: campaign table,900 sanitized routes,70 unchanged corpus inputs,288 gate-off exact and288+288+24 production exact, two public-bound traces restored to exact,8 refusals, preserved Length1 mismatch,140 arithmetic routes/0 changed samples, replay8/8.

Existing test commands used, with ticket-local logs:

```sh
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast.log" 2>&1
PYTHONPATH=tests python3 - > "$s/sanitizer.log" 2>&1 <<'PYTEST'
import pathlib, unittest
import test_olmkirakira_generic_beta_sanitizers_20260820 as test
test.ROOT = pathlib.Path('/Users/onmk/Documents/Projects/Personal/OLM as')
r = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test))
raise SystemExit(not r.wasSuccessful())
PYTEST
```

next:
- Three-cluster stop condition met. Seed1 remaining78 refusals:13 without AEX output,65 with output.
- Largest remaining parameter/profile group is Channel6/Mode2 SDR (8), followed by Channel2/Mode2 SDR (6). Follow up on color constructors, active IPP resize, Gaussian Length1/Highlight and NaN propagation; do not infer native AE/UCRT closure.
