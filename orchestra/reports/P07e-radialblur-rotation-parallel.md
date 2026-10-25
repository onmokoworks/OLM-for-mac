status: blocked
summary:
- Work in progress: deterministic Rotation prepass/scatter partitioned by complete radius rows.
- Universal candidate builds; 150 forced-cap comparisons and 50 TSan renders are byte-identical.
- Required oracle, full-frame performance, concurrency and native large reference checks are pending.
- An automated approval rejection requires blocked status under the worker brief.

facts:
- Read AGENT_GUIDE.md, RadialBlur ledger entries, compatibility plan and emulation GOTCHAS.
- `memory_pressure` reported 51–56% free during initial work.
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07e-evidence/profile.py` captured retained P05b ARM64 heavy rotation. `profile_summary.py` classifies 13,615 rotation stack samples: 9,017 scatter-range, 4,577 prepass-range, 21 other. No SampleRGBA/SampleScalar frames were observed; no zero sampling-cost claim is made.
- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_*radialblur*.py'`: initial missing-SDK run 268 tests, 77 failures, 65 errors. After worktree-only SDK links: 268 tests, 77 failures, 63 errors. This is the before baseline, not green tests.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMRadialBlur --scratch "$TMPDIR/bundle"`: x86_64 and arm64 success. Candidate SHA256 c6a0d31f8f8221f3f1d476d9cdec176a2eb460822560fb38963f6b989555538f.
- `python3 orchestra/reports/P07e-evidence/threads.py`: 50 successful rotation renders, 150 reference-versus-fast comparisons at caps 1/2/8, 50 reference-versus-TSan comparisons, no first differing byte and no TSan report. All three depths; 25 enlarged 129x129 cases; 4,634,464 output bytes per complete case set. Seed 20261026; Quality forced to 5 to bound runtime. Detailed case parameters and hashes are retained in `P07e-evidence/threads__results.json.gz`.
- An initial test attempt accidentally changed Brightness instead of Quality; it was interrupted, child reaped, and rerun with slot 20. No results from the initial attempt are used.
- Automatic approval rejected a compound shell command containing deletion of the generated `threads` build directory: “rm -f style commands are not permitted. Use a safer approach”. The command did not run. Cleanup was subsequently confined to that exact generated directory using pathlib/shutil. No permission escalation was requested.

inference:
- The profile address-range classification is inferred from retained P05b ARM64 disassembly, not exact wall-time instrumentation. It favors parallelizing prepass and scatter; sampling remains sequential.
- Order proof: all sample planes finish before prepass begins. Prepass writes cell ri*angular_count+ai; cross-row polar reads are immutable. After its join, scatter writes only ri*angular_count+wrapped_ai. A task owns a complete contiguous radius range and preserves ai, outer-offset, inner-offset and channel arithmetic order. Normalization starts after the scatter join. Eight private caches prevent shared map mutation; there is no additional contribution buffer. Exceptions are caught in callbacks and rethrown after join.
- OLM_REFERENCE_BUILD invokes the same original sequential traversal with one cache, retaining R10 scalar scatter. The default candidate uses the shared GCD helper. The initial 16,384-pixel threshold still needs measurement.

changed_files:
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialRotationRows.h
- tools/perf/ref_vs_fast.py (RadialBlur defaults to caps 1/2/8)
- orchestra/reports/P07e-radialblur-rotation-parallel.md
- orchestra/reports/P07e-evidence/*

verify:
```sh
export TMPDIR="$PWD/orchestra/state/P07e-radialblur-rotation-parallel"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
bash scripts/setup_ae_sdk_links.sh
python3 orchestra/reports/P07e-evidence/threads.py > "$TMPDIR/threads.log" 2>&1
python3 orchestra/reports/P07e-evidence/oracle.py > "$TMPDIR/oracle.log" 2>&1
```
Use a fresh generated build directory before rerunning scripts. Expected established result: threads.py reports 50 cases / 150 forced-cap / 50 TSan comparisons passing. Oracle results are not yet established for this ticket.

next:
- Complete pending acceptance and measurements; this intermediate commit is not ready for merge as an accepted optimization.
