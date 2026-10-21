# All-ten current-install fresh After Effects host smoke — 2026-08-12

Status: `pass`

This campaign started with zero matching After Effects processes and used one
fresh Adobe After Effects 2026 process, PID `71551`. The process started after
the accepted installed-identity manifest, used the Software project renderer,
mapped every one of the ten accepted installed arm64 executables at its exact
absolute path, produced ten fresh host-frame PNGs, exited normally, and left
zero matching After Effects processes.

## Identity and durable evidence

- Accepted identity manifest:
  `refs/conformance/olm_installed_identity_manifest_20260806.json`, SHA-256
  `70db3215ff4125dcfcf072b3b29ea7b0422ec7fc00c23e1646af79e005cf0954`,
  accepted at `2026-08-12T07:49:11.174620+00:00`.
- Host start: `2026-08-12T08:28:21+00:00`; vmmap capture:
  `2026-08-12T08:28:33.310743+00:00`.
- The persisted vmmap identifies PID `71551`, `Code Type: ARM64`, and exactly
  one accepted `/Contents/MacOS/<plugin>` path for every plug-in. Competing
  same-executable-name bundle paths are rejected.
- Canonical machine-readable reports:
  `refs/conformance/olm_all10_current_install_fresh_ae_smoke_20260812.json`
  and
  `refs/conformance/olm_all10_current_install_fresh_ae_smoke_raw_20260812.json`.
- Durable AE return, vmmap, launch wrapper, acknowledgement, and ten PNGs are
  under `handoffs/olm_all10_current_install_fresh_ae_smoke_20260812/`.

The initial report was conservatively `fail_closed` because its vmmap parser
mistook the slash in the protection column (`r--/rwx`) for the mapped pathname.
The retained vmmap bytes were not recaptured or edited. A corrected,
path-column-anchored parser reprocessed the same durable vmmap and recovered
the exact ten accepted paths; the raw report records this derivation
correction. ExtendScript exposes `File.modified` at second resolution on this
host, so the persisted validator binds that value to the filesystem mtime in
the same UTC second while independently requiring exact path, byte size,
SHA-256, and the higher-resolution filesystem mtime.

## Host-frame routes

`OLMBlur`, `OLMDirectionalBlur`, and `OLMToonDilate` remained enabled for their
host-frame saves. The other seven effects were loaded and added, their
enable-state was checked, and then they were disabled before the host-frame
save. All ten host-frame saves succeeded and produced fresh PNGs.

This distinction is intentional. The three enabled saves use default AE
tuples that are not the already-proved public numerical-owner tuples. The
seven disabled saves do not execute plug-in numerical rendering at all.
Consequently every row records `numerical_render_expected: false`,
`effect_enabled_numerical_render_attempted: false`, and
`numerical_render_succeeded: null`.

## Claim boundary

This is current-installed host plumbing evidence: fresh-process admission,
load/add, enable-state handling, Software-renderer host-frame export, exact
same-PID installed-module mapping, unchanged installed hashes, normal exit,
and residual-process cleanup. It does **not** claim pixel exactness, Windows
equivalence, public-owner numerical exactness, typed-plane behavior, or
padding behavior.

The producer test suite replays the persisted validator and includes
fail-closed tamper checks for identity, PID, renderer, timestamps, module
cardinality/path, hashes, route state, PNG metadata, competing mappings, and
translated/non-arm64 vmmap identity.
