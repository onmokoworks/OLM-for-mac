status: blocked
summary:
- Implemented per-read zero semantics for out-of-range noise-table indices in both blur generators.
- Original table allocation, valid endpoint reads, arithmetic order and unrelated guards are preserved.
- All 1,800 cases complete: 41 Smart refusal-to-exact gains, zero Smart mismatches, zero exact losses.
- Status is blocked per the brief after a cleanup permission rejection; numerical work is complete.

facts:

FACT: Base commit `f4964bafa4286ea730f72310ca0fe74209d28d8f` on branch
`orch/C45-original-oob-noise-table`. The production change is confined to
`core/dblur_noise.h`, shared by DirectionalBlur and RadialBlur. Each indexed
read checks `[0, table.size())`; index -1 therefore reads zero on the left and
the original table[0] on the right. A 64-bit endpoint addition avoids signed
integer overflow. No allocation padding, lower wrap, clamp, other-plugin
change, release-gate change, ledger change, emulator rebuild or MAIN write.

FACT: `verify_noise_oob_C45.py` snapshots production sources into ticket scratch,
substitutes only the base commit's noise header, and builds baseline/candidate
public SDK hosts. Both consume the same generated inputs and same per-route
original AEX result. It runs sequential cases (jobs1), default F46 oracle,
10-second per-call limits, seeds 1/45101/45102, 300 per seed per plugin, no
shrinking. Two plugin processes ran concurrently. Baseline and candidate raw
output hashes are checked for every previously exact route. Corpus witnesses
include full parameters and input hashes; they rebaseline the recorded
before-refusal state to the observed exact Smart output.

