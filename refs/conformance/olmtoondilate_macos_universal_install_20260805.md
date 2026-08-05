# OLMToonDilate macOS Universal install — 2026-08-05

- Status: **PASS_INSTALLED_RESTART_REQUIRED**
- The current source built successfully as a Universal `arm64` + `x86_64` bundle.
- Installed binary SHA-256: `8ac60d57193d1848fc830cff49c2a31faff5ed6298fa0d7736ab4298e2bd0ffc`.
- The bundle is ad-hoc signed and passes deep, strict code-sign verification.
- It was installed in the user MediaCore directory by verifying a sibling staging bundle before same-volume rename.
- Previous binary SHA-256: `731798e1386f04afd181523e3fd55fbf5824a89b7ea97493281217ed5882c36e`; the prior bundle remains recoverable at `OLMToonDilate.plugin.backup-20260805-1955`.
- After Effects 2026 PID 77384 was observed running from the canonical application path and was not stopped or restarted.
- **Restart required:** the running AE process predates installation, so loading of the new binary is not claimed.

Host identity: MacBookPro18,3, arm64, macOS 15.7.2 (24G325).
