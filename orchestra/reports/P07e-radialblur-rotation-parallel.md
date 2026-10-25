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

## Progress checkpoint: acceptance and measurement (native large comparison still running)

FACT: all six required oracle generation campaigns completed. Contract route is Smart; Classic legacy results remain in the complete reports.

| Campaign | Cases | Smart exact | Original rejects | Original budgets | Smart numerical mismatch / Mac-only refusal |
| --- | ---: | ---: | ---: | ---: | --- |
| default seed 1 | 300 | 276 | 20 | 4 | 0 / 0 |
| realistic-v1 seed 1 | 100 | 88 | 11 | 1 | 0 / 0 |
| realistic-v1 seed 20261026 | 100 | 91 | 7 | 2 | 0 / 0 |
| realistic-v2 seed 1 | 100 | 88 | 11 | 1 | 0 / 0 |
| realistic-v2 seed 20261026 | 100 | 92 | 7 | 1 | 0 / 0 |
| odd-even-v1 + realistic seed 2026 | 150 | 132 | 15 | 3 | 0 / 0 |

- Odd-even also records one Mac budget exhaustion on an oracle-unavailable case (the same category documented in P05b); unavailable output is not counted exact.
- All R10's 275 default exact cases stay exact, with identical hashes. All P05b's 276 exact Mac hashes are unchanged; P05b case index 62 is now oracle-budget/uncompared, so there is one status transition against that older run, not an output change.
- Standard replays: root 59/61, realistic P02d 180/180, P05b 6/6, odd-even 4/4. C46_seed1_case000280 original guest stops at RIP 0x180002860, C49_seed1_case000117 at RIP 0x180002cc3. C46 standalone standard replay also fails. Their Mac hashes match saved output: `5a19de28aece7b23b644e5f2533da7f662677e3d6a837b9a96d88a53726487f8` and `6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d`. No first numerical mismatch exists for unavailable oracles. C46's exact root cause is not established; no oracle or corpus was changed.
- After unit suite: 268 tests, 77 failures, 63 errors. The 140 failure/error name set is identical before/after (zero added/removed).

FACT: P00b matrix used `--phase matrix --plugins radialblur --cases default corpus05 --situations eighth full 4k --jobs 1 --timeout 240`, before cache `P05b-radialblur-simd`, after cache `P07e-radialblur-rotation-parallel`. Both entire driver invocations held `lockf -k ~/.cache/olm-emu/bench.lock`. Heavy-case seconds:

| Size | Depth | Before | After (default cap 8) |
| --- | ---: | ---: | ---: |
| 240x135 | 8 | 16.973716041 | 5.662189250 |
| 240x135 | 16 | 17.148741834 | 5.882969875 |
| 240x135 | 32 | 17.441461417 | 5.780286375 |
| 1920x1080 | 8 | 121.177218334 | 29.971408834 |
| 1920x1080 | 16 | 127.917481584 | 32.743784584 |
| 1920x1080 | 32 | 124.070249250 | 35.189411959 |
| 3840x2160 | 8 | >240 (timeout) | 67.380923041 |
| 3840x2160 | 16 | >240 (timeout) | 64.567034041 |
| 3840x2160 | 32 | >240 (timeout) | 65.737126167 |

Default/no-op cases all completed at all three depths/sizes; exact seconds remain in matrix evidence. These are shared-machine single measurements, not medians; other workers and this ticket's serial oracle lane were active during portions of baseline, so load can affect speed ratios. The driver does not return output bytes; these numbers alone do not establish exactness.

FACT: `python3 orchestra/reports/P07e-evidence/concurrent.py` compiled a source host and held the shared lock for all timing. It runs `RenderRotationTyped` with disjoint frame worlds in four threads of one process, using deterministic opaque PF8 pixels, Quality 5, outer/inner strength 30/10 and fade 15/10. All 54 measurements finished without deadlock; every output is byte-compared with cap-1 output. Three-repeat medians (seconds):

| Size | Single cap 1 | Single cap 2 | Single cap 8 | Four concurrent cap 1 | Four cap 2 | Four cap 8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 64x64 | .032570 | .032053 | .033069 | .032932 | .032916 | .032773 |
| 128x128 | .060529 | .040158 | .027393 | .062315 | .053720 | .050486 |
| 240x240 | .115397 | .080766 | .051958 | .119086 | .099537 | .090851 |

INFERENCE: 16,384 pixels is a conservative demonstrated useful threshold: the 128x128 single render improves 2.21x, and four concurrent renders improve 1.23x. At 240x240 four renders improve 1.31x. 64x64 follows the sequential path for every cap; its small timing spread is not a threading speedup/regression. This is an internal render concurrency test, not an AE application benchmark.
