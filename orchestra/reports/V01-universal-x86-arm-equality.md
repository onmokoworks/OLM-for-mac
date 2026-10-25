status: partial
summary:
- Fresh Universal bundles for all ten plugins: four requested samplers completed, 3,500 cases / 8,400 slice pairs, zero byte or rectangle differences.
- Heavy P00b campaign: 57/60 cases completed and equal; RadialBlur 4K remains in progress.
- Direct Intel/F53 comparison: 1,854 exact renders / 2,000 cases after four retries; 146 original-oracle non-renders are not equality evidence.
- No production arithmetic, release gate, ledger, MAIN, or AEXCompat source changes; full acceptance is not claimed.
- Hosts/bundles are durable in ~/.cache/olm-emu/worker-V01-universal/ and registered in INDEX.json.

facts:
- Built source HEAD `6e140f1616ce19e697264d399b9afd9e222a3ae2`; later V01 commits change only this ticket's harness/report/evidence. `git diff --name-only 6e140f16 HEAD -- core mac` returned no files.
- `python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/V01-universal-x86-arm-equality/bundles` completed successfully in the prior retained run. All ten executables have `x86_64 arm64` slices. Actual single-job Xcode commands and bundle hashes: `V01-evidence/bundle-builds.json`.
- `python3 tools/fuzz/verify_V01.py --prepare` rebuilt only the standalone F51/F52c-derived Universal hosts, preserving the current bridge suites. Source hashes/commands are in `V01-evidence/build.json`. Full host SHA-256 `94ca3fa8d688411473c384132d1d4b18dd4cd7cde90a1a58ffefb10529891829`; geometry host `defa5b4b86cdc20035fe90f14df58b788309016363844d6de63214922d98c5d1`.
- Resume-time hash/lipo check verified both retained hosts and all ten retained Universal bundles against that manifest. `arch -x86_64 /usr/sbin/sysctl -n sysctl.proc_translated` returned `1` in the retained run.
- Each pair uses explicit `/usr/bin/arch -arm64` and `-x86_64` launches of the same host and plugin executable. Successful comparisons check raw output bytes and negotiated rectangles. Refusal comparisons additionally require the same error and refusal trace; they are counted separately below.
- Seed 909 / n100 for default, realistic-v1 and realistic-v2. Seed 2026 / n50 for odd-even-v1, with realistic-v1 geometry and T15b maxima: 1920x1080 normally, Kira 1080x1080, Smoother2 623x623.
- Caps 1/2/8 on both slices for Blur, ColorKey, DirectionalBlur, DistanceGradation, Kira, Smoother2 and RadialBlur; cap 1 for the other three. Completed outputs also agree across caps.

| Sampler | Cases | Equal rendered pairs | Equal refusal pairs | Byte/rect differences |
| --- | ---: | ---: | ---: | ---: |
| default | 1000 | 2356 | 44 | 0 |
| realistic-v1 | 1000 | 2215 | 185 | 0 |
| realistic-v2 | 1000 | 2362 | 38 | 0 |
| odd-even-v1 | 500 | 1096 | 104 | 0 |
| heavy | 57 | 133 | 2 | 0 |

- Heavy selection uses each size/depth's slowest measured non-default P00b corpus tuple, prioritizing P00b timeouts; original absolute point coordinates are retained. All 60 selected cells are listed in `V01-evidence/heavy-selection.json`. Inputs use the same deterministic opaque P00b spatial pattern, normalized for 8/16/32 bpc. P00b corpus hashes are validated before use.
- Heavy commands run on resume: `python3 tools/fuzz/verify_V01.py --phase heavy --timeout 600 --jobs 1`, then `python3 tools/fuzz/verify_V01.py --phase heavy --timeout 600 --jobs 1 --slice-jobs 2`. The first runner was explicitly stopped with its child before switching execution strategy; only an unfinished RadialBlur case was restarted, with no partial result counted. At most two render/oracle processes were run by this worker.
- Resource interruption: a live `memory_pressure` check fell to 29%, below the required 30%. The two-slice runner and its remaining native child were stopped immediately; its unfinished RadialBlur 4K/8 case was not counted. `V01-evidence/memory-stop.json` records this event. Memory recovered to 50%; resumed with `python3 tools/fuzz/verify_V01.py --phase heavy --plugins olmsmoother radialblur --timeout 600 --jobs 1 --slice-jobs 1` (Smoother completed; RadialBlur 4K in progress).
- Two-slice execution calibration: `python3 tools/fuzz/verify_V01.py --state orchestra/state/V01-universal-x86-arm-equality/two-slice-smoke --n 1 --jobs 1 --slice-jobs 2`, exit 0, 10 equal cases; every result matches its retained serial default counterpart. Evidence: `V01-evidence/two-slice-smoke.jsonl.gz`.
- F53 original-AEX observations: default initially 955 exact / 45 non-render; realistic-v1 898 exact / 102 non-render. `python3 tools/fuzz/retry_V01_budgets.py` retried only the four original 10-second wall-budget failures at 60 seconds (exit 0). Default RadialBlur/23 became exact; DirectionalBlur/47 and DistanceGradation/79 (default and realistic-v1) stopped before guest return. Effective totals are default 956 exact / 44 non-render, realistic-v1 898 exact / 102 non-render. No byte/rect mismatch was observed between successfully returned oracle and Intel outputs.
- Effective non-render breakdown: default = 35 unsupported Smoother PF32 + 6 OpenCV exceptions + 2 guest execution stops + 1 unmapped write (RadialBlur/86). Realistic-v1 = 35 unsupported Smoother PF32 + 13 output-guard corruptions + 49 VCRUNTIME exception ownership failures + 3 OpenCV exceptions + 1 guest stop + 1 unmapped write (RadialBlur/86). The adapter classifies these as `reject`; this does not imply all are intentional plugin refusals. Raw diagnostics and original AEX/worker hashes are retained in compressed observations/provenance, including the four retry rows.
- No first differing byte, rectangle or production source line exists in completed slice comparisons. No numerical mismatch hypothesis or production fix was attempted. Oracle non-renders were not patched or treated as expected pixel values.
- `python3 tools/fuzz/summarize_V01.py --evidence` checks committed compressed observations against their summary, verifies unique identities and equality across completed thread-cap outputs, and succeeds without the scratch directory. `git diff --check` passed at each checkpoint.

