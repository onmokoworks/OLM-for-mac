# F47 native bundle loader boundary (incomplete prototype)

This patch adds `aex-guest-worker native-plugin PATH.plugin --inspect` to the
F46 worker. It is **load-only**, not a native AE render backend. It reads the
bundle's resource-file PiPL, selects the `ma64` or `mi64` Pascal-string entrypoint,
loads the executable with CoreFoundation, resolves that symbol, and reports
executable/PiPL SHA-256 hashes. No selector is called. Requests without
`--inspect` fail with exit 2; `render_supported` is explicitly false.

The default AEX backend, session protocol, fuzz candidate and plugin sources
are unchanged. Do not use this entry in INDEX as a Mac render candidate.

## Host audit: facts

Paths below are relative to the F46/F47 `reference-guest` source root.

- `crates/aex-guest-worker/src/classic.rs:from_engine_with_effect` allocates
  InData, OutData, utility and SPBasic tables from generated Windows offsets;
  it requires `PeImage` even when supplied an existing engine. Its interaction
  table wires parameter add/checkout/checkin, with no-op abort/progress.
- `native_x64.rs` is gated to x86_64 macOS plus `native-carrier`. Its entry and
  callbacks use `extern "win64"`, including reverse iterate callbacks. It
  maps PE sections and installs Windows imports; it is not a Mach-O loader.
- The native carrier has its own `NativeState`, arena, PF handles, world
  allocations and suite tables. AEGP memory is in `native_aegp_memory.rs`.
  Simply replacing the entrypoint would not expose Mac C-ABI callbacks.
- `configure_smart_render` records input/output worlds, format, geometry and
  time; the pre-checkout/checkout/checkin callbacks track checkout IDs.
  `finish_smart_checkout_scope` checks for unbalanced checkouts. Those semantics
  must survive a backend extraction.
- Iterate callbacks call guest pixel/progress/abort functions through Win64
  function types. Both directions require native ABI wrappers.
- The native `call_win64` sets thread-local host/AEGP state and rejects newly
  loaded Mach-O images after a selector. A bundle backend must establish its
  image baseline after loading the bundle/dependencies.
- `aex-abi` provides only `x86_64_windows` byte offsets. The committed SDK probe
  finds matching Mac sizes for InData (408), OutData (408), ParamDef (176),
  LayerDef (120), InteractCallbacks (176), and matching sampled pointer/union
  offsets. This is a sample, not a complete ABI proof.
- `tools/fuzz/adapters/public.py:compile_sdk` recompiles with arm64, `-O2`,
  `-fno-fast-math`, `-ffp-contract=off`. The bundle projects have only Debug;
  only OLMBlur among these three explicitly sets `-ffp-contract=off`.

## Build and verification

Run from this worktree:

```sh
python3 tools/fuzz/build_F47_bundles.py
python3 tools/emulation/aexcompat_patches/build_F47.py
python3 tools/emulation/aexcompat_patches/verify_F47.py
```

The worker build requires a fresh output directory, copies F46 if F47 is absent,
checks memory free >=30%, runs Cargo offline/locked with one job, deletes its
build tree, and adds a capability-labelled INDEX entry under the shared lock.
Existing source must match the patch in reverse dry-run. The source copy is
`~/.cache/olm-emu/src-F47`; original AEXCompat sources are not edited.

The bundle build creates disposable project copies, renames Debug to Release,
rebases source/header/plist paths, and requests arm64+x86_64, `-O2`, no signing,
and no testability. It retains each project's floating-point flags. These are
current-source Release builds, not a claim about an installed AE binary.
Products/logs go under `orchestra/state/F47-aexcompat-native-plugin-host`.
Intermediate object/PCH trees are deleted after each successful bundle build.

Only the arm64 worker was built. The x86_64 Rust target is installed; building
that worker would rebuild the Unicorn/native dependencies for another target.
The loader selects `mi64` when compiled for x86_64, but neither that build nor
execution via `arch -x86_64` has been verified.

## Inference and next implementation boundary

The sampled layout agreement suggests that some Classic serialization can be
shared, but does not justify reusing Win64 callback pointers. Extract the
native arena/state/suite operations from the PE carrier, provide typed Mac
C-ABI entry and reverse callbacks, and remove the PE dependency from host
construction via an explicit executable descriptor. Validate all consumed SDK
offsets on both architectures before sharing serializers. Preserve lifecycle,
handles, parameter materialization and Smart checkout semantics.

Then add native session routing and the opt-in `--candidate plugin-bundle PATH`
transport, reusing the oracle's parameter encoding. Only after selectors and
worlds work should seed 1/n100 comparisons run. No adapter option or pixel
comparison is delivered here. No conclusion about numerical agreement follows
from successful loading.

Potential build finding: ColorKey/RadialBlur do not explicitly disable FP
contraction in the project as their source hosts do. This is a flag difference,
not a proven numerical bug. Keep the production settings and measure it once
the native host works; do not silently normalize them in the comparator.
