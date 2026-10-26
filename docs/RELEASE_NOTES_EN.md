# OLM for Mac release notes

October 2026 · Beta

[日本語](RELEASE_NOTES_JA.md) (Japanese is the primary version; this is a translation)

An unofficial Mac port of the Windows After Effects plugins "OLM Tools". The plugins are Universal binaries that run on both Apple Silicon and Intel, and require macOS 11 or later.

## Included plugins

Ten plugins: ColorKeep, OLMBlur, OLMColorKey, OLMDirectionalBlur, OLMDistanceGradation, OLMKiraKira, OLMRadialBlur, OLMSmoother, OLMSmoother2 and OLMToonDilate.

OLMSmoother supports 8/16 bpc. The other nine support 8/16/32 bpc.

## Changes since v0.2.0-beta.1

Output is unchanged. We removed old code paths that only served specific inputs, cutting about 5,000 lines.

## Changes since the August beta

- Fixed black frames at lower preview resolutions and when only part of the image is drawn.
- OLMKiraKira's gradient editor and the hiding or disabling of controls based on settings now behave the same as in the original plugin.
- Heavy settings are faster. With heavy OLMDirectionalBlur settings, a 1080p frame that took about 18 seconds now takes about 1.4 seconds.

## Verification results

We compare the output with the original Windows plugin bit for bit. See [How we verify](BETA_SUPPORT.en.md) for details.

- Of 2,000 cases compared with the original plugin, all 1,854 cases that the original could render matched.
- The Apple Silicon and Intel builds produced no differences. The Intel build was run under Rosetta, not on a real Intel Mac.
- In After Effects 2026, all 10 plugins rendered at Full to 1/4 resolution.

## Limitations and installation

GPU rendering is not supported. See [Known limitations](../KNOWN_LIMITATIONS.en.md) for other limitations.

See the [installation guide](INSTALL_EN.md) for the steps. The plugins have no Apple Developer ID signature or notarization, so the guide also explains what to do about Gatekeeper.

## License

This port inherits the license of the original OLM plugins (Apache License 2.0 by OLM Digital). The full text is in [LICENSE](../LICENSE). This is an unofficial port, not affiliated with OLM Digital, and has not been permitted or endorsed by them.
