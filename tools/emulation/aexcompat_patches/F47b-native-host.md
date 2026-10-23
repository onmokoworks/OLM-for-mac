# F47b native lifecycle boundary (render backend incomplete)

`build_F47b.py` makes a private copy of the cached F47 worker source and adds
`native-plugin OLMBlur.plugin --setup`. The existing `--inspect` mode and AEX
routes remain intact. No cache worker or INDEX entry is replaced.

The new Mac C-ABI EffectMain call and `add_param`, `abort`, `progress`,
AcquireSuite and ReleaseSuite callbacks use eight-byte-aligned buffers and the
shared `aex-abi` offsets. Before Cargo runs, the recipe compiles a Mac SDK probe
for every shared constant referenced by the shim and rejects layout differences.
This verifies consumed layout constants, not a complete AE ABI or x86_64 run.

The input defaults follow `ClassicHost::from_engine_with_effect`; parameter
snapshots reuse its `GuestParam` representation. GLOBAL_SETUP, PARAMS_SETUP and
SEQUENCE_SETUP are followed by SEQUENCE_SETDOWN and GLOBAL_SETDOWN. Global and
sequence pointers propagate from OutData to InData. Selector errors are recorded,
with successful scopes unwound and `setup_ok=false` on errors. OLMBlur implements
no sequence-specific switch cases, so their zero return does not prove sequence
allocation or cleanup support.

AcquireSuite logs the actual requested name/version to stderr and JSON, clears
the output pointer and returns the SDK's suite-not-found error. **No suite is
implemented.** Utility slots and unsupported interaction slots are absent. This
is deliberately constrained to the audited OLMBlur setup path; it is unsafe to
extend the allowlist without implementing callbacks the added plugin uses. The
filename check is a scope guard, not a binary identity/security check. Reports
record the loaded executable and PiPL hashes.

There are no world, parameter checkout, handle, SmartFX or resident-session
implementations here. `--render`/`--session` are rejected. No plugin-bundle fuzz
candidate option is installed, and the default candidate remains unchanged.
Static source inspection identifies `PF World Suite` version 2 in OLMBlur's Smart
render code; that is **not** an observed runtime acquisition by this probe.

Build and verify from the ticket worktree:

```sh
python3 tools/fuzz/build_F47_bundles.py --plugins OLMBlur --scratch orchestra/state/F47b-native-plugin-host-render/bundles
python3 tools/emulation/aexcompat_patches/build_F47b.py
python3 tools/emulation/aexcompat_patches/verify_F47b.py
```

The build checks `memory_pressure`, uses one Cargo/CMake job and removes the
Cargo target tree even on build failure. Scratch remains under the worktree. A
no-space symlink at `~/.cache/olm-emu/F47b-scratch-link` points there; Unicorn's
configure receives the logical alias as PWD to avoid rejecting the physical
worktree path containing a space. This one-line change affects only configure
launch plumbing in the disposable source copy. Original cache sources and MAIN
remain untouched. The link may be deleted after building; the recipe recreates
it, and refuses to reuse a link belonging to another worktree.

Next boundary: extract the shared host operations behind native memory access,
then provide checked native WorldSuite2, utility copy, parameter checkout/checkin
and Smart checkout callbacks. Wire native entry dispatch into the existing
resident framing/protocol before adding the fuzz option. Do not substitute this
setup-only verification for the requested seed-1/n100 byte comparisons.
