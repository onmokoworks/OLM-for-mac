status: blocked

summary:
- Extended the shared-arena native bridge/adapter to all ten bundles, including Smoother v1 Classic, with observed suites, default Kira ramps and explicit unknown-suite failure.
- Built all ten real Xcode projects in Universal Release; plugin sources, default candidate, release gates and ledger unchanged.
- Final arm64 seed 1/n100 per plugin: 901 AEX byte-exact, 93 rejected, 1 timeout, 5 outputs without an available AEX comparison; zero pixel mismatches.
- All 906 returned bundle outputs equal source-candidate hashes; 58 refusals and 1 timeout agree with source. ColorKeep PF32 adds 35 refusals due to its production world-flag guard.
- Blocked boundaries: ColorKeep PF32 needs a separately authorized plugin/fixture-contract fix; Rosetta worker crashes inside AEX process attach before native rendering.

facts:
- Read AGENT_GUIDE.md, GOTCHAS.md, compatibility plan, the targeted decision-matrix rows for these plugins, F47c implementation/report, native entry points and source adapters. No numerical hypothesis was refuted; each callback extension followed a new observed suite/callback boundary.
- `python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/F47d-native-plugin-all/bundles`: exit 0; all ten report `x86_64 arm64`. It builds the real Release projects, with `-jobs 1`, `ARCHS=arm64 x86_64`, `ONLY_ACTIVE_ARCH=NO`, optimization 2 and deployment target 11.0. Commands and executable SHA-256 values are in `F47d-evidence/bundle-builds.json` and `bundle-hashes.json`.
- Initial `python3 tools/fuzz/verify_F47d.py`: completed all ten source-candidate seed-1/n100 campaigns and initial bundle discovery campaigns. Source candidate includes its existing Classic and Smart routes; only Smart is paired here except Smoother v1 Classic. Source Classic mismatches/no-write/refusals are outside this ticket's paired-route result.
- Initial suite failures were explicit and logged: ColorKeep Iterate8/16/Float; DirectionalBlur/Kira AEGP Utility registration; Kira HandleSuite. Further boundaries were DirectionalBlur's unavailable optional Noise Layer and Smoother v1 passing the world embedded in params[0] to GetPixelFormat. Retained samples: `F47d-evidence/discovered-boundaries.json`.
- Final builds, each exit 0:
  `python3 tools/emulation/aexcompat_patches/build_F47d.py --state orchestra/state/F47d-native-plugin-all/checked`
  and the same command with `--target x86_64-apple-darwin`.
  Both checked `memory_pressure` before Cargo: 52% free. Each used one Rust/CMake build job and passed eight SDK ABI size/offset assertions. No more than two build/emulator processes were run together. Only the existing Rust dead-code warning remained.
- Final arm64 worker SHA-256: `8057af6313d851f7e00939400b6b64a302fd00addc8f22c0812715216c49c35b`.
  Final x86_64 worker SHA-256: `958b7925b033e49b3d5f4e7c40953435a2b1a7b906d224413a779cd0107717d8`.
  Compiled C++/Rust source hashes match both manifests. The arm64 manifest's documentation-only hash predates the final world-flag explanation; this is annotated in retained evidence.
- Final campaign command:
  `python3 tools/fuzz/verify_F47d.py --candidates plugin-bundle --worker orchestra/state/F47d-native-plugin-all/checked/aex-guest-worker --plugins olmkirakira olmdirectionalblur olmsmoother olmblur colorkeep olmcolorkey olmsmoother2 olmtoondilate olmdistancegradation radialblur`
  Exit 0, 100 completed per plugin, seed 1, jobs 1, per-case timeout 10 seconds, no shrinking. Each plugin has PF8=31/PF16=34/PF32=35. All final traces lack unsupported/invalid-callback errors.
- `python3 tools/fuzz/summarize_F47d.py`: exit 0. It asserts identical generated input hashes, parameters, geometry and depth across source/bundle cases, and identical AEX hashes wherever both campaigns return an AEX output. It retains every case's status, output hashes, trace, refusal guards and difference classification. First pixel mismatch: none. All differences are classified; no unresolved bundle/source-output difference remains.

