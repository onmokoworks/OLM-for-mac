status: blocked

summary:
- Partial implementation: F47b calls the real arm64 OLMBlur bundle's setup and setdown selectors through native C ABI.
- Added native parameter capture using the shared Rust GuestParam representation, aligned AE buffers, ABI checks and AcquireSuite logging.
- OLMBlur setup metadata matches AEX for the compared fields; the existing AEX setup route remains byte-identical to F47.
- Rendering, native suites, resident session routing and the plugin-bundle fuzz adapter remain unimplemented; zero render comparisons ran.
- No plugin source, default candidate, release gate, ledger, MAIN or existing cached worker/source was changed.

facts:
- Read AGENT_GUIDE.md, emulation GOTCHAS, the F47 report/design, compatibility plan and targeted OLMBlur ledger entries. No numerical hypotheses were tested or refuted.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMBlur --scratch orchestra/state/F47b-native-plugin-host-render/bundles`: exit 0; `OLMBlur x86_64 arm64`. Only the arm64 worker was exercised. The new builder arguments preserve F47's defaults when omitted.
- `python3 tools/emulation/aexcompat_patches/build_F47b.py`: successful clean build; the final build manifest and memory percentage are retained in `F47b-evidence/build.json`. Cargo uses offline/locked Release and one job. The Mac SDK probe matched all 37 consumed shared ABI constants; compile-time assertions also check PF_Err width and callback/suite error codes.
- Initial direct-path Cargo build failed at Unicorn's configure path-with-spaces rejection, followed by missing configuration's `__int128_t` conflict. A no-space symlink alone also failed. A separate `sh -c pwd` probe showed physical spaced PWD without an explicit environment value, and the no-space logical path when PWD was set. Passing logical PWD to configure resolved the build. This is new build-boundary evidence, not two refuted numerical hypotheses. The one-line CMake launch change exists only in the disposable source copy.
- `python3 tools/emulation/aexcompat_patches/verify_F47b.py`: exit 0. Two independent native invocations each return 0 for GLOBAL_SETUP, PARAMS_SETUP, SEQUENCE_SETUP, SEQUENCE_SETDOWN and GLOBAL_SETDOWN. Each registers five parameters and advertises six including input. OLMBlur has no sequence-specific switch cases; the sequence success does not demonstrate allocation or handle cleanup.
- Compared native/AEX advertised count, out_flags/out_flags2 and each parameter's slot/index/type/name/flags: zero differences. Defaults, numeric ranges, choices and raw parameter unions were NOT compared.
- Observed AcquireSuite calls during setup: zero. Implemented suites: none. The logging callback clears the returned pointer and reports SDK suite-not-found. Its error path was not exercised by OLMBlur setup. Static inspection identifies `PF World Suite` version 2 in Smart rendering; this is not a runtime observation.
- Native `--inspect` still executes no selectors. Bare/native `--render`/`--session` requests all return exit 2. Only the audited OLMBlur basename is admitted to `--setup`; this is a scope check, not a binary security boundary.
- F47 and F47b AEX `setup` stdout match exactly: 2044 bytes, SHA-256 `c63311fd43a44ed140a7fe3cb0dbf2d9cbee5a1dfae4cfccd3dea05b7a8dfc19`. This is a setup regression check, not a render regression.
- Native SMART_PRE_RENDER calls: 0; SMART_RENDER calls: 0; seed-1/n100 cases: 0. No output-pixel hashes, first pixel mismatch or source-host numerical classifications exist. ColorKey and RadialBlur were not attempted.
- `python3 -m py_compile` for all three changed Python scripts, `rustfmt --edition 2024 --check tools/emulation/aexcompat_patches/F47b-native-host.rs`, and `git diff --check` pass.

- Final worker SHA-256: `7d5e5e276dc19798dae3a99ce400ae892711ed7ebe263380a328d47f404adf6f`; pre-build free memory: 53%. Final clean build finished in 2m50s with one existing library dead-code warning. Cargo target and copied source trees were removed; the temporary no-space symlink was removed. Worker, bundle and logs remain in ticket-local scratch (9.8 MiB total); no background build/emulator process is retained.

inference:
- The tested boundary establishes native entry dispatch and parameter registration, not an end-to-end native host. Only GuestParam representation and generated ABI constants are shared; the complete ClassicHost/GuestEngine state has NOT been exposed as native tables.
- BLOCKER / incomplete integration: world allocation/format, utility copy, parameter checkout/checkin, handles and Smart checkout lifetimes still need native callbacks backed by shared host operations. Existing session code still constructs the PE/Unicorn host. A fake session or adapter that cannot render would obscure this boundary, so neither was added.
- The absence of suite calls during setup says nothing about render-time suite needs. Passing consumed offsets does not prove all SDK structures or x86_64 ABI compatibility.

changed_files:
- tools/emulation/aexcompat_patches/F47b-native-host.rs
- tools/emulation/aexcompat_patches/F47b-native-host.md
- tools/emulation/aexcompat_patches/build_F47b.py
- tools/emulation/aexcompat_patches/verify_F47b.py
- tools/fuzz/build_F47_bundles.py
- orchestra/reports/F47b-native-plugin-host-render.md
- orchestra/reports/F47b-evidence/{build.json,verification.json,mac-abi.txt,verify.txt,bundle-builds.json}

verify:
```sh
# Existing ticket-local worker and bundle:
python3 tools/emulation/aexcompat_patches/verify_F47b.py
# Expected exit 0: two successful native lifecycles, setup differences {},
# AcquireSuite calls [], AEX setup unchanged, render_cases 0.

# Reproduce after scratch cleanup, using read-only cached F47 source:
bash scripts/setup_ae_sdk_links.sh
python3 tools/fuzz/build_F47_bundles.py --plugins OLMBlur --scratch orchestra/state/F47b-native-plugin-host-render/bundles
python3 tools/emulation/aexcompat_patches/build_F47b.py
python3 tools/emulation/aexcompat_patches/verify_F47b.py
# Expected: universal OLMBlur, 37 ABI constants match, one-job worker build,
# then the same lifecycle checks. Build hashes may change with toolchain/build metadata.

git diff --check
```

next:
- Continue F47b with a native memory/backend abstraction for shared ClassicHost operations; implement checked WorldSuite2/copy/parameter/Smart callbacks and retain suite acquisition/release evidence.
- Route native rendering through the existing resident session protocol, then add opt-in `--candidate plugin-bundle <path>` without changing the default.
- Run OLMBlur seed 1/n100 with jobs=1, AEX and source-host comparisons, and classify every difference before expanding to ColorKey/RadialBlur. No numerical agreement is asserted by this ticket's partial result.
