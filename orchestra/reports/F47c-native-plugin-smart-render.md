status: done

summary:
- Added an opt-in SDK-typed native OLMBlur Smart bridge at the existing Rust ClassicHost Smart dispatch boundary.
- Native setup, SMART_PRE_RENDER, SMART_RENDER and setdown run from the built arm64 bundle; arena parameters/worlds and the output hash/report path are shared with the AEX session.
- Seed 1/n100: 100 raw-byte exact, 0 differences/refusals/harness errors/timeouts; PF8 31, PF16 34, PF32 35.
- Added `--candidate plugin-bundle --plugin-bundle PATH` for OLMBlur Smart; default source candidate unchanged. Plugin sources, release gates, ledger, MAIN and cached sources/workers unchanged.
- This is a shared-arena bridge requiring AEX setup, not a standalone native resident backend. ColorKey was not attempted.

facts:
- Read AGENT_GUIDE.md, GOTCHAS.md, F47b report/implementation, compatibility plan, targeted OLMBlur ledger rows, OLMBlur Smart source and cached Rust host/session sources. F47b observed zero setup AcquireSuite calls; it did not establish a render suite log.
- `bash scripts/setup_ae_sdk_links.sh`: succeeded in this worktree.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMBlur --scratch orchestra/state/F47c-native-plugin-smart-render/bundles`: exit 0; Universal x86_64/arm64 bundle. Only arm64 was executed. Bundle Mach-O SHA-256 `cc5359a9937c9e778fcb77bcc8036433767c13bffc5c78b73f1854344a282047`.
- `python3 tools/emulation/aexcompat_patches/build_F47c.py`: exit 0. Final clean Rust Release/offline/locked build used one job, with 54% free memory from `memory_pressure` before compilation. Eight shared ABI sizes/offsets consumed by the bridge pass SDK static assertions. The compiler reports one pre-existing dead-code warning. Final worker SHA-256 `893f92de3feada4ad66e576a47c378ede762190278d836c70ba3a7e1a8c140b4`.
- Two clean worker builds succeeded. The first anchor passed before native snapshot guard checking was added; all retained evidence and the n100 campaign use the second build with guard checks. No numerical hypothesis was refuted.
- `python3 tools/emulation/aexcompat_patches/verify_F47c.py`: exit 0. 32x32 PF8 anchor, input padding rounded from 7 to 8 bytes with 0xA5 fill, packed output: 4096 output bytes exact. AEX/native output SHA-256 `c923c0b37aa3767e0388f7388ea680dc08f79433fdff1986b8a06a6f280bcaf9`; input SHA-256 `a6ed198321a84d641a39719bf923e817f3b1b0f0d1a744afc880bae61ebe3be1`, so this is not a no-effect copy.
- The anchor's AEX output is byte-identical to cached F47's AEX output. The adapter deliberately given the old F47 worker reports `harness_error`, proving it does not accept an ignored native switch as a native result.
- Native selectors 1/4/5/23/24/8/3 (GLOBAL_SETUP/PARAMS_SETUP/SEQUENCE_SETUP/SMART_PRE_RENDER/SMART_RENDER/SEQUENCE_SETDOWN/GLOBAL_SETDOWN) each return 0 for the anchor and all 100 cases. Each render registers five non-input parameters, checks out/checks in five parameters, acquires/releases WorldSuite2 once and calls GetPixelFormat twice.
- The exact fuzz command in `verify` below completed seed 1/n100, jobs 1, in 2.7492 seconds: 100 AEX successes and 100 native byte-exact outputs. Depth counts: 8=31, 16=34, 32=35. All cases carry native selector/callback traces and both output hashes. Four outputs equal their inputs; 96 do not. First mismatch: none. Classification for every case: raw-byte exact; no differing case requires numerical attribution.
- Retained full fuzz report SHA-256 `73df0fefc08778693c356efe6eb9477f50d019016e07f48233744ed50db14ec0`. Evidence lives in `orchestra/reports/F47c-evidence/`.
- `OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F47c-native-plugin-smart-render/tests" TMPDIR="$PWD/orchestra/state/F47c-native-plugin-smart-render" python3 tools/fuzz/test_framework.py`: 14 tests, OK, 1 skipped. Python compilation of the five touched/new Python modules and `git diff --check` pass.
- Final staged diff check found trailing spaces in the verbatim memory_pressure log; the retained text was whitespace-normalized without changing its values, and the final full-ticket diff check passes.
- Scratch is about 10 MiB. Rust source/target trees, no-space cache symlink, native object/archive files and generated Xcode project were removed. The worker, bundle, logs and small evidence remain. No background process is retained.

