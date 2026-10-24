status: done
summary:
- Restored original Smart request forwarding, checkout-bound unions and output-sized writing from full source rows.
- Smart ray lengths now use the original float32 X downsample arithmetic; approximation disables at ratios <= 0.5.
- Realistic seed 1: 100 exact; fresh seed 2: 99 exact, 1 unavailable original IPP exception; zero available mismatches/refusals.
- Added 272 labelled realistic witnesses, including 72 full/ROI/expanded/empty boundary probes; Classic behavior retained.
- Default seed 1/n300 and historical corpus regression results and unit-test baseline are recorded below.

facts:

All commands ran in this worktree, serially within each driver, with at most two
build/emulator processes. Scratch and TMPDIR were ticket-local. No oracle rebuild,
MAIN edit, release-gate edit, ledger edit, push or history rewrite was performed.

### Original boundary evidence

`python3 tools/fuzz/witness_kirakira_geometry_P02c.py` extracted 312 instruction
lines and read the PE constant directly: `0x181486c1c = 0000003f = 0.5f`.
[Static evidence](P02c-evidence/static.json) retains disassembly/AEX hashes.

- `181151710..1811517cc` copies the incoming request, checks out layer 0 and unions
  checkout result/max-result rectangles through `181234f10`. It does not force a
  full-frame request or force preserve-RGB.
- PF16 `18114cc88..18114cd6c`, PF8 `18114d258..18114d33c` and PF32
  `18114d828..18114d90c` capture source dimensions and divide X numerator by
  denominator in float32. Approximation uses the half constant only above 0.5;
  ray lengths use float32 multiplication followed by truncation.
- PF16 writer `18114de30..18114df58` strides source/glow by source width, but loops
  over output width/height. It does not offset reads by output origin. The Mac
  implementation preserves this top-left-prefix behavior, including nonzero ROI.
- No aspect or extent adjustment was added to the render arithmetic. Available
  original comparisons below include non-square aspect, partial extent and odd
  byte padding. This is finite witness evidence, not an exhaustive absence proof.

### Measurements actually run

The exact commands are reproduced in `verify`. Raw case metadata, comparisons,
refusal attribution, hashes and build provenance are in [P02c-evidence](P02c-evidence/).
All exact counts mean identical negotiated rectangles and every packed sample byte.

| Run | Inputs | Exact | Mac-only refusal | Mismatch | Oracle unavailable |
|---|---:|---:|---:|---:|---:|
| Before, realistic seed 1 | 100 | 11 | 89 | 0 | 0 |
| Final, realistic seed 1 | 100 | 100 | 0 | 0 | 0 |
| Final, realistic seed 2 | 100 | 99 | 0 | 0 | 1 |
| Explicit boundary matrix | 72 | 72 | 0 | 0 | 0 |
| Final, default seed 1 | 300 | 287 | 0 | 0 | 13 |
| All KiraKira corpus replay | 342 | 341 | 0 | 0 | 1 |

- Before: 88 `request-not-admitted` and one `checkout-geometry` (index 37),
  reproducing F52c. Final index 37 AEX/Mac SHA-256:
  `cc58b308f99ad37d0da74503f016f0e8931b82e7c236536576015ea120f63cfe`.
  Index 0 AEX/Mac SHA-256:
  `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`.
  There is no first differing sample in the available final comparisons.
- Seed 2 index 48: original `IwException@ipp` at caller `0x18125ef13`; Mac retains
  a tuple/source refusal for this case. It is **unresolved**, excluded as oracle
  unavailable, and not called a faithful or Mac-only refusal.
- Boundary matrix: three depths, ratios 1:1/1:3/2:3, approximation on/off,
  full/subrect/expanded/empty requests, 4:3 aspect, partial content extent and
  seven-byte row padding. Expanded requests negotiate the original's bounded
  source rectangle; empty results correctly skip rendering in the qualified host.
- Default regression compares candidate status and bytes against a scratch build
  of base `5bb598413d4a40fc8b23480c7bc3a1a6b036ff18`: **300 unchanged, zero
  changes, zero exact-to-non-exact transitions**, including unavailable-oracle
  cases. The candidate-only comparison does not depend on oracle availability.
