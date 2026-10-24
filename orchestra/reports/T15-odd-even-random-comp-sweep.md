status: blocked
summary:
- F52c resolves the earlier oracle protocol blocker; ColorKey and DirectionalBlur transport now qualify for realistic-v1.
- Corrected missing ColorKey PreRender bit depth in the source host; production sources are unchanged.
- Prerequisite seed 2026/n20 Smart E/M/R/U: ColorKey 10/6/4/0; DirectionalBlur 12/8/0/0.
- Three reduced witnesses replay as saved on both routes; default seed 2026/n10 results are identical before/after for each adapter.
- Two rectangle-only DirectionalBlur hypotheses fail; stopped under the ticket rule. Size calibration, new size sampler and 3,000-case sweep remain unperformed.

facts:

Starting commit: `1d997cbcf2ae6b341d0b3ef4a211b28ba2daa8e3`, branch
`orch/T15-odd-even-random-comp-sweep`. Read AGENT_GUIDE, emulator GOTCHAS,
compatibility plan, relevant ledger decision-table rows, F52c and P02 reports,
and the prior T15 report from `aca96437`.

Reference worker: `~/.cache/olm-emu/worker-F52c-geom/aex-guest-worker`, SHA256
`4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
Per-plugin AEX, candidate, declarations and source identities are in
[T15-evidence](T15-evidence/qualification-summary.json) and the corresponding
`*-provenance.json` files. No oracle rebuild, installed-bundle change, MAIN write,
release-gate edit, ledger edit, or production implementation edit was retained.

## Prerequisite measurements

`python3 tools/fuzz/qualify_T15.py` completed serially. It uses F52c, the existing
realistic-v1 sampler, seed 2026, n20 per plugin, ten-second case timeouts, and both
Classic and Smart comparisons. All 80 route delivery checks matched full size,
X/Y downsample, aspect and padding metadata. All three depths were exercised.
Negotiated ROI output rectangles and packed-byte comparisons are retained in
`*-qualification.json`; successful transport is not numerical acceptance.

The ColorKey host previously left `PF_PreRenderInput.bitdepth` zero. The shared
geometry wrapper uses that field to allocate negotiated output. Setting it from
the actual input depth fixes this host defect. For the same first five inputs:

| Adapter | Before Smart | After Smart |
|---|---|---|
| ColorKey | 0 E / 0 M / 4 R / 0 U / 1 host error | 2 E / 2 M / 1 R / 0 U |
| DirectionalBlur | 3 E / 2 M / 0 R / 0 U | unchanged |

The original returned successfully on every prerequisite input. Thus each R is
Mac-only, not an original refusal. After correction there were no host errors.
`*-before.json` retains the five-case baseline; `*-default.json` retains all
before/after default objects. Both adapters' default seed 2026/n10 objects match
exactly on both routes (40 route comparisons across the two adapters). This is
bounded regression evidence, not a claim that the entire historical default
corpus was rerun.

## Smart counts (prerequisite only; not the requested new size sweep)

E/M/R/U by **full-comp width parity / height parity**:

| Plugin | odd/odd | odd/even | even/odd | even/even | Total |
|---|---|---|---|---|---|
| ColorKey | 5/2/0/0 | 2/1/1/0 | 2/3/1/0 | 1/0/2/0 | 10/6/4/0 |
| DirectionalBlur | 5/2/0/0 | 3/1/0/0 | 3/3/0/0 | 1/2/0/0 | 12/8/0/0 |

| Plugin | 1/1 | 1/2 | 1/3 | 1/4 | 1/8 |
|---|---|---|---|---|---|
| ColorKey | 1/1/1/0 | 2/1/0/0 | 2/2/1/0 | 5/0/2/0 | 0/2/0/0 |
| DirectionalBlur | 1/2/0/0 | 2/1/0/0 | 2/3/0/0 | 7/0/0/0 | 0/2/0/0 |

This short seed did not select asymmetric downsample. Full raw results, depth
splits, classifications of every observed failure, and first differences are in
[counts.json](T15-evidence/counts.json). No measurements are claimed for the other
eight plugins or seed 2027 in this attempt.

## Failure classes and reduced witnesses

- **ColorKey admission:** indices 1, 9, 11, 19 refuse with
  `PrepareRenderWorld:public-admission@2598`. First input: PF16, full 94x1,
  sampled 24x1, downsample 1/4, extent [0,0,10,1], full output request.
  Reduced witness: sampled **3x1**, original succeeds, Mac returns 516.
  Relevant restriction: `mac/OLMColorKey/OLMColorKey.cpp:2523` requires complete
  extents for non-pixel-local processing; `:2520` also requires equal dimensions.
  Input SHA256 `ebf6610d00d95ee91497fa9c647351d0e580955031c2ee27de2993acf548e24e`.
- **ColorKey same-rectangle pixels:** indices 2, 3, 8, 10, 12, 17.
  First input: PF8, sampled 42x1, output [16,0,34,1], 63 different bytes;
  byte 0 original `ff`, Mac `00`. Reduced witness: **5x1**, output [1,0,5,1],
  10 different bytes, byte 0 still `ff` versus `00`.
  `RenderTyped` at `mac/OLMColorKey/OLMColorKey.cpp:1834` applies the output/input
  origin difference when reading source samples; it sizes working arrays from
  output dimensions at `:1832`. These are investigation pointers, not a proven
  complete cause for all six inputs.
  Input SHA256 `d7d3ffef0aab83bae9021e2b0f8a8db34c0e56712191e16329589a78bbb517c7`.
- **DirectionalBlur negotiated bounds:** indices 2, 3, 8, 10, 11, 12, 17, 19.
  First input: PF8, sampled 42x1, original [16,0,34,1], Mac [0,0,42,1].
  Reduced witness: **5x1**, original [1,0,5,1], Mac [0,0,5,1]; original output
  16 bytes, Mac 20 bytes. `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2337`
  replaces the request with full sampled bounds; `:2362` advertises the returned
  full rectangle. Input SHA256
  `de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90`.

Shrinking used 21 refusal attempts, 18 ColorKey pixel attempts, and 14
DirectionalBlur rectangle attempts. These are bounded greedy reductions, not
proofs of global minimality. Exact parameters, typed input bytes, geometry,
operations and both-route results are embedded in the separately labelled
`tests/fuzz_corpus/{olmcolorkey,olmdirectionalblur}/T15-prerequisite-realistic/`
sets. No existing corpus file or default generator was changed. Default replay's
non-recursive glob does not include these subdirectories.

## Two refuted local-fix hypotheses and stop

`python3 tools/fuzz/probe_T15_local_fixes.py` compiled two disposable copies of
DirectionalBlur and reran the retained 5x1 rectangle witness:

1. **Forward the incoming request:** remove the full-frame request assignment.
2. **Advertise ROI while retaining full input checkout:** replace the union of
   the full checkout result with the union of the original requested rectangle.

Both leave the original AEX successful but change the candidate from rectangle
mismatch to **refusal 516**, `RenderWorld:deep-copy-world@1482`. Neither restores
an admitted exact output. Thus neither request-only repair is sufficient; no
new pixel-level boundary value was obtained. The ticket's two-hypothesis stop
condition applies, so no additional production tuning or campaign was pursued.
The experiment source replacements, hashes, full results and guard traces are
in [local-fix-experiments.json](T15-evidence/local-fix-experiments.json).

Two initial experiment-build setup failures were corrected before measurement:
a missing sibling Strings header in the scratch source mirror, then a directory
named `mac` colliding with the host executable. These were compiler/linker setup
failures, not plugin observations. All experiment source copies were removed.

## Replay and validation

Standard `tools/fuzz/run.py --replay`, with `--geometry realistic --jobs 1`,
reports **replay_matches_saved: true** for ColorKey 2/2 and DirectionalBlur 1/1.
Each saved result includes both Classic and Smart. All retained oracle calls
completed under the ten-second case timeout; no unavailable/timeout witness was
saved. See `*-replay.json`. Matching a saved mismatch/refusal is reproducibility,
not conformance acceptance. `git diff --check` passes.

inference:

- The F52c protocol blocker is resolved, but prerequisite numerical acceptance
  is not: ColorKey has admitted mismatches and Mac-only refusals, DirectionalBlur
  has admitted rectangle mismatches.
- The source-host capability declarations describe measured transport support,
  as in F52c; they do not certify zero numerical failures.
- A faithful DirectionalBlur repair must address the render-world ownership/copy
  contract as well as PreRender output bounds. ColorKey needs a separate original
  AEX investigation of ROI source addressing and neighborhood staging. Removing
  guards or merely cropping the finished output is not established as correct.
- Proceeding with a claimed qualified all-ten size sweep would skip the ticket's
  acceptance prerequisite. The requested all-ten results remain unknown.

changed_files:
- `tools/fuzz/adapters/olmcolorkey.py`: real PreRender depth and transport capability.
- `tools/fuzz/adapters/olmdirectionalblur.py`: transport capability only.
- `tools/fuzz/qualify_T15.py`, `tools/fuzz/probe_T15_local_fixes.py`.
- `tests/fuzz_corpus/olmcolorkey/T15-prerequisite-realistic/{pixels,refusal}.json`.
- `tests/fuzz_corpus/olmdirectionalblur/T15-prerequisite-realistic/rectangle.json`.
- `orchestra/reports/T15-evidence/*.json` and this report.

verify:

Run in this worktree, serially:

```sh
export TMPDIR="$PWD/orchestra/state/T15-odd-even-random-comp-sweep"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 tools/fuzz/qualify_T15.py > "$TMPDIR/qualification.log" 2>&1
python3 tools/fuzz/probe_T15_local_fixes.py > "$TMPDIR/local-fixes.log" 2>&1
for plugin in olmcolorkey olmdirectionalblur; do
  python3 tools/fuzz/run.py --plugin "$plugin" --geometry realistic --jobs 1 \
    --replay "tests/fuzz_corpus/$plugin/T15-prerequisite-realistic" \
    --scratch "orchestra/state/T15-odd-even-random-comp-sweep/replay-$plugin" \
    --report "orchestra/reports/T15-evidence/$plugin-replay.json" \
    > "$TMPDIR/replay-$plugin.log" 2>&1 || exit 1
done
git diff --check
```

Expected: qualification exits 0 with 80 delivery checks, unchanged default
objects, and the numerical counts above; both experiments return the named
refusal; both standard replay reports have `replay_matches_saved: true`.
Qualification regenerates labelled evidence/witnesses; replay alone validates
committed expectations without regenerating them. Timing/guest instability must
be reported if it changes results, never hidden by rewriting expectations.

next:
- Separate P02-style ColorKey ROI addressing/neighborhood admission investigation,
  starting from the two saved witnesses and original AEX intermediate values.
- DirectionalBlur ROI output ownership/copy investigation at `RenderWorld:1482`,
  using the two refuted rectangle-only experiments as exclusions.
- After numerical prerequisites pass, resume T15's opt-in odd/even size sampler,
  measured oracle size/time ceilings, seeds 2026/2027 n150 across all ten plugins,
  parity/downsample breakdowns, shrinking and both-route labelled-corpus replay.
