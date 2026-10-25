status: blocked
summary:
- Implemented OLM_REFERENCE_BUILD for all six requested plugins; fast remains the default.
- Added streaming native reference/fast differential testing and the fuzz runner's --reference-build option.
- All retained seed1 n300 fast output hashes are unchanged; all reference n100 output hashes match fast.
- Native runs have no numerical mismatches; unavailable/refused renders are counted separately.
- Acceptance remains blocked by inherited RadialBlur C49 oracle replay failure and a literal heavy-preset reference timeout at HD.

facts:
- History: DirectionalBlur 4dd1406c / merge f05c36af; RadialBlur merge 738aed52; Blur ec6cc82c, ColorKey 5602e329, Smoother 4ebcfd7d / merge c7e63a63; KiraKira 651bc587 / merge 4a0623d2.
- Reference forms: DirectionalBlur scalar helpers/scatter and sequential rowdriver, Clang rotation optimization disabled; RadialBlur scalar scatter with original channel order and the trig table retained; Blur six sequential parts; ColorKey per-pixel Lab conversion; Smoother original full 4 KiB virtual stack; KiraKira original sequential warp plus serial shared helper.
- DirectionalBlur and Blur now honor OLM_PARALLEL_MAX=1 without changing their default caps (8 and 2). Reference builds require no environment setting.
- `python3 orchestra/reports/R10-evidence/oracle.py --plugin <adapter> --label <label>` executes reference seed1 n100 and fast seed1 n300, one process at a time. DirectionalBlur/RadialBlur used the equivalent explicit commands preserved in the logs/reports. Contract-route results:

| Plugin / label | Reference n100 | Fast n300 | Prior fast hashes |
| --- | --- | --- | --- |
| olmdirectionalblur / directional | 100 Smart exact | 298 exact, 2 oracle budgets | unchanged, both routes |
| radialblur / radial | 85 exact, 14 oracle rejects, 1 budget | 275 exact, 20 rejects, 5 budgets | unchanged, both routes |
| olmblur / blur | 100 Smart exact | 300 Smart exact | unchanged, both routes |
| olmcolorkey / key | 100 Smart exact | 300 Smart exact | unchanged, both routes |
| olmsmoother / smooth | 65 Classic exact, 35 PF32 rejects | 205 exact, 95 PF32 rejects | unchanged, both routes |
| olmkirakira / kira | 97 Smart exact, 3 original rejects | 287 exact, 13 original rejects | unchanged, Smart (P07a retained route) |

- `hash-comparisons.json` contains zero changed hashes in all twelve comparisons. Refused routes have no output hash; these are not claimed as rendered images. Reference n100 versus fast is checked on both routes for every plugin. Classic mismatches outside the contract route remain in the complete evidence.
- `python3 tools/perf/ref_vs_fast.py --plugin <adapter>` built both source hosts and compared output bytes and rectangles. Measured runs (RadialBlur procedural run is not literal heavy-preset coverage):

| Plugin | Cases (small / HD / UHD) | Exact comparisons | Matching refusals | Seconds |
| --- | --- | --- | --- | --- |
| DirectionalBlur (final source/heavy presets) | 200 / 20 / 5 | 675 | 0 | 645.027 |
| RadialBlur (initial procedural parameters) | 200 / 20 / 5 | 675 | 0 | 845.422 |
| Blur | 200 / 20 / 5 | 675 | 0 | 88.221 |
| ColorKey | 200 / 20 / 5 | 225 | 0 | 76.538 |
| Smoother | 200 / 20 / 5 | 156 | 69 (PF32) | 47.370 |
| KiraKira | 200 / 20 / 5 | 648 | 27 (9 small cases × 3 caps) | 63.053 |

