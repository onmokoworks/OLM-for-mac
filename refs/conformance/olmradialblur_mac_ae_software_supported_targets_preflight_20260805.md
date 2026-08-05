# OLMRadialBlur Mac AE Software host-phase preflight (2026-08-05)

Status: `restart_required`

The AE host phase is pinned to two supported targets:

- Rotation PF8 `case0010`, Software renderer, 1920x1080, lossless RGBA PNG.
- Zoom PF32 `case0009`, Software renderer, 1920x1080, FLOAT RGBA EXR.

Both runners and the ephemeral project fixture require installed binary SHA-256
`2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732`.
Input/reference/internal-frame hashes, all 24 readable manifest parameters,
output templates, renderer, bit depth, working-space settings, resolution, and
time are fail-closed.

The provenance preflight passes. Render readiness is false only because AE is
not running and therefore no process has mapped the exact canonical binary.
Neither runner was invoked with `--run`; both report `run_executed=false`.

When the user starts AE manually, rerun:

```sh
python3 scripts/preflight_olmradialblur_mac_ae_supported_targets_20260805.py
```

Only a `ready` result authorizes invoking the individual runner with `--run`.
