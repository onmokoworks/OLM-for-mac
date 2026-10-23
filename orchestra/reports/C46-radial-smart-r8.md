status: partial
summary:
- Closed Type3/NV0 missing-layer Smart refusals with deterministic zero scatter spans and a separate Zoom size prepass.
- Seed1 sanitized E/M/R/U: 264/0/33/3 -> 268/0/19/13; fresh46101: 260/0/39/1 -> 260/0/18/22.
- All 524 baseline exact hashes survive; zero candidate sanitizer failures in 600 campaign executions.
- Independent original-rendered matrix: 48 references / 144 layouts exact; 96 original crashes / 288 layouts remain uncompared.
- Other residual domains are still under investigation; no release/AE completeness claim.

facts:

FACT: Started at `3ac8d70e85165596581c5dc7086deb2ec03ecb26`, branch
`orch/C46-radial-smart-r8`. Read AGENT_GUIDE, GOTCHAS, compatibility plan,
Radial ledger rows and C17/C35/C44/C45/F41b reports. MAIN/emulator/worker,
release gate, ledger and other-plugin sources are unchanged. No worker rebuild,
push, stash, history rewrite or delegation.

FACT: Ordinary requested seed1 n300 jobs1 run exited0: Smart264 exact,
0 mismatch,33 refusal,3 uncompared. Oracle275 rendered,20 rejected,5 budget.
AEX-rendered refusals: Type3/NV0 four (93/96/239/297), nonfinite four
(17/89/238/247), budget two (48/148), host checkout one (248).
Case280 was not AEX-rendered in this measurement; it is not counted as a gain.
Historical calibration4/6 is retained and not relabeled as new conformance.

