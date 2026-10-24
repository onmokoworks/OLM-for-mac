status: done
summary:
- Smart uses the original's ordinary iterate call and output extent; removes unit-downsample/origin refusals.
- realistic-v1 seeds 1 and 20261024, n100 each: Smart 200 exact, 0 mismatch, 0 refusal, 0 unavailable.
- Default seed1/n300: both routes' complete result objects unchanged; Smart 300 exact.
- Added 218 labelled geometry witnesses, including expanded requests and empty results.
- Classic behavior unchanged; historical unit failures retained and enumerated in evidence.

facts:

## Implementation and original ownership

Only ColorKeep production code changed. Smart no longer checks the 1:1 scale or
compares PF_InData.output_origin with the world origin. It delegates to ordinary
iterate with `output.extent_hint` and progress extent `bottom-top`, preserving
existing staged output and checkout cleanup. Smart does not use Classic's manual
layer-origin offset loop or require output bounds inside input bounds. The host
iterate owns clipping. Classic continues to use precisely its previous guards and
mapped renderer. Palette arithmetic is unchanged.

Read-only disassembly SHA256
`9b8af3b010371ca654ca85b9b0fb8888c25946d0be6cce3cc50377c2a57e746d`:
Smart PF8 at `0x180001daf` calls `0x180001140`; PF16 at `0x180001e33`
calls `0x180001000`. These pass output extent to ordinary iterate. Smart PF32
has the same bottom-top calculation at `0x180001ebd..0x180001ec1` and extent
argument in its following call. Exact excerpts: `P02a-evidence/smart-disassembly.txt`.
No plugin-side scale or aspect arithmetic was added.