Architecture conditionals (full grep retained in `V01-evidence/architecture-guards.txt`):
- `core/dblur_float.h:3-4`: ARM-only NEON include, supporting the vector helpers.
- `core/dblur_float.h:22`: guards `olm::dblur_float::result4`, `mul4`, `add4`.
- `core/dblur_rowdriver.cpp:227`: guards vector/RGB setup inside `olm_dblur_scatter_f32_fast`.
- `core/dblur_rowdriver.cpp:236`: guards that function's independent-channel NEON accumulation; other architectures use its scalar fallback.
- `tools/fuzz/test_F38.cpp:11`: `main`'s ARM FPCR default-NaN test, saving/restoring FPCR; test-only.
- No `__x86_64__`, `__SSE`, or `immintrin` matches in tracked C/C++/Objective-C/header sources. A broader architecture-macro search found no additional guards. `mac/OLMRadialBlur/RadialScatterSIMD.h` uses architecture-neutral `vector_size(16)` types, not an architecture preprocessor branch.

inference:
- The completed results support bounded Rosetta-x86_64 versus native-arm64 equivalence for these exact inputs/bundles/caps. Matching refusals are not rendered-output evidence. This is not a native AE or physical Intel Mac certification.
- The original-AEX failures leave 146 cells without direct Intel numerical evidence. Guest stops/guard corruption/exception ownership failures need a separate oracle/host follow-up; this ticket permits only a host rebuild, not an AEXCompat rebuild or guest semantic changes.
- R10 ref_vs_fast behavior and arm64 production arithmetic are unchanged by source identity; no new ref_vs_fast campaign is claimed.

changed_files:
- `tools/fuzz/verify_V01.py`
- `tools/fuzz/summarize_V01.py`
- `tools/fuzz/retry_V01_budgets.py`
- `orchestra/reports/V01-universal-x86-arm-equality.md`
- `orchestra/reports/V01-evidence/*` (build/provenance manifests, compressed observations, summary, heavy selection and architecture inventory)

verify:
- `python3 tools/fuzz/summarize_V01.py --evidence` — expected exit 0; phase counts and explicit non-render totals shown above.
- `git diff --check` — expected exit 0.
- Fresh small replay: `python3 tools/fuzz/verify_V01.py --state orchestra/state/V01-universal-x86-arm-equality/recheck --phase default --n 1 --jobs 1 --slice-jobs 2` — expected 10 equal cases.
- Full slice replays: run the same command with `--phase default --n 100`, `--phase realistic-v1 --n 100`, `--phase realistic-v2 --n 100`, and `--phase odd-even-v1 --n 50` (sequential commands, same fresh state). Expected 1000/1000/1000/500 equal cases, with refusal counts separated as above.
- Heavy replay: `python3 tools/fuzz/verify_V01.py --state orchestra/state/V01-universal-x86-arm-equality/recheck --phase heavy --timeout 600 --jobs 1 --slice-jobs 2`.
- Direct Intel/F53 replay: `python3 tools/fuzz/verify_V01.py --state orchestra/state/V01-universal-x86-arm-equality/recheck --phase default --oracle --n 100 --timeout 60 --jobs 1`, then the same with `--phase realistic-v1`. Expected effective exact/non-render counts 956/44 and 898/102; time-dependent budgets can differ, and must not be counted as exact.
- Bounded oracle repro: same direct command with `--plugins olmdirectionalblur --indices 47` (default), `--plugins olmdistancegradation --indices 79` (both phases), or `--plugins radialblur --indices 86` (both phases); original diagnostics are in the retained rows.

next:
- Finish the remaining three heavy cells; retain final counts and resource observations.
- Follow-up oracle ticket: investigate the 76 non-PF32 non-renders separately from the 70 unsupported Smoother PF32 cells. Do not promote unrendered cells or modify plugin pixels to match an oracle failure.
