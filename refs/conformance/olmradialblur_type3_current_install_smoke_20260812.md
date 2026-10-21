# OLMRadialBlur Type-3 current-install AE smoke (2026-08-12)

The frozen source SHA-256 is `36063ae…1743`. Alongside that source identity, the
isolated ad-hoc-signed Universal build has binary SHA-256 `7701c3…18b3`, passes deep/strict signature validation,
and is installed as the only `OLMRadialBlur.plugin` bundle in MediaCore. The
previous `8a4bd2…7934` bundle remains recoverable in the durable
`handoff/mac_plugin_backups/mediacore_20260812_radial_type3_before_install/`
directory.

A fresh Adobe After Effects 2026 process (26.3x87, PID 10809) opened a PF32
SOFTWARE project, added `OLM RadialBlur`, and rendered a 16×16 default-effect
PNG (`ff6ab6…bbe3`). The persisted vmmap contains four segments for the exact
installed binary path; the compressed raw map is retained beside the ready
handshake and output PNG. AE was stopped after capture.

The subsequent 9×7 Type-3 Layer render did not return or create an output and
was terminated as a timeout. It supplies no live pixel-exact or Smart numerical
evidence. This smoke therefore proves only install, load, effect-add, PF32
SOFTWARE default-render plumbing. The separate bounded direct internal-owner
and public classic hostless closure remains separate evidence and is not used
to reinterpret the live timeout.

Capture provenance limitation: an early runner started fresh AE, then the same
runtime JSX was sent manually with `DoScriptFile`. Those exact early runner
bytes were not retained. The checked-in runner is the hardened replay runner;
the separately retained post-capture variant did not generate this run. The
hash-bound ready record, PNG, vmmap, and raw observation are authoritative.
