# Public-path random differential fuzzing

```sh
python3 tools/fuzz/run.py --plugin radialblur --n 2000 --seed 1 --jobs 4 --budget-minutes 30
```

Requires macOS arm64, Xcode command line tools, the existing AE SDK links
(`Headers`, `Util`, `Resources`) in MAIN, the original AEX in MAIN, and a retained
AEXCompat worker. Set `OLM_AEX_WORKER=/absolute/path/to/aex-guest-worker` or use
`--worker`. The workstation's retained October 6 containment worker is a fallback;
its SHA-256 is always recorded. `--main` overrides the automatically detected MAIN
checkout. Assets are read in place. Production source comes from this worktree.

The runner reuses the RadialBlur public probes' parameter serializer, Point API
conversion, SDK EffectMain harness and compiler helper. The generator reads legal
ranges, defaults and popup choices from the existing captured AEX declarations
and checks them against live PARAMS_SETUP. It samples sparse and dense changes,
small/degenerate and occasional up-to-256 geometries, all three depths, random
SDR pixels, transparent/semitransparent alpha, and PF32 HDR/signed/NaN/inf bits.
PF16 SDR uses AE's 0..32768 units. PF_Fixed Point sampling covers -1..2 frame extents;
Angle sampling covers +/-720 degrees. These are bounded legal subsets, not a claim
of exhaustive input coverage. Noise Layer is None; the Layer popup is still sampled.

Each case runs the original AEX's CPU Smart path under Unicorn, then production
Mac Classic and Smart in the fake SDK host. Mac worlds have independently random
byte padding (including odd strides); AEX session worlds are packed. Compare only
active raw ARGB bytes, including NaN payloads and signed zero. No tolerance.
Source, AEX, worker, harness, generator and calibration hashes accompany results.
Host math imports and six matching calibration cases do **not** establish native
Windows UCRT or AE equivalence. Signature clusters are not proven causes.

Reports go to `reports/fuzz/radialblur_YYYYMMDD.json`; counterexamples go to
`tests/fuzz_corpus/radialblur/`. `--report` and `--corpus` override destinations
inside the worktree. Rerunning the same date overwrites that report. An explicit
corpus directory lets campaigns stay separate. Each mismatch gets bounded greedy
reduction: crop geometry (scale Center), restore/default or halve controls, simplify
pixels. Every accepted reduction must preserve all initially mismatching routes.
The report records attempts/outcomes; reductions are not guaranteed globally minimal.
The public session pair exposes no corresponding intermediate stages, so RadialBlur
records raw diff counts and the first differing word. It does not infer a stage.

Corpus JSON embeds compressed input up to 32 KiB; larger inputs regenerate from the
seed and accepted operations. No large images or binaries are saved. Replay:

```sh
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur/CASE.json --report orchestra/state/T02-fuzz-framework-radialblur/replay.json
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
```

Pass a directory to `--replay` to verify every corpus JSON with one build.
Replay exits nonzero if raw hashes/statuses differ. Tests without the environment
flag skip the real worker integration test. Seed+index determine cases independently
of job completion order. Wall budgets can change which cases finish or how far
shrinking gets. `--case-timeout` defaults to 10 seconds per subprocess;
`--shrink-attempts 32 --shrink-seconds 10` bound each reduction. `--jobs` limits
concurrent subprocesses; the campaign deadline includes build/calibration and kills
process groups. Partial reports retain completed/attempted rows. Pixel mismatches
exit zero (measurement succeeded); setup/framework errors exit 2. AEX rejects and
budgets, Mac refusals/budgets/errors, and uncompared outputs have separate counters.
A public Mac error does not reveal whether its internal cause was a work budget or
unsupported controls; the original PF_Err is retained without inventing a reason.

Scratch is confined to this worktree's `orchestra/state/T02-fuzz-framework-radialblur/`
(or `--scratch` under `orchestra/state/`), never `/tmp`. Child TMPDIR follows it.
Each replay uses a fresh disposable directory, including the worker's exclusive
sidecars. Build outputs and case worlds are deleted on completion. Admission rejects
scratch already above 4 GiB; at most 32 bounded 256x256 cases are live at once.

## Add a plugin

Write only `tools/fuzz/adapters/NAME.py` exporting `Adapter(options)`. Implement
`name`, `generator_version`, `routes`, `max_size`, `prepare(scratch, deadline)`
(return provenance), `defaults(w,h)`, `generate(seed,index)`,
`oracle(case,dir,deadline)` and `candidate(case,dir,route,deadline)` (return status
metadata plus raw bytes). Cases carry `parameters` with slot/kind/value, `geometry`,
`depth`, `pixels`, `seed` and `index`. Implement `resize(cropped_case,old_geometry)`,
`simple_pixels(case)`, and `first_stage(...)` (return None if paired stages are
unavailable). Use `core.command` for bounded subprocesses and the existing plugin
helpers for public parameter units/ranges. The shared runner owns comparison,
shrinking, clustering, corpus and scheduling; no plugin registry edit is needed.

