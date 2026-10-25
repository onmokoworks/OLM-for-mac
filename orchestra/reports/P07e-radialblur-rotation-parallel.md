status: blocked
summary:
- Deterministic Rotation prepass/scatter partitioned by complete radius rows; faithful reference remains sequential.
- Universal candidate builds; 150 forced-cap comparisons and 50 TSan renders are byte-identical.
- Heavy 1080p improves from 121–128 s to 30–35 s; 4K improves from >240 s to 65–67 s.
- Native reference/fast: 156 byte-exact comparisons, including heavy PF8 HD/4K at caps 1/2/8; root replay 59/61 remains blocked.

facts:
- Read AGENT_GUIDE.md, RadialBlur ledger entries, compatibility plan and emulation GOTCHAS. Stage-range inspection used `xcrun llvm-objdump --macho --arch=arm64 --disassemble --demangle ~/.cache/olm-emu/P05b-radialblur-simd/xcode/OLMRadialBlur/products/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur > "$TMPDIR/baseline.asm"`.
- Observed `memory_pressure` checks stayed at or above 48% free (required minimum 30%). Scratch was observed at 157 MiB during the final native comparison, below 5 GiB.
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07e-evidence/profile.py` captured retained P05b ARM64 heavy rotation. `profile_summary.py` classifies 13,615 rotation stack samples: 9,017 scatter-range, 4,577 prepass-range, 21 other. No SampleRGBA/SampleScalar frames were observed; no zero sampling-cost claim is made.
- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_*radialblur*.py'`: initial missing-SDK run 268 tests, 77 failures, 65 errors. After worktree-only SDK links: 268 tests, 77 failures, 63 errors. This is the before baseline, not green tests.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMRadialBlur --scratch "$TMPDIR/bundle"`: x86_64 and arm64 success. Candidate SHA256 c6a0d31f8f8221f3f1d476d9cdec176a2eb460822560fb38963f6b989555538f.
- `python3 orchestra/reports/P07e-evidence/threads.py`: 50 successful rotation renders, 150 reference-versus-fast comparisons at caps 1/2/8, 50 reference-versus-TSan comparisons, no first differing byte and no TSan report. All three depths; 25 enlarged 129x129 cases; 4,634,464 output bytes per complete case set. Seed 20261026; Quality forced to 5 to bound runtime. Detailed case parameters and hashes are retained in `P07e-evidence/threads__results.json.gz`.
- An initial test attempt accidentally changed Brightness instead of Quality; it was interrupted, child reaped, and rerun with slot 20. No results from the initial attempt are used.
- Automatic approval rejected a compound shell command containing deletion of the generated `threads` build directory: “rm -f style commands are not permitted. Use a safer approach”. The command did not run. Cleanup was subsequently confined to that exact generated directory using pathlib/shutil. No permission escalation was requested.

inference:
- The profile address-range classification is inferred from retained P05b ARM64 disassembly, not exact wall-time instrumentation. It favors parallelizing prepass and scatter; sampling remains sequential.
- Order proof: this is destination partitioning specialized to the actual radius-invariant stencil: a source row can only scatter to the same radius row, so there is no need to duplicate other source rows. All sample planes finish before prepass begins. Prepass writes cell ri*angular_count+ai; cross-row polar reads are immutable. After its join, scatter writes only ri*angular_count+wrapped_ai. A task owns a complete contiguous radius range and preserves ai, outer-offset, inner-offset and channel arithmetic order. Normalization starts after the scatter join. Eight private caches prevent shared map mutation; there is no additional contribution buffer. Exceptions are caught in callbacks and rethrown after join.
- OLM_REFERENCE_BUILD invokes the same original sequential traversal with one cache, retaining R10 scalar scatter. The default candidate uses the shared GCD helper. The 16,384-pixel threshold is supported by the measurements below.

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
python3 orchestra/reports/P07e-evidence/concurrent.py > "$TMPDIR/concurrent.log" 2>&1
lockf -k "$HOME/.cache/olm-emu/bench.lock" python3 tools/perf/ref_vs_fast.py --plugin radialblur --small 50 --hd 1 --uhd 1 --corpus-index 5 --parallel 1 2 8 --case-timeout 900 --jobs 1 --scratch "$TMPDIR/native-verify" > "$TMPDIR/native-verify.log" 2>&1
python3 -m unittest discover -s tests -p 'test_*radialblur*.py' > "$TMPDIR/units-verify.log" 2>&1
lockf -k "$HOME/.cache/olm-emu/bench.lock" python3 tools/fuzz/ae_realism_audit.py --phase matrix --plugins radialblur --cases default corpus05 --situations eighth full 4k --cache "$HOME/.cache/olm-emu/P05b-radialblur-simd" --state "$TMPDIR/verify-before-matrix" --jobs 1 --timeout 240 > "$TMPDIR/verify-before-matrix.log" 2>&1
lockf -k "$HOME/.cache/olm-emu/bench.lock" python3 tools/fuzz/ae_realism_audit.py --phase matrix --plugins radialblur --cases default corpus05 --situations eighth full 4k --cache "$HOME/.cache/olm-emu/P07e-radialblur-rotation-parallel" --state "$TMPDIR/verify-after-matrix" --jobs 1 --timeout 240 > "$TMPDIR/verify-after-matrix.log" 2>&1
```
Use a fresh generated build directory before rerunning scripts. Expected: threads.py reports 50 cases / 150 forced-cap / 50 TSan comparisons passing; concurrency completes 54 exact measurements; oracle runs have zero Smart numerical mismatches/Mac-only refusals, with the recorded root replay failures; unit failure/error names remain unchanged. Performance numbers are shared-load dependent. Native driver must report 156 exact / 0 refusal / 0 mismatch. Large equality coverage is PF8; PF16/PF32 are included in small/TSan/oracle comparisons and large performance measurements, not claimed as large native byte comparisons.

