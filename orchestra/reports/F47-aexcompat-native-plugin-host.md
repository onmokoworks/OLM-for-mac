status: blocked

summary:
- Partial prototype: F47 worker loads all three real Universal Mac bundles and resolves PiPL-selected EffectMain on arm64.
- Native AE selectors/suite callbacks and session rendering are not implemented; this is not a functioning native render host.
- No plugin-bundle fuzz adapter or seed-1/n100 comparisons were run. Numerical agreement is unmeasured.
- Build recipe, loader patch, SDK ABI probe, design note and evidence are committed; no plugin, gate or ledger edits.
- Worker registered with explicit load-only capability, with the default fuzz candidate unchanged.

facts:
- Copied `/Users/onmk/.cache/olm-emu/src-F46/reference-guest` to `/Users/onmk/.cache/olm-emu/src-F47`; original AEXCompat trees and MAIN were not edited.
- Read AGENT_GUIDE, emulation GOTCHAS, compatibility plan and targeted ledger references. No plugin numerical changes were attempted.
- `python3 tools/fuzz/build_F47_bundles.py`: exit 0; OLMBlur, OLMColorKey and OLMRadialBlur each report `x86_64 arm64`. Production projects contain only Debug. Disposable copies define Release with O2, both architectures, signing disabled, testability disabled, original FP flags retained. Nothing was installed into AE.
- Build-script development exposed relocated relative source paths, header search paths split at spaces, and a relative Info.plist path. Each was fixed in the disposable-project recipe; the final three builds succeed. These are build-harness findings, not plugin bugs.
- `python3 tools/emulation/aexcompat_patches/build_F47.py`: exit 0; memory free 58% before build; Cargo offline/locked/jobs=1 Release finished in 2m43s, with one existing dead-code warning. Worker SHA-256: `d637fb2d0f9e8f51470faca4a3c39b028a2db2f7997c89d65b07a60dacd4eeec`.
- Worker installed at `/Users/onmk/.cache/olm-emu/worker-F47-nativeplugin/aex-guest-worker`. INDEX entry `worker-F47-nativeplugin` says `native-plugin-load-only`; source/build manifests retained.
- `python3 tools/emulation/aexcompat_patches/verify_F47.py`: exit 0, 3/3 bundles loaded and EffectMain resolved; 3/3 invocations without `--inspect` rejected with exit 2. Every report says render_supported=false and selectors_executed=[]. No output image/hash is claimed; hashes below identify executables.
- Executable SHA-256: OLMBlur `65b227ed5651744b0dcfe23ff2d976936d37c31d400dfb9a41be44abdf3fe820`; ColorKey `9b071e47b6688c6c4a7265d43501eaba1142f30ab1c6e192a40048be564570c5`; RadialBlur `d62a141596343fa1a96edca15610236aec4649e10be94d2d83a9aedd9a900878`. PiPL hashes are in F47-evidence/loader-results.json.
- SDK probe: InData=408, OutData=408, ParamDef=176, LayerDef=120, InteractCallbacks=176 bytes; InData utils/effect_ref/pica_basicP offsets=176/184/384; ParamDef.u=56; LayerDef.data=24. All ten observations match F46 Windows constants. This is not complete ABI coverage.
- `rustup target list --installed` includes aarch64-apple-darwin and x86_64-apple-darwin. No x86_64 worker build or Rosetta execution was attempted.
- Both F46 and F47 workers ran `inspect '/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMBlur.aex'` successfully. `cmp` of their stdout JSON exits 0 (4822 bytes each). This is a PE-inspection smoke check, not a render regression.
- Scratch after cleanup: 3.5 MiB; worker directory 7.3 MiB. Rust build tree and Xcode object/PCH trees deleted. No background build or emulator process is retained.

inference:
- BLOCKER / unfinished implementation: native_x64 is a PE/Win64 carrier, not a native Mac callback backend. Shared ClassicHost construction requires PeImage; native callbacks and reverse pixel/progress callbacks are Win64. The missing work is host/backend extraction plus typed C-ABI wrappers, not symbol loading. This ticket stops at the tested loader boundary rather than treating load success as render support.
- Sampled layout agreement supports investigating shared serialization but cannot prove every suite/parameter/Smart structure is ABI-compatible.
- Flag difference: source-host compilation explicitly disables FP contraction; ColorKey/RadialBlur projects do not. Possible numeric impact is unmeasured. This is not a proven plugin defect.
- No pixel mismatches or first differing pixel can be reported: zero native render cases executed, including zero of the requested 300 cases. Agreement with existing source-host results is unknown.
- No pair of numerical hypotheses was tested/refuted. The stop is an incomplete host integration, not exhaustion of a numerical investigation.

changed_files:
- tools/emulation/aexcompat_patches/F47-native-plugin.patch
- tools/emulation/aexcompat_patches/F47-native-plugin.md
- tools/emulation/aexcompat_patches/F47-abi-probe.cpp
- tools/emulation/aexcompat_patches/build_F47.py
- tools/emulation/aexcompat_patches/verify_F47.py
- tools/fuzz/build_F47_bundles.py
- orchestra/reports/F47-aexcompat-native-plugin-host.md
- orchestra/reports/F47-evidence/{bundle-builds.json,loader-results.json,mac-abi.txt,sdk-hashes.json,verify.txt,worker-build.json}

verify:
```sh
# Existing cached worker and retained bundles:
python3 tools/emulation/aexcompat_patches/verify_F47.py
# Expected exit 0: 3/3 loads, 3/3 unsupported invocations rejected, ten ABI observations.

# Rebuild disposable bundles if needed (hashes may differ due to build metadata):
python3 tools/fuzz/build_F47_bundles.py
# Expected exit 0, three lines reporting x86_64 arm64.

# Worker rebuild recipe is for a fresh F47 output directory only; it intentionally
# refuses to overwrite the installed worker. See the design note/build manifest.
git diff --check
```

next:
- Follow-up F47b: decouple ClassicHost from PeImage; extract native state/suite operations; implement Mac C-ABI entry and callback tables with complete SDK layout probes. First demonstrate GLOBAL_SETUP/PARAMS_SETUP and one Classic/Smart render through the shared host, including handle/checkout cleanup.
- Then implement the opt-in plugin-bundle adapter and seed 1/n100 for all three plugins, retaining source-host results and classifying every delta. Add x86_64 worker/Rosetta validation separately if dependency rebuild cost is acceptable.