## Additional public adapters (T04)

All nine adapters use the existing `tools/emulation/` public replay hosts and
original-AEX session transport. They compile worktree production code with `-O2
-fno-fast-math -ffp-contract=off`; no numerical test seam or internal worker bypass
is enabled. Original AEX files and SDK assets remain in MAIN. Adapter modules:

| `--plugin` | Original owner | Mac public host | Scope notes |
|---|---|---|---|
| `olmdirectionalblur` | Smart | real SDK | Recovered fixed sliders; declared Noise Type 1..2, no independent layer |
| `olmcolorkey` | Smart | real SDK | All 25 color groups; mixed matching and independent pixels |
| `olmsmoother2` | Smart | retained CLI SDK shim | Key, smoothing, version, gamma, five gamma colors; Classic refusal retained |
| `olmkirakira` | Smart | real SDK | Default ramp handles; recovered native raw-fixed Rotation → Mac degrees |
| `olmblur` | Smart | real SDK | All five controls; fixed Smoothness; host copy preserves inactive padding |
| `colorkeep` | Smart | real SDK | All 100 colors; counts include 1/4/5/99/100 and random values |
| `olmdistancegradation` | Smart | retained SDK shim | All 12 public controls; no field/compose bypass |
| `olmsmoother` | Classic | retained CLI SDK shim | Exactly the three v1 controls; original does not advertise Smart |
| `olmtoondilate` | Smart | real SDK | Radius 0..100; Classic is an intentional successful no-op |

Run each independently, in the requested order, for example:

```sh
python3 tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed 1 --scratch orchestra/state/T04-fuzz-adapters-all-plugins
python3 tools/fuzz/run.py --plugin olmcolorkey --replay tests/fuzz_corpus/olmcolorkey --scratch orchestra/state/T04-fuzz-adapters-all-plugins --report orchestra/state/T04-fuzz-adapters-all-plugins/colorkey-replay.json
OLM_FUZZ_INTEGRATION=1 TMPDIR="$PWD/orchestra/state/T04-fuzz-adapters-all-plugins" python3 tools/fuzz/test_adapters.py
```

The new sampler covers sparse/dense controls, all three depths, degenerate and
occasional up-to-256 dimensions, SDR alpha endpoints, and PF32 HDR/signed/nonfinite
bits. Angles use a bounded legal +/-720-degree subset. KiraKira additionally
weights small single/multiple rays and native raw-angle values from its existing
public helper. ColorKey and ColorKeep include palette-member pixels as well as
independent pixels. PF16 sampling uses 0..32768; extended uint16 is not sampled.
For ColorKey, Smoother2, OLMBlur, and Smoother v1, the reused host shares one random
padded stride between input and output; other new hosts use independent strides.
All AEX session worlds remain packed. Native UI, custom ramps, selected layers,
ROI, downsample, and native AE/UCRT are outside these campaigns.

`declarations/*.json` holds hash-bound original `PARAMS_SETUP` snapshots; every
successful oracle session checks its live declarations against the snapshot.
Ranges are the original builder's recovered ranges, not guessed from UI labels.
Two builders have defaults outside their own bounds: KiraKira Gain is about 0.1
with a minimum of 1, and DistanceGradation In/Out is 0 with a minimum of 1. The
snapshot preserves these anomalies; generation and shrinking use the legal
minimum. KiraKira's declared Blur Mode range is 1..3 even though other historical
probes exercise serialized value 4. Review drift before explicitly recapturing:

```sh
python3 tools/fuzz/capture_declarations.py --plugin olmcolorkey --aex-name OLMColorKey --scratch orchestra/state/T04-fuzz-adapters-all-plugins
```

Corpora now have a default `--corpus-max-bytes 2000000` cap, enforced across
concurrent writers. A full corpus never drops measurements: omitted files have
`corpus_retained: false` and `corpus_omission: "byte cap"` in the campaign row.
Existing files count against the cap. No pixel counterexample is invented for a
campaign with no mismatches; those directories contain a short README instead.

Two interpretation boundaries matter in the first measurements:

- Smoother v1 uses the original Classic owner. The retained worker cannot allocate
  its PF16 legacy deep worlds; PF32 is not advertised by the AEX. These are AEX
  rejects, and successful Mac outputs remain **uncompared**. No emulator was built.
- ToonDilate's Classic handler intentionally returns success without rendering,
  matching the original legacy owner's documented no-op. The benchmark still
  records its raw destination-vs-AEX-Smart differences, but these are **cross-route
  differences**, not numerical kernel defects. Its Smart mismatches are separate
  in the route counters. Do not change the Classic no-op to chase this comparison.

`test_adapters.py` checks reproducible legal cases, builder anomalies, geometry,
concurrent corpus retention, and (with integration enabled) the existing KiraKira
Mode-1 5x3 public anchor at all three depths. Both Mac routes and the retained
worker must match the previously recorded AEX hashes. This anchor establishes
transport on those inputs; it does not generalize KiraKira's admission boundary.