- Corpus replay: original `olmkirakira` 8/8 exact; `olmkirakira_gate_off_T06`
  62/62 exact; new labelled set 271 exact + 1 unavailable. Historical saved
  expectations were not rewritten; all comparisons here use the current oracle.
- Unit discovery before and final: **134 tests; 17 failures, 44 errors in each**;
  failing/error test-name sets identical. Full names are listed in
  [unit-summary.json](P02c-evidence/unit-summary.json), with complete logs adjacent.
  Historical failures include stale source/hash assertions and missing worktree
  assets/legacy worker paths. Three previously passing source assertions requiring
  Smart ROI/downsample refusal were updated to the recovered geometry contract;
  Classic assertions were retained. No numerical test failure was suppressed.
- `git diff --check` passes. Ticket scratch stayed below 10 MiB; regenerable
  executables/build trees were removed after validation.

Identities:

- Original AEX: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Cached F52c oracle: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- Final production source: `5824cdbf961ed2b335f41d8c0c3f1ad16de1014256f6e3bd283631cfd47bcb9f`.

inference:

The reproduced Mac-only refusals came from full-frame admission assumptions,
not original limitations. Forwarding the original request, honoring returned
bounds, using source dimensions and float32 X scale resolves the measured cases.
The nonzero-origin prefix behavior is original behavior, even though a spatial
crop might appear more intuitive. This ticket establishes the specified CPU
emulator/qualified-source-host contract, not native AE or all-input equivalence.
Output storage safety still requires output dimensions bounded by source storage;
no claim is made for an original writer reading beyond its source allocation.

changed_files:

- `mac/OLMKiraKira/OLMKiraKira.cpp` (Smart geometry; optional shared-render arguments
  preserve the Classic defaults).
- `tests/test_olmkirakira_generic_beta_lane_20260820.py` (three obsolete Smart
  refusal assertions updated; Classic checks preserved).
- `tools/fuzz/verify_kirakira_geometry_P02c.py`,
  `tools/fuzz/witness_kirakira_geometry_P02c.py` (plugin-only verification).
- `tests/fuzz_corpus/olmkirakira_realistic_P02c/` (272 witnesses and README).
- This report and `orchestra/reports/P02c-evidence/`.

verify:

Run from this worktree, one command at a time. Drivers accept only `--jobs 1`,
stream cases to scratch and exit nonzero on an available mismatch/refusal or
exact regression. Oracle unavailability remains explicitly counted.

```sh
export TMPDIR="$PWD/orchestra/state/P02c-kirakira-geometry"
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 tools/fuzz/witness_kirakira_geometry_P02c.py > "$TMPDIR/static.log" 2>&1
python3 tools/fuzz/verify_kirakira_geometry_P02c.py --label check-seed1 --seed 1 --n 100 --geometry realistic --jobs 1 > "$TMPDIR/check-seed1.log" 2>&1
python3 tools/fuzz/verify_kirakira_geometry_P02c.py --label check-seed2 --seed 2 --n 100 --geometry realistic --jobs 1 > "$TMPDIR/check-seed2.log" 2>&1
python3 tools/fuzz/verify_kirakira_geometry_P02c.py --label check-boundary --boundary --jobs 1 > "$TMPDIR/check-boundary.log" 2>&1
python3 tools/fuzz/verify_kirakira_geometry_P02c.py --label check-default --geometry default --n 300 --baseline-revision 5bb598413d4a40fc8b23480c7bc3a1a6b036ff18 --jobs 1 > "$TMPDIR/check-default.log" 2>&1
python3 tools/fuzz/verify_kirakira_geometry_P02c.py --label check-replay --replay --jobs 1 > "$TMPDIR/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmkirakira*.py' > "$TMPDIR/check-unit.log" 2>&1
git diff --check
```

Expected measurement counts are in the table. Unit discovery retains the listed
historical failures (exit 1), with no new failure/error names. To regenerate the
new corpus intentionally, add `--corpus` to the two realistic seed commands and
the boundary command. The static script reads original assets by absolute MAIN
path, without copying or modifying them.

next:

Investigate the seed-2/index-48 original IPP exception and tiny approximation
workspace as a separate ticket. Native AE validation and source checkouts with
nonzero input origins remain follow-up host coverage. Repairing historical unit
fixture/worker paths is separate from this geometry change. No hypothesis pair
was refuted; the stop-rule threshold was not reached.
