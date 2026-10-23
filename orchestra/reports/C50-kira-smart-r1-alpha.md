status: done
summary:
- Admit nonfinite PF32 Alpha approximation through existing box and Gaussian tuples.
- Fresh seed106 Smart282/0/18 →283/0/17 (index88); seed1 stays287/0/13 and seed105 stays285/0/15.
- Independent1152 gate-off and1152 production conditions are exact;20 negative refusals;900 sanitized campaign renders pass.
- Preserve854 prior exact Smart and900 Classic result objects,70 corpus results; historical1200 Smart replays preserve1156 exact and admit2 more exactly.

facts:

Base `31eeda2e`. After the preceding original IPP edge correction, two independent nonfinite Alpha approximation matrices each give576 exact under ASan/UBSan: ordinary controls and length/Highlight/rotation/ramp/opacity boundaries, three geometries including4×4, both merges, Modes1/2/3, multiple strengths, signed infinities, quiet/signaling NaNs and payloads. Gate-off1152 and final production1152 are strictly exact.20 negative conditions in other nonfinite constructors refuse. No hypothesis failed in this cluster. No paired-stage equality is claimed; the proof is public-AEX output plus independent matrices and sanitizer checks.

The source change adds `IsSmartApproximationTuple` to the existing PF32 Alpha source predicate. It retains the existing dimensions≥4, layout, angle, control, ramp and work limits. No arithmetic changes in this commit.

| Seed | Before Smart E/M/R | After | Improvement |
|---|---|---|---|
|1|287/0/13|287/0/13|none|
|105|285/0/15|285/0/15|none|
|106 (fresh)|282/0/18|283/0/17|88|

Every campaign completes300 cases, jobs1, no shrinking, default F46 and ticket-local scratch/corpus. The sanitizer campaign audit replays900 Smart cases against ordinary result hashes/statuses. All854 pre-cluster exact Smart and all900 Classic result objects are unchanged. Direct initial-to-final comparison also preserves all851 original exact Smart objects and all900 original Classic result objects.

Corpus before/after table: production8 unchanged; T06 62 unchanged; no rebaseline needed. Saved production replay8/8 passes using its retained worker provenance. Historical T06 saved expectations are not claimed current; both-revision executions are compared.26 fast tests and the compiled54-row sanitizer test pass (one unittest,45.187s).

`verify_kirakira_history_C50.py` additionally replays1200 Smart cases from committed S01 seeds101–104 under sanitizers, regenerating and validating input hashes/parameters and comparing to the archived F46 oracle hashes. It preserves all1156 former exact outputs and admits seed103/index82 and seed104/index120 exactly. Final history totals1158 exact/42 refusal. This is cached-oracle replay, not a new AEX campaign. It introduces no oracle or source overrides.

Final source SHA256 `098ab80805c4083e9b0c7f98c99b9549f3139d7f184f1466cb3bd3bf9c9af0f8`. F46 worker `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; original AEX `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. Reports, sanitizer logs and uncompressed SHA256 manifest are in `C50-kira-smart-r1/alpha/`; before campaigns are in the preceding color evidence directory.

The resize patch fixture is now zero-context: the previous commit's staged whitespace check flagged ordinary unified-diff context prefixes before tabs. Applying the reformatted fixture to the Gaussian source and `cmp` against the recorded scratch candidate succeeds byte-for-byte. Final diff whitespace checks pass. Legacy host-powf trace metadata now explicitly requires public-output binding rather than claiming F46 equivalence; F46 trace execution is unchanged.

inference:

The recovered resize and Alpha pipeline support the tested nonfinite approximation domain. This does not establish arbitrary native-AE, ROI/downsample or custom-ramp behavior. Remaining successful-oracle seed106 refusals122/123/248 are separate finite Gaussian source domains and were not promoted.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/verify_kirakira_history_C50.py`
- Legacy trace labels in `probe_kirakira_smart_C07.py` and `trace_kirakira_numeric_F09.py`
- Zero-context `tools/emulation/fixtures/kirakira_resize_edges_C50.patch`
- This report, final ticket report and alpha evidence.

verify:

Run at this cluster commit. Reproduce before/after campaigns using the Gaussian report's exact campaign loop with base `31eeda2e`, seeds1/105/106. Expected counts are above. Additional exact commands:

```sh
s="$PWD/orchestra/state/C50-kira-smart-r1/recheck-alpha"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 31eeda2e:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain alpha-approx --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain alpha-approx --boundary --require-exact --scratch "$s/boundary" --report "$s/boundary.json" > "$s/boundary.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain alpha-approx --negative --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --scratch "$s/corpus" --report "$s/corpus.json" > "$s/corpus.log" 2>&1
python3 tools/emulation/verify_kirakira_history_C50.py --scratch "$s/history" --report "$s/history.json" > "$s/history.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Gate-off reproduction: repeat positive matrices with `--source "$s/before.cpp" --gate-off`, separate scratch/report. Expected1152 exact. Ordinary production matrices here use the same candidate source bytes that were tested before installing the admission into the worktree. See the final ticket report for exact existing-test commands.

next:
- Three clusters closed; stop as requested.
- Suggested follow-up: finite scalar/color Gaussian source admission, starting seed106/122,123,248 and S01 seed102/20,55 and seed103/26,46; gate off and trace before promotion.
