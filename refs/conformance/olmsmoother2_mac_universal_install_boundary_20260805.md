# OLMSmoother2 macOS Universal install boundary

Status: `installed_restart_required`

The current source built successfully as an ad-hoc signed Universal `x86_64 + arm64` bundle. Candidate and installed Mach-O SHA-256 are both `fe782f344dcaf8865b778198b0faeb8cecd525062a83f38aca8dc1db74442c34`; strict codesign verification passes.

The previous installed bundle was moved intact to `handoff/mac_plugin_backups/olmsmoother2_20260805_195354/OLMSmoother2.plugin` (Mach-O SHA-256 `bad3472d3ce808bdd69f0fa55be493c3d2f76cd7ad8c49b519f03347b3e2cd7b`) before installation.

After Effects 26.3.0 remained running as PID 77384, started locally at `Wed Aug 5 12:28:22 2026`. It was not stopped or restarted. `lsof` found no OLMSmoother2 mapping in that process before or after installation, so the new bundle is not claimed as host-loaded. Restart AE and bind its loaded mapping to the installed path/hash before any AE-host assertion.