FACT: Worker F46 SHA256
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`;
AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
Evidence JSON files bind candidate/source/core/import hashes and input hashes.

FACT: First scratch hypothesis, zero scatter span plus retaining the SV0 Zoom
seed, passes the ordinary seed1 population but fails independently at SV50.
Initial independent generator accidentally varied Offset slots6/12 rather than
Edge Fade7/13; this is retained explicitly as an offset matrix, not fade evidence.
It has12 mismatching references (36 layouts),36 exact references,48 oracle
crashes. First mismatch index52: 28/28 PF8 bytes, AEX7f vs Mac00 at byte0.
The final reproducer supports `--matrix offsets`; it also adds a third geometry.

FACT: F46 lacks the older trace worker's `offset` watch option. An initial full
C06 trace failed with `unknown watch field: "offset"`. Added an explicit
`--prefix-only` mode to C06, preserving F46 and lossless PNG transport for the
PF8 fixture. Before: polar/span prefixes1024 words each match; prepass factor
442/1024 words differ, first word AEX0000803f / Mac00000000. After: all three
prefixes match, public SHA256
`d150fa002561df86a87614dedb0e6ca8d9ae4cc47a4ee29f4c398d59270e1811`.
This is a measured intermediate boundary; no full-plane claim is made.

FACT: Second hypothesis separates the size plane but samples it even when
Size Variation is disabled. Edge-fade matrix then has3 mismatching references
(9 layouts): indices51/67/83, PF8/PF16/PF32, Repeat Border on, Size0/Fade3.
First PF8 difference byte4 AEX88/Mac87. Static original56F0 explicitly writes
literal1 when owner size flag+0x44 is clear, bypassing scalar sampling.
Final rule restores that branch. No per-coordinate or output-byte patch.
The new measured boundary between the first and second hypotheses prevents
the two-refuted-without-new-boundary stop condition from firing here.

FACT: Final independent matrix covers3x5,7x1,5x3, all depths, Zoom/Rotation,
Size0/50, both fades0/3, both Repeat modes and three strides. 144 references:
48 AEX-rendered references /144 candidate layouts exact;96 original invalid
memory-write failures /288 candidate layouts uncompared. All432 candidate
layouts sanitizer-clean. Those original failures are recorded, not silently
filtered or classified as a numerical success.

| Campaign | Before E/M/R/U | Final sanitized E/M/R/U | Lost exact hashes |
|---|---|---|---:|
| seed1 n300 |264/0/33/3|268/0/19/13|0|
| seed46101 n300 |260/0/39/1|260/0/18/22|0|

FACT: Refusal-to-exact gains are seed1 indices93/96/239/297. Other newly
rendered cases have unavailable original results and remain uncompared.
Fresh-seed results do not add exact cases. Existing corpus replay:50/50 saved
result objects unchanged (including Classic). Rebaseline table:50 unchanged,
0 modified; four new exact witnesses are added. Expanded replay54/54 saved results match.
Production comments/whitespace differ from the tested scratch transformation;
production independent matrix repeats the same144 exact/288 uncompared layouts.

FACT: Additional old smoke suite (`python3 tools/fuzz/verify_radialblur_smart_C06.py --ordinary --smoke --output orchestra/state/C46-radial-smart-r8/smoke`) ran8 tests:2 pass,6 build failures. They omit the UCRT library from their clang link commands and report unresolved `_ucrt_cos`, `_ucrt_sin`, `_ucrt_expf` (and other UCRT imports). These imports predate this change; this is not a numerical test failure. No smoke-pass claim. Current public-harness ASan/UBSan executions and original-AEX comparisons above do link UCRT and pass.

inference:

INFERENCE: Missing-layer scatter allocation and the independent size-factor
prepass explain the Type3/NV0 refusal family. Deterministic zero is consistent
with original emulator values but does not establish native allocator contents.
Original 2D crashes and absent raw nonfinite trace transport remain external
boundaries. No mismatch is excused as uninitialized memory without a witness.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `notes/KNOWN_ORIGINAL_BUGS.md`
- `tools/fuzz/probe_radialblur_C46.py`
- `tools/fuzz/verify_radialblur_type3_C46.py`
- `tools/fuzz/trace_radialblur_smart_C06.py` (opt-in F46 prefix trace)
- `tools/fuzz/fixtures/radialblur_type3_size_C46.json`
- `tests/fuzz_corpus/radialblur/C46_*.json` (four new exact witnesses)
- `orchestra/reports/C46-evidence/` and this report

verify:

From the worktree, all commands sequentially, fresh scratch paths:

```sh
s="$PWD/orchestra/state/C46-radial-smart-r8/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/probe_radialblur_C46.py --experiment type3-size-flag --campaign orchestra/reports/C46-evidence/baseline.json --output "$s/seed1" > "$s/seed1.log" 2>&1
python3 tools/fuzz/probe_radialblur_C46.py --experiment type3-size-flag --campaign orchestra/reports/C46-evidence/fresh.json --output "$s/fresh" > "$s/fresh.log" 2>&1
python3 tools/fuzz/verify_radialblur_type3_C46.py --independent --output "$s/matrix" > "$s/matrix.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/fuzz/trace_radialblur_smart_C06.py --source mac/OLMRadialBlur/OLMRadialBlur.cpp --cases-from tools/fuzz/fixtures/radialblur_type3_size_C46.json --indices 52 --no-shrink --prefix-only --legacy-trace-angles --trace-worker /Users/onmk/.cache/olm-emu/worker-F46-pow/aex-guest-worker --output "$s/trace" > "$s/trace.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --scratch "$s/replay" --report "$s/replay.json" > "$s/replay.log" 2>&1
git diff --check
```

Expected: both campaigns exit0, counts above, no lost exact/sanitizer errors;
matrix144 exact layouts,288 explicitly uncompared, zero mismatch/unclean;
trace three matching prefixes, original/public binding intact; corpus all saved
matches. Timeouts can change availability in fresh oracle reruns. Probe replays
use committed baseline oracle hashes, not a replacement worker.

next:
- Type3 cluster complete: ordinary post-change seed1 is268/0/19/13, zero baseline exact losses; corpus54/54 matches.
- Investigate remaining nonfinite, Rotation Override budget and host checkout domains.

FACT: Final production source SHA256 `d77b9a45193109d3cf1bc151480bb7d6aa5ac2d428c9a4c20993b9771a9d9e9d`.