inference:
- The tested boundary demonstrates native bundle Smart output agreement for the declared anchor and seeded corpus. It does not establish general bit-exactness, native AE/Windows behavior or x86_64 execution.
- Both routes use the same Rust arena allocation, applied parameter bytes, input rowbytes/padding, initial output bytes and final checksum/report implementation. Native pointers must refer to snapshots, not Unicorn guest addresses; active output bytes are copied back into the shared arena after native guard checks.
- The candidate still executes AEX setup and host frame setup/setdown. Native global/sequence lifetime is per render. Arbitrary or secondary-layer parameters and persistent native sequence state are outside the OLMBlur bridge's scope.
- Input padding is rounded up to pixel alignment because the existing resident allocator rejects odd byte strides. Output is packed on both sides; generated output_padding values are intentionally unused and reported in provenance. Independent output padding, ROI and nonzero origins are not validated.
- Host handle/memory suites and Iterate/PixelFormat suites are unnecessary for the observed OLMBlur Smart route. Their absence is not a claim of broader host support.

implemented_functions:
- InteractCallbacks: add_param (native count/type validation against AEX definitions), checkout_param, checkin_param, abort, progress.
- PreRenderCallbacks: checkout_layer for primary slot/ID 0 using shared world dimensions/extent.
- SmartRenderCallbacks: checkout_layer_pixels, checkout_output, checkin_layer_pixels for primary ID 0. Host-owned worlds survive through selector return.
- SPBasicSuite: AcquireSuite/ReleaseSuite for PF World Suite v2, with balance checking and logging.
- PF_WorldSuite2: GetPixelFormat for the two known worlds, PF8/PF16/PF32.
- Utility copy: whole-frame active pixels, equal geometry, independent strides, no conversion/rectangle support.

stubbed_or_unsupported:
- PF_WorldSuite2 NewWorld/DisposeWorld: diagnostic + error 516 + render failure flag.
- Utility new_handle/lock_handle: diagnostic + null + failure flag; handle_size: diagnostic + zero + failure flag; unlock_handle/dispose_handle: diagnostic + failure flag. They were not called in the retained runs.
- PixelFormatSuite, Iterate8/16/Float suites, HandleSuite, WorldSuite1 and other suites: diagnostic, cleared suite pointer, kSPSuiteNotFoundError and failure flag on AcquireSuite. They were not requested in the retained runs.
- Other optional utility/callback members remain null, not callable stubs. GPU/census/trace requests fail explicitly at the Rust bridge. The host is intentionally limited to this audited plugin path.

changed_files:
- tools/emulation/aexcompat_patches/F47c-native-bridge.cpp
- tools/emulation/aexcompat_patches/F47c-native-ffi.rs
- tools/emulation/aexcompat_patches/F47c-native-render.rs
- tools/emulation/aexcompat_patches/F47c-native-host.md
- tools/emulation/aexcompat_patches/build_F47c.py
- tools/emulation/aexcompat_patches/verify_F47c.py
- tools/fuzz/adapters/plugin_bundle.py
- tools/fuzz/adapters/public.py (optional session arguments/observation hooks; defaults unchanged)
- tools/fuzz/run.py
- orchestra/reports/F47c-native-plugin-smart-render.md
- orchestra/reports/F47c-evidence/{build.json,anchor.json,fuzz.json,summary.json,bundle-builds.json,memory-pressure.txt,framework-tests.txt}

verify:
```sh
# Existing scratch artifacts: expected exit 0, exact anchor and unchanged AEX output.
python3 tools/emulation/aexcompat_patches/verify_F47c.py

# Reproduce from committed recipes after scratch cleanup:
bash scripts/setup_ae_sdk_links.sh
python3 tools/fuzz/build_F47_bundles.py --plugins OLMBlur --scratch orchestra/state/F47c-native-plugin-smart-render/bundles
python3 tools/emulation/aexcompat_patches/build_F47c.py
python3 tools/emulation/aexcompat_patches/verify_F47c.py

python3 tools/fuzz/run.py --plugin olmblur --candidate plugin-bundle \
  --plugin-bundle orchestra/state/F47c-native-plugin-smart-render/bundles/xcode/OLMBlur/products/OLMBlur.plugin \
  --worker orchestra/state/F47c-native-plugin-smart-render/aex-guest-worker \
  --seed 1 --n 100 --jobs 1 --case-timeout 10 --budget-minutes 10 \
  --shrink-attempts 0 --shrink-seconds 0 \
  --scratch orchestra/state/F47c-native-plugin-smart-render/fuzz \
  --corpus orchestra/state/F47c-native-plugin-smart-render/corpus \
  --report orchestra/state/F47c-native-plugin-smart-render/fuzz.json
# Expected: complete; aex_ok=100, smart_exact=100, pixel_mismatch_cases=0.
# Build hashes can vary with toolchain/build metadata; output hashes must match.

git diff --check
```

next:
- Separate ticket: remove the AEX setup dependency via a standalone native parameter/session backend while preserving this shared-arena comparison anchor.
- Extend host world allocation/handles only when another plugin actually requests them, then add ColorKey and persistent-session lifecycle coverage.
- Independently validate output padding, unsupported layouts and native guard failure injection; do not infer them from the seed corpus.