| Plugin / route | Exact against AEX | Other final bundle results | Source comparison / boundary |
| --- | ---: | --- | --- |
| OLMBlur Smart | 100 | none | All 100 outputs identical; works |
| ColorKeep Smart | 65 | 35 rejected, all PF32 | Source returns 100 exact; blocked PF32 world-flag contract |
| ColorKey Smart | 100 | none | All 100 outputs identical; works |
| DirectionalBlur Smart | 100 | none | All 100 outputs identical; works |
| DistanceGradation Smart | 95 | 1 timeout, 1 rejection, 3 uncompared outputs | All 98 outputs identical; same timeout/refusal; AEX limits block 5 comparisons |
| KiraKira Smart | 97 | 3 rejected | All 97 outputs identical; same 3 source/AEX refusals; default-ramp profile only |
| Smoother2 Smart | 100 | none | All 100 outputs identical; works |
| ToonDilate Smart | 100 | none | All 100 outputs identical; works |
| RadialBlur Smart | 79 | 19 rejected, 2 uncompared outputs | All 81 outputs identical; same 19 source refusals; AEX budget variation |
| Smoother v1 Classic | 65 | 35 PF32 AEX rejections before native dispatch | All PF8/PF16 outputs identical; AEX does not advertise PF32 |

- ColorKeep first additional refusal: seed 1/index 2, PF32, `ColorKeepValidateWorldPair:world-flags-or-bounds@216`. The cached worker's `FramePixelFormat::world_flags` sets DEEP for PF16/PF32. Native OLMBlur, KiraKira and Smoother2 also expect DEEP for PF32. ColorKeep instead requires DEEP only at PF16; `tools/fuzz/harnesses/colorkeep_main.cpp` constructs that different header, masking the conflict in source runs. The bridge preserves the arena header. This is a real plugin/source-fixture input-contract bug in this shared-host comparison, not a pixel-rounding or build-flag difference. It is not proof about native AE's actual world flags. No plugin-specific header rewrite was introduced.
- DistanceGradation AEX-unavailable indices: 10/90 timeout, 31/53/55 rejected. Candidate 10 also times out, 53 refuses, and 31/55/90 return source-identical outputs. Kira's three refusals include `SmartRender:tuple-or-source` and agree with the source campaign.
- RadialBlur AEX times out at indices 4/62. Source's AEX succeeds at 62, so source has 80 exact versus bundle's 79; both native outputs at 62 have the same SHA-256. This count difference is an oracle timeout, not a bundle difference. All 19 candidate refusals match source, including five cases where AEX renders successfully.
- Rosetta: `arch -x86_64 /usr/bin/uname -m` returns `x86_64`; Rust x86_64 target is installed; `file` confirms the final worker is Mach-O x86_64. The n100 OLMBlur command in verify completed, but both AEX and candidate processes return -11 for all 100 cases, with no native selector trace. Worker usage/help executes. The macOS crash report has `translated=true`, EXC_BAD_ACCESS/SIGSEGV and frames `resume_all_vcpus_x86_64 -> uc_emu_start -> GuestEngine::run_process_attach_addresses -> load_primary`. Its worker UUID `81B09303-0B62-3EA4-AA84-A57F2CE59F99` matches `dwarfdump --uuid` on the built worker. No OLMBlur bundle appears in that crash's image list. Therefore no x86_64 bundle-render result is claimed.
- Old-worker negative check using cached F47, OLMBlur seed 1/n1: AEX succeeds, native adapter returns `harness_error` because the worker ignores the native switch. It does not misreport AEX bytes as a native result.
- Final framework test command in verify: 14 tests, OK, 1 skipped (2.641 seconds). Python compilation of the seven modified/new Python modules and `git diff --check` pass. Generator check: all ten source/bundle generators produce identical seed-1 cases for indices 0..99.
- Scratch after cleanup is 62 MiB. Disposable Rust source/target trees and no-space cache symlinks were removed by the recipes; object/archive files, Xcode object/PCH trees and superseded worker binaries were deleted. Final workers, Universal bundles and diagnostic logs/reports remain. No background process remains.

