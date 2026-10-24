status: partial
summary:
- Built and registered F52 oracle geometry worker; default worker remains unchanged.
- Qualified downsample forwarding for source-host Blur, ColorKey and DirectionalBlur; seed 1 / n100 measured for each.
- Original Smart renders expose 81 Blur and 80 DirectionalBlur Mac refusals; ColorKey has 7 Smart mismatches.
- Full realistic sampler, bundle-host geometry and the other seven plugin campaigns remain unfinished.
- Default replay matched 768/769 cases; one unchanged F46 RadialBlur oracle failure persists in an isolated retry.

facts:

The committed patch applies to `~/.cache/olm-emu/src-F46/reference-guest`.
Sources are retained in `~/.cache/olm-emu/src-F52/reference-guest`; binary and
full source manifest are in `~/.cache/olm-emu/worker-F52-geom/` and registered
in `~/.cache/olm-emu/INDEX.json`. Worker SHA-256:
`1be0cb14f6e68ab9276ef37be3a381aae9fb0306914987eb91e1a9d23dd94f4b`.
The committed patch was reformatted to zero-context after building; applying it
to F46 reproduces all four modified source files byte-for-byte. The original and
committed patch hashes are in [patch-format.json](F52-evidence/patch-format.json).
The build used jobs=1 and checked memory_pressure >=30%; the measured percentage,
command and hashes are in [build.json](F52-evidence/build.json). Build trees were
removed. No plugin, ledger, release-gate or default-worker changes were made.

Implemented oracle options: `--downsample-x`, `--downsample-y`,
`--rowbytes-pad`, `--extent-hint`, `--request-rect`, `--pixel-aspect`.
Full dimensions remain in PF_InData; primary worlds use ceiling-scaled dimensions.
Raw transport stays packed. The source candidate wrapper forwards downsample only.
World origins, negotiated expanded output worlds and candidate ROI/aspect options
are not implemented. SDK header citations and static disassembly addresses are in
[README-F52.md](../../tools/emulation/aexcompat_patches/README-F52.md).

Commands actually run:

- `python3 tools/emulation/aexcompat_patches/build_F52.py` and `--register`.
  Initial compilation failed on an ABI module namespace; corrected before build.
- `python3 tools/fuzz/validate_F52.py`: **44 checks passed**: 18 default F46/F52
  comparisons, 18 odd-byte-stride comparisons and 8 downsample/scaled-control
  comparisons. [Evidence](F52-evidence/qualification.json).
  An initial padding immutability assertion rejected Blur Classic PF8: the original
  writes row padding. Removed that invalid assertion, retained allocation guards,
  and verified active bytes exactly. [Initial observation](F52-evidence/first-padding-failure.json).
- `OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F52-oracle-downsample-geometry/tests" TMPDIR="$PWD/orchestra/state/F52-oracle-downsample-geometry" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_*.py'`:
  **34 tests, OK, 2 skipped**. [Log](F52-evidence/tests.log).
- `python3 tools/fuzz/measure_F52.py --plugin NAME --n 100` for `olmblur`,
  `olmcolorkey`, `olmdirectionalblur`: seed 1, serial, 10-second per-call deadline.
  This is the explicitly bounded **downsample qualification sampler**, not the
  unfinished `--geometry realistic` sampler. It draws 1/1, 1/2, 1/3, 1/4, 1/8
  and asymmetric 1/2 × 1/3; existing default generation is unchanged.
- `python3 tools/fuzz/limit_F52.py`: sampled Blur PF8 Smart 960×540 completed in
  **1.2662 s**, 1920×1080 in **4.9978 s**, both with downsample 1/2.
  The latter is the worker's existing maximum sampled width/height, not a
  general performance guarantee for arbitrary parameters/depths/plugins.
  [All seven measured sizes](F52-evidence/limits.json).
- `python3 tools/fuzz/replay_F52.py`: all **769** saved cases attempted with their
  recorded workers/default geometry. **768 matched**, one RadialBlur Smart oracle
  stopped before returning at `0x180002860`. An isolated replay using the same
  saved 30-second timeout reproduced the rejection. No expected bytes changed.
  KiraKira initially failed host construction because its source include uses a
  macro; wrapper now handles that include, and both KiraKira corpora replay 70/70.
  [Per-corpus counts and failing row](F52-evidence/default-replay.json),
  [isolated retry](F52-evidence/radial-retry.json).

E/M/R/U below counts each route's 100 comparisons. U takes precedence when the
oracle is unavailable; R means candidate refusal while the original rendered.

| Plugin | Route | E | M | R | U |
|---|---|---:|---:|---:|---:|
| Blur | Classic | 3 | 0 | 79 | 18 |
| Blur | Smart | 19 | 0 | 81 | 0 |
| ColorKey | Classic | 0 | 100 | 0 | 0 |
| ColorKey | Smart | 93 | 7 | 0 | 0 |
| DirectionalBlur | Classic | 0 | 50 | 50 | 0 |
| DirectionalBlur | Smart | 20 | 0 | 80 | 0 |

Original behavior: all 300 Smart calls rendered successfully. ColorKey Classic
returned an all-zero destination in all 100 cases. Blur Classic had 18 emulator
handle-allocation failures exceeding its 2 GiB handle cap (including oversized
unsigned requests); these are **not proven native-AE refusals**. All other
original calls returned successfully. Thus this campaign establishes no additional
faithful original PF-error refusal class. Raw candidate Blur Classic refusals total
97; 18 overlap those unavailable oracles and are U in the table.

