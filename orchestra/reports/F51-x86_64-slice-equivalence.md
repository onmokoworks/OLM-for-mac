status: done

summary:
- Built and cached a standalone Universal fake AE host using the unchanged F47d suites; it neither links Unicorn nor loads an AEX.
- All ten Universal Release bundles: 3,000 seed-1 cases plus every 810 committed fuzz corpus JSON replayed; 3,684 byte-identical renders, 126 identical refusals, zero differences or host errors.
- Standalone arm64 outputs match the retained F47d shared-arena host in 29 calibration cases. No production source or arithmetic changed.
- x86_64 disassembly contains SSE4.1 in nine bundles (ColorKeep uses SSE3), no AVX/AVX2/FMA instructions; fused operations call system libm. RadialBlur retains x87 long-double budget arithmetic.
- Host and all ten tested bundles are retained under `~/.cache/olm-emu/worker-F51-x86host/` and registered in `INDEX.json`.

facts:
- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the compatibility plan, the ten plugin rows of the ledger's Current Decision Matrix, and F47d's bridge/build/report. MAIN and external AEXCompat sources were only read. Branch: `orch/F51-x86_64-slice-equivalence`; starting commit: `7a43cadc`.
- Build command: `python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/F51-x86_64-slice-equivalence/bundles`, exit 0. All ten executables report `x86_64 arm64`. Actual Xcode Release commands, deployment target 11.0, optimization flags and hashes are retained in `F51-evidence/bundle-builds.json` and the comparison summaries. Each Xcode build used `-jobs 1`.
- `python3 tools/emulation/aexcompat_patches/build_F51.py`, exit 0. This C++-only executable includes `F47d-native-bridge.cpp` unchanged and reuses the existing `parameters.hpp` materializer. It creates full-frame ARGB worlds, rounds input padding to pixel alignment, packs the output, initializes it to zero, sets DEEP for PF16/PF32, and uses the retained AEX parameter declarations to validate native PARAMS_SETUP types/counts. Kira retains F47d's explicit default-ramp/raw-fixed-angle profile. The native bridge still checks input mutation, guards and suite/checkout balance. Unknown callbacks are host errors, not successful paired refusals.
- No Rust build or Unicorn startup was needed. The host's only linked libraries are `/usr/lib/libc++.1.dylib` and `/usr/lib/libSystem.B.dylib`. `arch -x86_64 /usr/sbin/sysctl -n sysctl.proc_translated` returned `1`. Each comparison explicitly launches `/usr/bin/arch -arm64` and `/usr/bin/arch -x86_64` against the same host and same Universal plugin executable.
- Host SHA-256: `7a5bc8c328503b6cd3918ae1db9b29ef9b0d0e3f274ae31904de0354aa3f0f28`. `F51-evidence/host-build.json` records source hashes, compilation command, durable paths and every bundle hash. Rebuilding while installing the bundles produced the same host hash used for the full comparisons.
- Full comparisons (both exit 0; default `--n 300`, seed 1, max-size 256, single-job execution, timeout 30 seconds, no shrinking):
  - `python3 tools/fuzz/verify_F51.py --plugins olmblur colorkeep olmcolorkey olmdirectionalblur olmdistancegradation olmkirakira olmsmoother2 --state orchestra/state/F51-x86_64-slice-equivalence/full-first`
  - `python3 tools/fuzz/verify_F51.py --plugins olmtoondilate radialblur olmsmoother --state orchestra/state/F51-x86_64-slice-equivalence/full-last`
  The two sequential runners overlapped, with at most two render processes at once. No timeout occurred. The verifier now exposes `--jobs 1` explicitly and accepts no other value.
- Generated cases: 2,874 matching renders and 126 matching refusals. Corpus: all 810 JSON cases, 810 matching renders. Corpus discovery includes the additional `olmkirakira_gate_off_T06`, nested `other_reductions`, and `olmtoondilate_T13` directories; each case is loaded with the existing generator-version/input-hash validation. No corpus was changed. Refusal equality requires identical error code, ordered refusal trace lines, and the entire output buffer; crashes/timeouts/callback failures cannot count as equality. Successful renders compare full raw bytes, not just hashes. First differing byte/stage/function: none.