- Final DirectionalBlur run uses actual caps 1/2/8, all depths and heavy HD/UHD presets. Its 645 seconds slightly exceeds ten minutes. Earlier logs are retained but superseded by final-directional.
- Initial DirectionalBlur/RadialBlur sampling used `--no-large-corpus --no-cycle-depth --max-height 2160 --parallel 1 2 8`. The later default harness uses 64x64 small bounds, guarantees each large-frame depth, and uses retained P00b presets with the heavy preset at each depth in both large phases. Non-threaded plugins now run once by default. Large fixed-frame pixels tile fuzz-generated payloads; they are not independently randomized per coordinate.
- KiraKira additional `--small 250 --hd 0 --uhd 0 --scratch orchestra/state/R10-reference-fast-split/kira-small-coverage`: 711 exact comparisons (237 successful small cases × 3 caps), 39 matching refusals, zero mismatches.
- `python3 orchestra/reports/R10-evidence/replay.py --plugin <adapter>`: DirectionalBlur 303/303, Blur 139/139, ColorKey 44/44, Smoother 303/303 match saved results. KiraKira 387/387 match saved results.
- RadialBlur: nested/realistic corpora 190/190 true; root 60/61 true on two runs. The original AEX stops at RIP 0x180002cc3 in C49_seed1_case000117; candidate raw SHA remains `6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d`. A standalone fast control replays true. P05b explicitly records the identical root-corpus blocker. No corpus or worker was rewritten.
- `python3 tools/fuzz/build_F47_bundles.py --plugins <name> --scratch orchestra/state/R10-reference-fast-split/release-<label>`: all six fast Universal bundles build with arm64 and x86_64.
- `python3 orchestra/reports/R10-evidence/perf.py --plugin <adapter>` uses `lockf -k ~/.cache/olm-emu/bench.lock` and the unchanged P00b driver. Heavy selector timings: Blur 1.452/1.456/1.477 s (prior 1.612/1.753/1.691); ColorKey 0.755/0.767/0.767 s; Smoother PF8/PF16 1.490/1.426 s, expected PF32 refusal. DirectionalBlur heavy full-frame wall times 1.354/1.320/1.377 s versus prior 1.411/1.504/1.462; RadialBlur heavy eighth-resolution wall times 17.187/16.783/17.073 s, consistent with P05b's 16.8–17.4 s. KiraKira default selectors 0.260/0.239/0.241 s and corpus05 0.259/0.258/0.246 s, versus P07a approximately 0.24–0.25 s.
- `python3 orchestra/reports/R10-evidence/helpers.py`: both builds pass 385 row/grain/cap combinations plus three Blur cap combinations. Reference callbacks assert caller-thread identity; all callbacks assert downward rounding and exactly-once visitation.
- Additional Smoother `--small 400 --hd 0 --uhd 0`: 271 successful comparisons, 129 matching PF32 refusals. All six plugins also ran `--small 40 --hd 0 --uhd 0 --max-size 3840 --max-height 2160`: exact/refusal counts DirectionalBlur 120/0, RadialBlur 40/0, Blur 120/0, ColorKey 40/0, Smoother 24/16, KiraKira 111/9; zero mismatches.
- Final RadialBlur command: `python3 tools/perf/ref_vs_fast.py --plugin radialblur --jobs 1 --scratch "$PWD/orchestra/state/R10-reference-fast-split/final-radial-literal"`. Completed 200 small plus 15 HD comparisons exactly, then the reference PF8 1920x1080 render timed out after 180 seconds at sequence index 215 (overall elapsed 243.269 seconds). No comparison exists for this timed-out case; remaining five HD/five UHD cases are unverified. The literal P00b point parameters are now preserved. An earlier rescaled-point final-radial run was interrupted, its child reaped and its results explicitly marked superseded. Other plugins have no point parameters in these presets, so their large results remain applicable.
- Final harness lifecycle smoke: DirectionalBlur four small cases, 12 exact comparisons; ColorKey four small cases, four exact comparisons. No stale output survives between cases.
- Memory checks stayed above 30% free (observed 53–63% during these runs). Scratch stayed below 5 GiB; final cleanup left 45,598,923 bytes, with 58% free memory and no remaining worker processes. Regenerable host/bundle trees were removed; retained evidence is compressed in R10-evidence.

inference:
- Measured default fast behavior is unchanged. Native reference/fast equality is not new AE-exact evidence.
- The C49 original-worker failure is inherited, not a reference output mismatch. Its inconsistent standalone/full-corpus behavior remains unexplained here.
- RadialBlur literal heavy-preset acceptance and the roughly ten-minute full-suite target are not established. A timeout is incomplete evidence, not a numerical mismatch. No per-case correction or timeout waiver was applied.

changed_files:
- core/dblur_rowdriver.cpp, core/dblur_rotate.cpp
- core/olmblur_parallel_parts.h, core/kirakira_warp.h, core/olm_parallel.h
- mac/OLMRadialBlur/OLMRadialBlur.cpp, mac/OLMRadialBlur/RadialScatterSIMD.h
- mac/OLMColorKey/OLMColorKey.cpp, mac/OLMSmoother/Mac/OLMSmoother_port.cpp
- tools/fuzz/adapters/public.py, tools/fuzz/adapters/radialblur.py, tools/fuzz/run.py
- tools/perf/ref_vs_fast.py, tools/perf/README.md
- orchestra/reports/R10-evidence/, orchestra/reports/R10-reference-fast-split.md

verify:
- `python3 tools/perf/ref_vs_fast.py --plugin olmblur`: expected 675 exact comparisons, zero mismatches/refusals, including the heavy HD/UHD presets.
- `python3 orchestra/reports/R10-evidence/helpers.py`: expected both builds' assertions pass.
- RadialBlur final command above: expected the recorded heavy reference timeout under the 180-second per-case budget; this is a blocker, not an acceptance pass.
- `python3 tools/perf/ref_vs_fast.py --plugin olmdirectionalblur --small 4 --hd 0 --uhd 0 --jobs 1`: expected 12 exact, zero refusals/mismatches. Use `--plugin olmcolorkey` for four exact raw-stream comparisons.
- Oracle/replay/build/performance commands above reproduce the corresponding checks. All scripts put scratch in this worktree; tools/perf/README.md documents bounded smoke and large-geometry options.
- `python3 orchestra/reports/R10-evidence/archive.py`: collects compact evidence and recomputes baseline/reference hash comparisons; expected zero different hashes. Oracle timeouts can vary; the retained RadialBlur C49 replay blocker must not be called a pass.

next:
- Follow-up: investigate the faithful RadialBlur heavy-preset cost and establish an explicit runtime budget before completing all HD/UHD comparisons. Do not infer equality for unrendered cases.
- Resolve or explicitly waive the inherited RadialBlur oracle replay blocker in a separate ticket; do not change the retained oracle or rebaseline the corpus within R10.
