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

## RadialBlur measurement switches

Both are off by default and change only the candidate build; the AEX oracle and
the generated cases are unchanged.

- `OLM_RADIAL_CANDIDATE_BYPASS="tag1,tag2"` prepends a compile-time
  `OLM_RADIAL_EXPERIMENT_BYPASS` definition so the named admission guards fall
  through instead of returning. Tags are the bare `OLM_RADIAL_REFUSAL` tags,
  for example `unadmitted-zoom-profile`.
- `OLM_RADIAL_CANDIDATE_SANITIZE=1` builds the candidate with the probe's
  existing `-fsanitize=address,undefined` flags and records sanitizer reports in
  each route result under `sanitizer`.

The default build (no variables) is the production behavior; replay the saved
corpus after touching the switch.

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