| Plugin / route | Generated | Corpus | Equal renders | Equal refusals |
| --- | ---: | ---: | ---: | ---: |
| OLMBlur Smart | 300 | 39 | 339 | 0 |
| ColorKeep Smart | 300 | 0 | 300 | 0 |
| OLMColorKey Smart | 300 | 9 | 309 | 0 |
| OLMDirectionalBlur Smart | 300 | 83 | 383 | 0 |
| OLMDistanceGradation Smart | 300 | 147 | 444 | 3 |
| OLMKiraKira Smart | 300 | 111 | 398 | 13 |
| OLMSmoother2 Smart | 300 | 8 | 308 | 0 |
| OLMToonDilate Smart | 300 | 323 | 623 | 0 |
| OLMRadialBlur Smart | 300 | 61 | 346 | 15 |
| OLMSmoother v1 Classic | 300 | 29 | 234 | 95 |
| Total | 3,000 | 810 | 3,684 | 126 |

- All 95 Smoother v1 PF32 generated cases refuse identically. ColorKeep's 95 PF32 generated cases render identically. Individual input/parameter hashes, output hashes, refusal lines and outcomes are retained in `F51-evidence/full-{first,last}-cases.jsonl`; summary manifests bind them to the tested bundles and host.
- Host calibration command: `python3 tools/fuzz/calibrate_F51_host.py --rows orchestra/state/F51-x86_64-slice-equivalence/full-first/cases.jsonl orchestra/state/F51-x86_64-slice-equivalence/full-last/cases.jsonl --bundles orchestra/state/F51-x86_64-slice-equivalence/bundles`, final exit 0: 29/29 output hashes match F47d's shared-arena arm64 host. This uses seed indices 0/1/2 per plugin, excluding Smoother v1 PF32, which F47d's AEX setup rejects before native dispatch. The retained worker's hash and every comparison are in `F51-evidence/calibration-summary.json`. An initial calibration was started before the last campaign finished and raised a missing Smoother-row KeyError after 27 successful comparisons; a preflight now rejects incomplete inputs before rendering, and the final complete run passed.
- `python3 tools/fuzz/audit_F51_isa.py`, exit 0: ran `otool -arch x86_64 -tvV`, `-l`, and `-L` on all ten tested executables. Every slice has minimum OS 11.0. No VEX/EVEX-style `v*` instruction is present in the disassembled text; no AVX, AVX2 or FMA3/FMA4 instructions were found. Observed SSE4.1 instructions include `roundsd`, `insertps`, `ptest`, `blendps` and integer widening/packing; ColorKeep has SSE3 `movshdup` and no identified SSSE3/SSE4.1 instructions. No SSE4.2, BMI or POPCNT instructions from the audited families were found. Full mnemonic counts and function/address examples are retained in `F51-evidence/isa-summary.json`; raw disassembly hashes allow regeneration checks. Linear text disassembly can also decode inline data, so the full mnemonic inventory is not a claim that every decoded instruction executes.
- FMA library call-site counts: Blur 20, ColorKey 76, DirectionalBlur 37, DistanceGradation 20, Kira 56 `fma` + 3 `fmaf`, Smoother2 3, RadialBlur 56; ColorKeep/ToonDilate/Smoother v1 have none. All external dependencies listed by `otool -L` are system frameworks/libraries. `clang -arch x86_64 -mmacosx-version-min=11.0 -### -c tools/emulation/aexcompat_patches/F51-plugin-host.cpp` selects `-target-cpu penryn` (retained command output). The bundle build logs use `-target x86_64-apple-macos11.0`, with no explicit AVX/FMA architecture switches.
- RadialBlur's `long double` expressions at `mac/OLMRadialBlur/OLMRadialBlur.cpp:1117` onward belong to its admission/work-budget calculation; x86_64 contains corresponding x87 `fldt`/`fstpt`. All measured RadialBlur refusals and outputs agree. No change was justified by these observations.
- Durable install: `python3 tools/emulation/aexcompat_patches/build_F51.py --bundles orchestra/state/F51-x86_64-slice-equivalence/bundles`, exit 0. Worker and bundles are registered together in `~/.cache/olm-emu/INDEX.json`, entry `worker-F51-x86host`. No reference worker was rebuilt. The subsequent cached-path n1/all-ten smoke passed 10/10 matching renders.
- Python compilation of the four new scripts and `git diff --check` pass. No production plugin, core, release gate or ledger file changed, so the conditional `verify_F47d.py` AEX revalidation for modified plugins was not triggered. F47d was used for transport calibration instead.
- Cleanup: disposable Xcode build/product trees were removed after durable installation; scratch retains 20,869,851 bytes of logs, disassembly and results. All started commands have exited; no background render/build remains. Nothing was written to `/tmp` by the recipes; temporary compiler paths were redirected into ticket scratch.