inference:
- Under the declared scalar/default-ramp inputs, all successful native outputs agree with source; no final numerical bridge or Release-build-flag issue was observed. This finite corpus is not all-input or native AE/Windows proof.
- The bridge still depends on AEX setup/session allocation. That dependency blocks Rosetta before any native plugin invocation; fixing the emulator/JIT or removing that dependency needs a follow-up.
- Kira's native arbitrary defaults are host-owned handles produced by native PARAMS_SETUP. The explicit `kirakira-default-ramps` profile reproduces the existing source adapter's default-only semantics and raw-fixed ANGLE-to-native-slider conversion. Custom arbitrary payloads are not marshalled or claimed.
- Input padding is rounded to pixel alignment, output is packed, and generated output_padding is unused. Secondary selected layers, ROI/nonzero origins, independent output padding, persistent native sequence state, GPU, census/trace, UI event execution and allocation-failure coverage remain outside this proof.
- No further permitted bridge change resolves the ColorKeep flag conflict without changing the shared input contract or plugin source. The latter is explicitly forbidden by this ticket, hence overall status blocked despite the completed implementation/campaign deliverables.

changed_files:
- tools/emulation/aexcompat_patches/F47d-native-{bridge.cpp,ffi.rs,render.rs,host.md}
- tools/emulation/aexcompat_patches/build_F47d.py
- tools/fuzz/adapters/plugin_bundle.py
- tools/fuzz/adapters/radialblur.py (optional session arguments/observation hooks; default unchanged)
- tools/fuzz/build_F47_bundles.py
- tools/fuzz/run.py
- tools/fuzz/verify_F47d.py
- tools/fuzz/summarize_F47d.py
- orchestra/reports/F47d-native-plugin-all.md
- orchestra/reports/F47d-evidence/*

verify:
```sh
python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/F47d-native-plugin-all/bundles
python3 tools/emulation/aexcompat_patches/build_F47d.py --state orchestra/state/F47d-native-plugin-all/checked
python3 tools/fuzz/verify_F47d.py --worker orchestra/state/F47d-native-plugin-all/checked/aex-guest-worker
python3 tools/fuzz/summarize_F47d.py
# Expected: all ten n100 campaigns complete, no bundle pixel mismatches,
# all returned bundle/source hashes identical; ColorKeep has 35 PF32 rejections.
# Oracle timeout counts can vary with load; retained exact/blocked counts are above.
# summarizer asserts paired input and available AEX hash agreement.

python3 tools/emulation/aexcompat_patches/build_F47d.py --state orchestra/state/F47d-native-plugin-all/checked --target x86_64-apple-darwin
python3 tools/fuzz/run.py --plugin olmblur --candidate plugin-bundle \
  --plugin-bundle orchestra/state/F47d-native-plugin-all/bundles/xcode/OLMBlur/products/OLMBlur.plugin \
  --worker orchestra/state/F47d-native-plugin-all/checked/x86_64/aex-guest-worker \
  --seed 1 --n 100 --jobs 1 --case-timeout 10 --budget-minutes 10 \
  --shrink-attempts 0 --shrink-seconds 0 \
  --scratch orchestra/state/F47d-native-plugin-all/rosetta \
  --corpus orchestra/state/F47d-native-plugin-all/rosetta-corpus \
  --report orchestra/state/F47d-native-plugin-all/rosetta.json
# Observed: 100 AEX rejects and 100 candidate rejects, returncode -11,
# no native selector trace. This reproduces the Rosetta blocker, not a pass.

OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F47d-native-plugin-all/tests-final" \
TMPDIR="$PWD/orchestra/state/F47d-native-plugin-all" python3 tools/fuzz/test_framework.py
# Expected: 14 tests, OK, 1 skipped.
git diff --check
```

next:
- Authorize a ColorKeep PF32 world-flag contract ticket: reconcile its production validation and source fixture with the shared typed-world contract; preserve all 35 refusal witnesses and rerun n100. Do not disguise the mismatch with per-plugin bridge-header changes.
- Isolate the x86_64/Rosetta Unicorn process-attach crash, or make the native session backend independent of AEX setup, then repeat the OLMBlur x86_64 comparison.
- Separate follow-ups for existing source/AEX refusals and oracle budgets, custom Kira arbitrary ramps, selected secondary layers and broader layouts. No plugin math changes are proposed by this ticket.
