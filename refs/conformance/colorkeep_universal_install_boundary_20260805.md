# ColorKeep macOS Universal install boundary

Status: `installed_restart_required`

The current Smart Render PF32 special-value source plus PARAMS_SETUP slider-supervision parity built as an ad-hoc signed Universal `x86_64 + arm64` bundle. The requested configuration was `Release`, but this Xcode project has no Release configuration, so xcodebuild selected the default `Debug` configuration. The signed candidate and installed Mach-O SHA-256 are both `ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce`; strict codesign verification passes.

The immediately previous installed bundle was moved intact to `handoff/mac_plugin_backups/mediacore_20260805_colorkeep_before_params_supervise/ColorKeep.plugin` before installation. Its Mach-O SHA-256 is `dd2ba9e9a2d08953a9c45e8d4893d80b4c46655ab6eaf39a77e7c65b9bbdd57a` and it is also Universal `x86_64 + arm64`. The earlier pre-special-value backup remains separately retained.

The installed hash itself was loaded with `dlopen`, its public `EffectMain` was resolved and executed, and its native arm64 PF16 worker/writer produced the exact existing actual-AEX extended-range payload (`1fa0ee04a8e57924bfb14a3c57f9ac937c7737486daca69b2bec689f6afe4a5e`). See `colorkeep_installed_entry_worker_writer_20260805.json`. This closes the prior gap where production behavior was demonstrated only by recompiling the source in temporary harnesses.

The stronger synthetic-suite witness `colorkeep_installed_public_pf16_render_20260805.json` executes the same installed hash through `EffectMain(PF_Cmd_RENDER)`, `CheckoutInfo`, the real PF16 dispatch, internal worker, and rowbytes-aware writer in one call chain. `PF ColorParamSuite` v1 and `PF iterate16 Suite` v2 are the only synthetic host boundaries. Its complete padded output remains raw-exact to the actual-AEX fixture.

After Effects 26.3.0 remained running as PID 77384, started at `Wed Aug 5 12:28:22 2026`. It was not stopped or restarted. Neither `lsof` nor `vmmap` found a ColorKeep mapping after installation, so the newly installed binary is not claimed as host-loaded. Restart AE and bind the loaded ColorKeep mapping to the installed binary/hash before making any AE-host behavior claim.