inference:
- The requested finite generated/corpus campaign establishes byte-identical arm64/x86_64 bundle behavior and identical admission decisions under the F47d fake-host contract. It does not establish all-input equivalence or native AE/Windows correctness.
- The bundle code does not impose an AVX/FMA hardware requirement. Its observed direct SIMD requirement reaches SSE4.1 (SSE3 for ColorKeep), consistent with the toolchain's Penryn baseline. System libm owns the CPU dispatch for `fma`/`fmaf`; an older physical Intel Mac was not available in this run. Rosetta is the measured x86_64 runtime.
- The x87 versus arm64 long-double distinction remains a possible boundary outside these cases; no measured refusal or pixel difference justifies changing the budget calculation. Selected secondary layers, arbitrary custom Kira ramps, ROI/nonzero origins, independent output padding, persistent sequence state, GPU and real AE suites remain outside the retained F47d contract.

changed_files:
- `tools/emulation/aexcompat_patches/F51-plugin-host.cpp`
- `tools/emulation/aexcompat_patches/build_F51.py`
- `tools/fuzz/verify_F51.py`
- `tools/fuzz/calibrate_F51_host.py`
- `tools/fuzz/audit_F51_isa.py`
- `orchestra/reports/F51-x86_64-slice-equivalence.md`
- `orchestra/reports/F51-evidence/*`

verify:
```sh
# Full fresh build and comparison (single-job, all ten, all corpus):
python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/F51-x86_64-slice-equivalence/bundles
python3 tools/emulation/aexcompat_patches/build_F51.py --bundles orchestra/state/F51-x86_64-slice-equivalence/bundles
python3 tools/fuzz/verify_F51.py --jobs 1
# Expected exit 0: equal_render=3684, equal_refuse=126, no differences.

# Reuse durable tested bundles instead of rebuilding:
python3 tools/fuzz/verify_F51.py --jobs 1 \
  --bundles "$HOME/.cache/olm-emu/worker-F51-x86host/bundles"
# Same expected counts; source/corpus changes require a new evidence binding.

python3 tools/fuzz/calibrate_F51_host.py \
  --rows orchestra/state/F51-x86_64-slice-equivalence/cases.jsonl \
  --bundles "$HOME/.cache/olm-emu/worker-F51-x86host/bundles"
# Expected exit 0: 29/29 equal; needs retained worker-F47d.

python3 tools/fuzz/audit_F51_isa.py \
  --bundles "$HOME/.cache/olm-emu/worker-F51-x86host/bundles"
# Expected: no v* instructions; extensions/call counts above.
git diff --check
```

next:
- No remaining work for the requested finite slice campaign. Optional follow-up: physical pre-FMA Intel validation, targeted RadialBlur admission-boundary cases, or extension of the F47d host contract to secondary layers/ROI/custom ramps.
