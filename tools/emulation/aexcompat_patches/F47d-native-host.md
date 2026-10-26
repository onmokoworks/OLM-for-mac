# F47d native bundle bridge

`build_F47d.py` stages the read-only F47 cached Rust source, adds the SDK-typed
bridge and intercepts the CPU frame dispatch for the opt-in
`OLM_NATIVE_BUNDLE_EXECUTABLE` environment variable. The default source candidate
and AEX route remain unchanged. `--target x86_64-apple-darwin` builds a separate
worker under the ticket's `x86_64` scratch directory for Rosetta execution.

The bridge uses the arena's actual parameter count, validates native setup
parameter types/count, snapshots primary input/output worlds and replaces guest
pointers with native pointers. Optional unselected layer parameters are empty;
checkout of those layers returns unavailable. Selected secondary layers, ROI,
nonzero origins, independent output padding, persistent native sequence state,
GPU and tracing/census are outside this bridge's tested scope.

Native GLOBAL_SETUP, PARAMS_SETUP and SEQUENCE_SETUP precede either
SMART_PRE_RENDER/SMART_RENDER or Classic RENDER. Pre-render data is destroyed
using the plugin's supplied deleter before setdown and dlclose. The input and
output snapshots have guards; input mutation, unbalanced parameter/suite use,
and unknown suites cause failure. Acquisition messages and selector results
are retained in each candidate result, including rejected renders.

Only observed suite members are provided (diagnostic lines retain the F47c prefix):

- WorldSuite2 GetPixelFormat: primary input/output and PF8/PF16/PF32.
- ColorParamSuite1 floating color: ARGB8 declaration converted by division by 255.
- Iterate8/16/Float v2 iterate: full frame, equal geometry, independent strides,
  serial callback order; used by ColorKeep. Unsupported rectangle requests fail.
- HandleSuite1 allocation/lock/unlock/size/dispose, with host ownership and cleanup.
- AEGP UtilitySuite6 RegisterWithAEGP: registration identity for setup only.
- Interact add/check-out/check-in parameters, abort and progress; Smart primary
  checkout/output/checkin; whole-frame utility copy.

World allocation and handle resize fail loudly; remaining optional members are
null, not implemented. KiraKira explicitly selects the default-ramp parameter profile: native PARAMS_SETUP
creates its own default arbitrary handles, and the recovered raw ANGLE maps to
the native floating slider exactly as in the existing source adapter. Custom
arbitrary data is outside the scalar fuzz protocol. UI registration is recorded;
UI events are not driven.

Unknown suites fail AcquireSuite rather than returning
an approximate or empty suite. This is a fake host, not native AE. It retains
AEX setup/session ownership and is not a standalone native plugin backend.

`tools/fuzz/build_F47_bundles.py` builds the real Xcode projects in Release with
both architectures. `tools/fuzz/verify_F47d.py` runs serial seed-1/n100 bundle
and source campaigns, preserving the existing per-plugin generators. Smoother
v1 uses Classic; other bundle candidates use Smart. Source campaigns also retain
their original Classic comparisons; those are separate from the paired Smart
comparison requested by F47d.

## Known world-flag boundary

The AEX arena sets DEEP for PF16 and PF32. Native OLMBlur, KiraKira and Smoother2
also expect that convention. ColorKeep's production guard instead expects DEEP
only for PF16; its source fuzz host constructs those different flags, masking
the conflict. The shared bridge preserves the arena flags. Consequently ColorKeep
PF32 is retained as a rejected plugin/input-contract boundary, not silently
fixed through a per-plugin world-header rewrite. Resolving that production guard
or changing the shared contract is outside this ticket's no-plugin-source rule.

## R13 refreshed host

R13 builds the current bridge into new cache entries `worker-R13-bundle` and
`worker-R13-universal`; F47d/F51 pinned binaries remain unchanged. Ordinary
iterate clips the optional area to both worlds, uses independent byte strides,
and propagates the callback error. This matches the existing P00 SDK host
clipping contract and full-frame source-host iteration. Color/parameter/world
callbacks already cover ColorKeep's other observed suite calls.

The build recipe now stages Rust/Unicorn under a no-space `--build-root` and
uses a cache build directory for Cargo and temporary files. `--cache-name`
installs and registers the result without replacing previous workers. R13's
release report records the actual comparison counts; historical PF32 refusal
observations above do not describe the current production admission.
