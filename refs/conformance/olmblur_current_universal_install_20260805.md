# OLMBlur current-source Universal install

Date: 2026-08-05

The current OLMBlur source built successfully as a Debug Universal macOS
bundle containing `arm64` and `x86_64`. The ad-hoc signed bundle was installed
as the sole `OLMBlur.plugin` under the user MediaCore directory. No After
Effects process was stopped or restarted.

## Installed identity

- Bundle: `/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin`
- Bundle identifier: `com.adobe.AfterEffects.OLMBlur`
- Architectures: `arm64`, `x86_64`
- Binary SHA-256: `dd64362e6071cfd93e92f3a4853782752aeb023c54671773bfedb0c496e8afc7`
- arm64 UUID: `9DD810B8-2298-365D-A9D6-C2E5726FD56D`
- x86_64 UUID: `362E4360-F89A-393B-8184-1BF44ACAA865`
- Signature: ad hoc; strict deep verification passed
- Full SHA-256 CDHash: `08c4276420f1fb141e144478c7e1e636c8e9b5caa51d867a3f10c014e4a83052`

The build used `ARCHS='arm64 x86_64'`, `ONLY_ACTIVE_ARCH=NO`, and
`CODE_SIGNING_ALLOWED=NO`; signing was applied explicitly after the build.
This target compiles the current PF8/PF16/PF32 Legacy and NonLegacy dispatch
and worker sources referenced by `mac/OLMBlur/OLMBlur.cpp`.

## Safe install and rollback

The previous installed bundle was moved outside MediaCore before the candidate
was copied. Its recoverable backup is:

`/Users/onmk/Library/Application Support/OLM Plugin Backups/20260805_1955/OLMBlur.plugin`

The previous binary SHA-256 is
`c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e`.
Only one `OLMBlur.plugin` remains visible under MediaCore.

## Live-host boundary

After Effects PID `77384` started at `Wed Aug 5 12:28:22 2026`, before this
install. Its executable is
`/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects`.
`vmmap` found no mapped OLMBlur image. The process was left running, so the
installed build is recorded as `restart_required: true`: a fresh host identity
is required before claiming that AE loaded this binary. This report makes no
AE runtime or AE-exact claim.

The machine-readable identity record is
`refs/conformance/olmblur_current_universal_install_20260805.json`.
