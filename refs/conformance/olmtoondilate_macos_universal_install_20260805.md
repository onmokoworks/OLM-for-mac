# OLMToonDilate macOS Universal install — 2026-08-05

- Status: **PASS_INSTALLED_AE_STOPPED**
- The current source built successfully as a Universal `arm64` + `x86_64` bundle.
- Installed binary SHA-256: `7d2c24d8ad0f7436ee7035e0d926a2abaac1a74bc9305a4223f76230c1fc5537`.
- The bundle is ad-hoc signed and passes deep, strict code-sign verification.
- It was installed in the user MediaCore directory by verifying a sibling staging bundle before same-volume rename.
- Previous binary SHA-256: `8ac60d57193d1848fc830cff49c2a31faff5ed6298fa0d7736ab4298e2bd0ffc`; the prior bundle remains recoverable at `OLMToonDilate.plugin.backup-20260806-1512`.
- After Effects was stopped during installation and verification.
- The installed arm64 entrypoint executes the focused AE-free SmartPreRender/SmartRender fixture exactly; real AE loading and rendering remain unclaimed.

Host identity: MacBookPro18,3, arm64, macOS 15.7.2 (24G325).