next:
- Investigate C46/C49 original-worker stops in a separate emulator/oracle ticket; keep saved output hashes and corpus expectations unchanged. Existing unit-suite failures also remain unresolved. Orchestrator may review the optimization as an exact partial result, but must not mark all acceptance conditions satisfied.

## Acceptance and measurement

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


## Final native reference check and closeout

FACT: the exact `ref_vs_fast.py` command in verify completed in 1143.508587 seconds: 50 small cases plus one literal heavy 1080p and one literal heavy 4K case, each at caps 1/2/8, **156 exact / 0 refusal / 0 mismatch**. Every first-mismatch field is null. Heavy parameters come from `C45_seed1_case000108.json` without rescaling its point values; PF8 large equality is the explicit coverage boundary. Small cases cycle all depths and geometry samplers. Timing is validation elapsed time, not a render-speed measurement.

| Large case | Bytes per output | Reference and all three fast SHA-256 hashes |
| --- | ---: | --- |
| 1080p PF8 | 8,294,400 | `b4fc72605b708453764a731faaaac10afdafd238ffc64cc88c1a86db16a8f249` |
| 4k PF8 | 33,177,600 | `9491da8320d886a565763fcc5bcc14c01a4945c8ed89a66dca11479a45859a7b` |

FACT: no production edits were made after the source used by the successful TSan/oracle/native tests. The cached universal bundle is under `~/.cache/olm-emu/P07e-radialblur-rotation-parallel`, registered in INDEX.json with source and bundle hashes; it is a measurement candidate, not an original-AEX oracle. Regenerable build trees and raw frames were removed after all renders joined; final scan found zero remaining object/archive/host binaries and zero ticket render processes. Final scratch is 18 MiB and memory_pressure reports 53% free. Compact logs, manifests, case parameters, first-mismatch fields and hashes are committed under P07e-evidence. No emulator source, original worker, MAIN checkout, release gate, ledger, other plugin source, or shared parallel helper was edited. No push, stash, or history rewrite was performed.

INFERENCE / disposition: deterministic radius ownership yields a useful single-frame speedup and no slowdown in the measured four-render concurrency probe. This is not blanket AE-exact certification. The literal all-corpora-success condition remains false, existing units are not green, and the worker brief explicitly requires `status: blocked` after the recorded automatic approval rejection even though that cleanup was subsequently completed safely. No refused, timed-out, or unavailable reference is called exact.
