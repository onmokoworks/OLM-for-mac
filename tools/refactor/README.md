# Native revision differential

Run from any directory on the Mac with Xcode command-line tools and Rosetta:

```sh
python3 tools/refactor/native_diff.py --plugin olmsmoother2 --base <pre-refactor-sha> \
  --head WORKTREE --cases 3000 --seed 909 --arch both --build both --jobs 1
```

All ten fuzz adapter names are accepted (`--help` lists them). `--head` defaults
to `WORKTREE`, including local edits; use a commit/branch name for a tracked
snapshot. Each revision builds its own fuzz harness and production sources. The archives
contain `mac`, `core`, `cli`, `tools`, `ucrtmath` and the RadialBlur declaration
report required by its adapter; unrelated captures are omitted.
MAIN supplies only the SDK paths. No AEX workers are needed. Architectures are
compiled explicitly, including ucrtmath, and launched with `/usr/bin/arch`.
Smoother v1 uses Classic; the other plugins use Smart.

`--cases N` means N small seeded cases **plus three 3840×2160 cases**, one per
depth. Small cases cycle all depths and default/realistic-v1/realistic-v2 geometry;
odd-even-v1 sizes alternate with default sizes. The geometry samplers provide
ROI, padding, aspect and downsample coverage. Smoother2 alternates the fuzz
sampler's independent `float-v1` colours with byte-derived colours. Other adapters
have no independent float-colour sampler. Use at least 18 small cases to cover
all depth/geometry/size combinations; the G1 run requires at least 3000.
Large inputs tile the generated raw payload and scale point parameters, as in
`tools/perf/ref_vs_fast.py`; they render the full frame without downsample.

The JSON summary includes counts, coverage, binary hashes and the first ten
differences with full case parameters and first differing raw byte. Refusal error
codes and ordered guard tags are compared; only the `@source-line` trace suffix
is ignored because refactoring moves source lines. Identical refusals are counted
separately from rendered matches. Process failures and timeouts never count as
successful equality. Exit codes: 0 = equal, 1 = difference/execution error,
2 = setup failure. There is no numerical tolerance.

Scratch defaults to `orchestra/state/Q00-refactor-native-diff-tool/<plugin>`.
`--scratch` can select another directory under this worktree's `orchestra/state`.
Per-case JSONL observations, compiler logs and `summary.json` remain there;
archives, native binaries and raw frames are removed on completion. Runs are
serialized and use `OLM_PARALLEL_MAX=1`. A stale `run` directory is rejected to
avoid deleting another active run. Reproduce a case with the recorded seed and
case count (depth rejection sampling depends on the count).

Self-tests (both architectures and both build modes):

```sh
python3 tools/refactor/self_test.py
python3 tools/refactor/self_test.py --mutation
```

The identity test runs 18 small + 3 full 4K cases for every plugin at HEAD versus
HEAD. The mutation test wraps snapshot creation to insert a `nextafter` change
into ColorKeep's float kernel in the archived head copy only, runs the same CLI
comparison, requires raw PF32 differences without execution errors, and verifies
that the planted copy was deleted. It returns 0 when that expected detection
succeeds; the differential itself returns 1 for the planted regression.