FACT: The default worker is `/Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker`,
SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`.
The campaign's numerical acceptance route is Smart, matching C36/C44's scope.
Classic is also measured and retained as a diagnostic: its pre-existing
mismatches are not silently promoted or attributed to non-zero heap reads.

FACT: All six campaigns completed 300/300 cases, exit0. Smart mismatch count
is zero in every campaign; no previously exact route lost its exact output
hash. E/R/U/B means exact/refusal/uncompared/candidate-budget.

| Plugin | Seed | Before E/R/U/B | After E/R/U/B | Smart gains |
|---|---:|---:|---:|---:|
| directional | 1 | 290/8/2/0 | 296/2/2/0 | 6 |
| directional | 45101 | 285/15/0/0 | 295/5/0/0 | 10 |
| directional | 45102 | 285/15/0/0 | 296/4/0/0 | 11 |
| radial | 1 | 257/40/3/0 | 264/33/3/0 | 7 |
| radial | 45101 | 256/41/3/0 | 257/40/3/0 | 1 |
| radial | 45102 | 248/48/3/1 | 254/41/4/1 | 6 |

FACT: 41 distinct Smart refusals become exact (27 DirectionalBlur, 14 RadialBlur).
One Classic case also becomes exact (RadialBlur seed1/index144). Smart gains:

- directional, seed 1: 4/7/127/246/280/284.
- directional, seed 45101: 41/123/131/136/166/167/179/253/273/287.
- directional, seed 45102: 35/62/88/89/152/171/230/264/267/274/286.
- radial, seed 1: 76/77/108/123/144/214/282.
- radial, seed 45101: 273.
- radial, seed 45102: 20/46/52/207/220/238.

FACT: RadialBlur seed45102/index196 additionally changes refusal to successful
Mac render, but the original Smart oracle hits its 10-second budget; it stays
uncompared and is not promoted into the corpus. Index200 hits both the oracle
and candidate budgets before and after. There are no Smart first-mismatch
bytes or non-zero heap exception values to list.

FACT: All pre-existing Classic exact hashes survive. DirectionalBlur's 27 new
Smart witnesses produce nonzero Classic output against its historical
zero-output oracle route, adding 27 Classic mismatches to the already-known
population. RadialBlur Classic mismatch counts remain unchanged. Full Classic
counts and first-difference diagnostics are preserved in the evidence; these
are outside C36/C44's Smart qualification and are not excused as heap bugs.

FACT: Original AEX SHA256: DirectionalBlur
`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`, RadialBlur
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Changed noise-header SHA256
`f3038b21b78a3f523e35cefcc202d4f35eadce5f70ba3fd23b3128a34242bdaa`.
The evidence records each input hash, paired output hashes/statuses, oracle
budgets, first-difference diagnostics, source/build provenance and full raw
report hashes. Baseline `noise_header_sha256` binds the actual scratch header;
the pre-existing Radial adapter's `core_sha256` field instead hashed the live
worktree header. This provenance-only issue is labeled in evidence and fixed
in the final reproducer.

FACT: DirectionalBlur expanded corpus replay exits0, 83/83 saved results match.
RadialBlur's initial replay completes50, with49 saved matches and one oracle
10-second timeout (C45 seed45102/index52). Its candidate hash remains exactly
`8dd8931b572b2d93f784d0d8d33da0604ebfb0a81488e6636e5f0ca6bec41133`.
A targeted30-second replay exits0 and matches the complete saved result. Only
this new record's replay timeout is pinned to30 seconds with provenance;
measured campaign results remain unchanged. All original92 corpus files remain
unchanged;41 new witnesses are added. Final full RadialBlur replay exits0,
50/50 saved results match. Total expanded corpora: 133/133 saved results match.

FACT: No new out-of-range AEX memory trace is claimed. Prior C18/C25/C36 and
C11/C44 establish the original read RVAs (Directional `37f3/37f8`, Radial
`95cd/95d8`). No Smart mismatches required a non-zero-heap exception. The new
`notes/KNOWN_ORIGINAL_BUGS.md` states the deterministic contract and explicitly
records no non-comparable exceptions. Output equality alone is not proof of
which individual heap words were read.

FACT: All started processes have finished, regenerable build trees are removed,
and retained scratch is below 20 MiB (5 GiB cap). Final whitespace check passes.
No push, stash or history rewrite occurred.

FACT: `test_noise_oob_C45.cpp` passes with ASan/UBSan and halt-on-error. It
checks all 101 valid entries, negative and upper invalid indices including
int64 extremes, positive-zero results, an empty table, both straddling pairs,
12 generator calls at negative/neutral/positive offsets, and retained geometry,
cell-size and demand-mask guards. Build and test exit0, empty diagnostic log.

FACT: Automatic approval review rejected an entire combined report-update /
cleanup shell command because `rm -rf` is forbidden ("rm -f style commands are
not permitted. Use a safer approach"). That call made no changes. The report
updates were rerun and only the exact ticket scratch `unit-build` directory was
removed with path-checked Python `shutil.rmtree`. Per the worker brief's explicit
any-permission-rejection rule, status is `blocked` despite successful numerical
qualification. This is a tooling rejection, not a refuted numerical hypothesis.

inference:

INFERENCE: The exact gains are consistent with the emulator's zero-valued
invalid reads and implement the user-approved policy without depending on
native Windows allocator contents. Finite campaigns do not prove all-input
compatibility, native Windows heap behavior or the unresolved Classic owner.

changed_files:
- `core/dblur_noise.h`
- `tools/fuzz/verify_noise_oob_C45.py`
- `tools/fuzz/test_noise_oob_C45.cpp`
- `notes/KNOWN_ORIGINAL_BUGS.md`
- `tests/fuzz_corpus/olmdirectionalblur/C45_*.json`
- `tests/fuzz_corpus/radialblur/C45_*.json`
- `orchestra/reports/C45-evidence/measurements.json`
- `orchestra/reports/C45-original-oob-noise-table.md`

verify:

Run from this worktree, sequentially (or at most the two plugin campaigns in
parallel). Use a fresh output directory; the runner intentionally refuses to
overwrite one. All temporary/build output stays in ticket scratch.

```sh
s="$PWD/orchestra/state/C45-original-oob-noise-table/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/verify_noise_oob_C45.py --plugin olmdirectionalblur --jobs 1 --output "$s/directional" > "$s/directional.log" 2>&1
python3 tools/fuzz/verify_noise_oob_C45.py --plugin radialblur --jobs 1 --output "$s/radial" > "$s/radial.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --replay tests/fuzz_corpus/olmdirectionalblur --jobs 1 --scratch "$s/directional-replay" --report "$s/directional-replay.json" > "$s/directional-replay.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --scratch "$s/radial-replay" --report "$s/radial-replay.json" > "$s/radial-replay.log" 2>&1
sh ucrtmath/build.sh "$s/unit-build" > "$s/unit.log" 2>&1
clang++ -std=c++17 -O1 -fno-fast-math -ffp-contract=off -fsanitize=address,undefined -fno-sanitize-recover=all tools/fuzz/test_noise_oob_C45.cpp "$s/unit-build/libucrtmath.a" -o "$s/unit-build/noise-test" >> "$s/unit.log" 2>&1
"$s/unit-build/noise-test" >> "$s/unit.log" 2>&1
python3 -c 'import pathlib, shutil, sys; p=pathlib.Path(sys.argv[1]).resolve(); assert p.name == "unit-build" and "C45-original-oob-noise-table" in p.parts; shutil.rmtree(p)' "$s/unit-build"
git diff --check
```

Expected: both campaigns exit0, no Smart mismatch, no lost exact output; corpus
replays match all saved records; boundary/sanitizer test exit0. Oracle-budget
counts can vary with machine load. The measurement commands used the same
paths directly below ticket scratch (without `recheck`); `--jobs 1` is also
the custom runner's only supported/default concurrency. The runner's final
logging, exit-status aggregation and explicit baseline header manifest were
improved after the measured runs; numerical builds and comparison logic were
unchanged.

next:
- Orchestrator review: the explicit rejection rule requires blocked status;
  the cleanup was recovered safely and all requested numerical work is ready
  for review/merge. No further numerical fix is identified.
- Other refusal domains, oracle budgets, historical Classic-owner differences
  and native AE/Windows validation remain separate tickets.