Final source SHA256:
`924d7978fb91bd70969c111440375b560916749bad11c2bccf27724583c2593d`.
F52c worker SHA256:
`4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
All campaign reports retain AEX/candidate/dependency hashes and per-case hashes.
No oracle rebuild, MAIN write, cache write, release-gate change or ledger edit.

## Measurements and attempted hypothesis

Commands below ran serial cases with `--jobs 1`, at most two concurrent processes.
Logs and reports were under `orchestra/state/P02a-colorkeep-geometry`.
Compressed full reports are committed in `P02a-evidence/`.

1. Before: `tools/fuzz/run.py --plugin colorkeep --geometry realistic --seed 1
   --n 100 --jobs 1 --shrink-attempts 0`: Smart E/M/R/U **11/0/89/0**.
2. First hypothesis, remove mapping refusal but retain manual ROI offsets:
   **70/30/0/0**. Refuted with a new ROI boundary: seed1 index0, PF8, sampled
   11x7, request `[5,4,6,5]`, stride padding3, downsample 1/2 x 1/3.
   First word original `00`, candidate `ff`; all four bytes differed.
   Original SHA `6a09a430419fc11e3403294383a1b647ff4b620e8a61650eefabb136fa23d4a3`;
   candidate `81ff65efc4487853bdb4625559e69ab44f19e0f5efbd6d5b2af5e3ab267c8e06`.
   This justified tracing Smart's actual ordinary-iterate dispatch.
3. Final original-style suite invocation: seed1 and fresh seed20261024 each
   **100/0/0/0**. Includes ROI allocation, asymmetric downsample, nonunit aspect,
   partial input extent and odd strides. No second refuted hypothesis.
4. Before and final default seed1/n300: Smart **300/0/0/0**, Classic
   **74/131/95/0**. Every paired `result` object equal across all 300 inputs;
   zero exact-to-non-exact transitions. Classic mismatches are outside contract.
5. `python3 mac/ColorKeep/tests/geometry_boundaries.py`: **18 Smart exact**,
   3 depths x expanded/empty/tile requests x 2 aspects, partial input extents.
   Expanded requests yield clipped input-sized results in original PreRender;
   empty results skip rendering. No claim of an original-expanded allocation:
   this plugin does not expand PreRender bounds. Larger externally supplied
   worlds now reach the host iterate instead of a Mac-only bounds refusal.
6. Existing `tests/fuzz_corpus/colorkeep` contains **0 JSON files**, only README.
   Attempted replay correctly reported empty-corpus setup error. Search for
   plugin-tagged JSON elsewhere in `tests/fuzz_corpus` found no older cases.
   New realistic corpus replay: **218/218 match saved results**, including
   Classic records; `P02a-evidence/replay-final.json.gz`.
7. `python3 mac/ColorKeep/tests/unit_geometry.py before` and `final`:
   **57 tests attempted, 13 failures, 24 errors** each (errors include two
   failing setUpClass calls). Per-file/test result records exactly equal.
   All free-function tests are run as well as unittest classes. One obsolete
   source-text assertion for the removed Smart float mapped helper was updated
   to assert the Smart float suite dispatch; the intermediate extra failure
   disappeared. No historical expectations were waived.
   Initial pytest invocation was unavailable (`No module named pytest`); the
   committed stdlib runner needs no installation.

Historical failing files (individual test names in `unit-before.json.gz` and
`unit-final.json.gz`; full tracebacks in accompanying logs): count9 incremental
identity, current installed complete union, current installed count9, generic
beta, legacy source admission, nine-color public closure, public guard closure,
ROI tile beta, source-bound complete-union candidate/install, Windows callback
contract. Causes include missing historical installed bundle/checkout resources,
missing worktree SDK/Util paths, stale source/identity hashes and old fixture
contracts. These are not newly observed pixel regressions. The qualified fuzz
host builds against MAIN's SDK via absolute paths and succeeds.

inference:

- The former manual layer-origin mapping diverged from the original's ordinary
  iterate contract on subrect-sized outputs; the 30 observed mismatches disappear
  when the host receives the same operation as the AEX.
- Scale, input extent and aspect need no new plugin-side color arithmetic for
  these witnessed cases. This is original-AEX emulation/source-host evidence,
  not a native AE 26.3 GUI or installed bundle qualification.

changed_files:
- `mac/ColorKeep/ColorKeep.cpp`
- `mac/ColorKeep/tests/{unit_geometry,save_geometry_corpus,geometry_boundaries}.py`
- `tests/test_colorkeep_windows_callback_contract_20260731.py`
- `tests/fuzz_corpus/colorkeep_realistic_P02a/` (218 cases and README)
- This report and `orchestra/reports/P02a-evidence/`.

verify:

Run from this worktree; redirect long output to scratch logs.

```sh
export TMPDIR="$PWD/orchestra/state/P02a-colorkeep-geometry"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
for seed in 1 20261024; do
  python3 tools/fuzz/run.py --plugin colorkeep --geometry realistic --seed "$seed" --n 100 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/verify-$seed" --report "$TMPDIR/verify-$seed.json" --corpus "$TMPDIR/verify-corpus" > "$TMPDIR/verify-$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin colorkeep --seed 1 --n 300 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/verify-default" --report "$TMPDIR/verify-default.json" --corpus "$TMPDIR/verify-default-corpus" > "$TMPDIR/verify-default.log" 2>&1
python3 tools/fuzz/run.py --plugin colorkeep --jobs 1 --replay tests/fuzz_corpus/colorkeep_realistic_P02a --scratch "$TMPDIR/verify-replay" --report "$TMPDIR/verify-replay.json" > "$TMPDIR/verify-replay.log" 2>&1
python3 mac/ColorKeep/tests/unit_geometry.py verify > "$TMPDIR/unit-verify.log" 2>&1
git diff --check
```

Expected: Smart 100 exact for each realistic seed, 300 exact default; replay
218/218 saved results match. Unit failure/error identities match committed
baseline (runner writes JSON rather than treating historical failures as PASS).

next:
- Orchestrator review/merge; native AE downsample/ROI smoke remains separate.
- Historical unit resource/identity repair and Classic differences are separate
  tickets. No Classic rendering behavior was changed to improve these counts.