Candidate refusal tags (raw counts, including unavailable-oracle overlaps):

| Plugin/route | Tag | Count | Interpretation |
|---|---|---:|---|
| Blur Smart | `generic-downsample@2087` | 81 | Geometry rejection despite original render |
| Blur Classic | `classic-nondefault-tuple@1444` | 62 | Parameter admission |
| Blur Classic | `classic-pf32-unowned@1426` | 35 | Depth/owner admission |
| DirectionalBlur Smart | `prerender-partial-frame@2324` | 79 | Geometry rejection despite original render |
| DirectionalBlur Smart | `smart-generic-world-or-budget@2665` | 1 | Combined world/budget guard |
| DirectionalBlur Classic | `pf16-neutral-world-or-budget@1586` | 3 | Combined world/budget guard |
| DirectionalBlur Classic | `pf16-feature-world-or-budget@1568` | 22 | Combined world/budget guard |
| DirectionalBlur Classic | `pf32-feature-world-or-budget@1799` | 16 | Combined world/budget guard |
| DirectionalBlur Classic | `pf32-neutral-world-or-budget@1818` | 1 | Combined world/budget guard |
| DirectionalBlur Classic | `pf8-feature-unadmitted@1557` | 8 | Feature admission |

First mismatches:

- ColorKey Smart: seed 1 index 3, full 39×45 → 10×12, PF16, 1/4.
  27 differing words; first word 0: original bytes `c634`, Mac `d634`.
  Other Smart mismatch indices: 12, 27, 31, 33, 87, 93 (all downsampled).
- ColorKey Classic: index 0, PF8, first byte 1: original `00`, Mac `93`;
  106 differing bytes of 120.
- DirectionalBlur Classic: index 0, PF8, first byte 0: original `00`, Mac `83`;
  29 differing bytes of 120.

Full generated metadata, input hashes, output hashes, diagnostics and refusal
traces are committed as `F52-evidence/*-results.jsonl`; corresponding summaries
bind the AEX, candidate executable and source dependencies. Inputs regenerate
from seed/index with the committed driver.

inference:

- Blur's `0x1800022ee..0x180002315` uses float32 horizontal scale then truncation.
  DirectionalBlur's `0x180003d39..0x180003dac` scales four strength/fade integer
  fields and truncates toward zero. Eight final-output equivalence checks support
  those bounded interpretations; they do not establish all parameter interactions.
- DirectionalBlur's partial-frame guard likely conflates full PF_InData dimensions
  with sampled world dimensions. The measured tag identifies the boundary;
  this ticket makes no plugin repair.
- ColorKey's seven Smart mismatches need separate numerical investigation. Its
  inverse-coordinate-scale helpers are identified, but their callers/radius rule
  remain unconfirmed. The Classic zero output is a separate route behavior.
- RadialBlur uses an unchanged independent adapter and a recorded F46 worker;
  its persistent oracle failure is not evidence of an F52 geometry regression.
  Its cause is not established here and the saved expectation remains untouched.

changed_files:

- `tools/emulation/aexcompat_patches/F52-geometry.patch`
- `tools/emulation/aexcompat_patches/build_F52.py`
- `tools/emulation/aexcompat_patches/README-F52.md`
- `tools/fuzz/adapters/public.py`
- `tools/fuzz/adapters/olmdirectionalblur.py`
- `tools/fuzz/harnesses/geometry.hpp`
- `tools/fuzz/measure_F52.py`, `validate_F52.py`, `limit_F52.py`, `replay_F52.py`
- This report and `orchestra/reports/F52-evidence/`.

verify:

Run from this worktree, serially:

```sh
shasum -a 256 ~/.cache/olm-emu/worker-F52-geom/aex-guest-worker
python3 tools/fuzz/validate_F52.py
python3 tools/fuzz/measure_F52.py --plugin olmblur --n 100
python3 tools/fuzz/measure_F52.py --plugin olmcolorkey --n 100
python3 tools/fuzz/measure_F52.py --plugin olmdirectionalblur --n 100
python3 tools/fuzz/limit_F52.py
python3 tools/fuzz/replay_F52.py
```

Expected hash and counts are above. Timing can vary. Replay is **not claimed
all-green**: expect the recorded RadialBlur oracle issue unless its environment
or underlying cause changes. `build_F52.py` refuses to overwrite a built worker;
reproduction in an empty F52 cache destination applies the committed patch to
hash-verified F46 sources. No default/corpus migration is performed.

next:

1. Complete candidate padding/extent/request/aspect support, F47d/F51 bundle-host
   options, and a tested `--geometry realistic` sampler with replay/shrink support.
   Qualify the oracle's aspect/rectangle paths and negotiated output geometry.
2. Run the remaining seven plugin campaigns after that plumbing is ready.
3. Fix Blur/DirectionalBlur geometry admission in separate plugin tickets using
   these original-render witnesses; investigate ColorKey's seven Smart mismatches.
4. Investigate the unchanged F46 RadialBlur `C46_seed1_case000280` oracle failure
   without changing its corpus expectation. No additional retry loop was run.
