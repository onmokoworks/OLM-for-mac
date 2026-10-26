status: done
summary:
- Release ZIP now contains only OLM_for_Mac/, ten plugin bundles, two package READMEs and LICENSE; build manifest is <zip>.manifest.json.
- One R13/R12 recipe build and real-binary audit passed; ZIP is 1,470,236 bytes, unpublished.
- Ten Universal/ad-hoc signatures, both slices minos 11.0 and executable hashes pass; README sources match and seven external URLs return HTTP 200.
- Fifteen regression tests, four negative sidecar checks and release gate v2 static stage pass.
- Durable ZIP and sidecar registered as release-R14; regenerable products removed.

facts:
- Built once, exit 0:
  `OLM_PACKAGE_STATE="$PWD/orchestra/state/R14-slim-release-zip/package" OLM_RELEASE_CACHE="$HOME/.cache/olm-emu/release-R14" bash orchestra/reports/R12-evidence/build.sh > orchestra/state/R14-slim-release-zip/build.log 2>&1`
- Source commit recorded by build: `679a651fbc368444b6d56b1a7e4a08a077bb8428`, git_dirty=false. Later changes affect developer smoke recipe/evidence only.
- ZIP SHA-256: `040372cfe8e32340f8fea44727b4fd2d8ab1234cacd1bd5e1439ec08a1ae75e5`.
- Audit command below exited 0: 103 ZIP members (including bundle internals), 13 immediate children of OLM_for_Mac, or 14 logical items counting that enclosing folder. The ticket's enumerated contents total 13 children, not 14 children.
- Audit: 10/10 Universal/ad-hoc bundles, 20/20 slices minos 11.0; all codesign strict/deep checks and binary hashes pass; 33 UTF-8 text files checked, 0 nested ZIPs, 0 local-path hits. No first mismatch.
- Recheck script below: 15 tests PASS, real package PASS; missing sidecar and altered binary_sha256/minimum_macos/signing_kind each rejected. Intake and listing recognize the slim ZIP.
- Release gate v2 `Gate.static` ran against this build's products with jobs=1: PASS, all ten Release settings/PiPL checks and package_layout_pass=true. See `R14-evidence/static-summary.json` for exact invoked commands and predicates. No full fuzz gate was rerun for this packaging-only ticket.
- Seven distinct URLs extracted from docs/PACKAGE_README_{JA,EN}.md were fetched with Python urllib.request.urlopen(timeout=30); all HTTP 200 (links.log). Relative Markdown links are checked by the verifier; language filenames and LICENSE exist, and the audit checks README bytes against source.
- Reachability: `rg -n package_ae_pixel_validation_request scripts refs/scripts` finds independent callers in `refs/scripts/smoke_ae_pixel_validation_request.py` and `refs/scripts/smoke_verify_ae_pixel_validation_batch.py`; the standalone generator remains. Release and handoff Mac packaging no longer invoke it or pass --pixel-reference-profile.
- Immutable historical ROI-v2 payload assertions in tests/test_beta_support_documentation.py still describe their pinned old artifact; deliberately not rewritten as claims about this release.
- Initial pytest invocation failed because MAIN's venv has no pytest. Recovered with unittest/runpy (retained recheck.py), all 15 tests passed. No rejected tool call.
- Evidence-copy command first used gate-results.json, which does not exist for Gate.static; corrected to its actual summary.json. No build or test rerun needed.
- Durable files: ~/.cache/olm-emu/release-R14/OLM_for_Mac.zip and .zip.manifest.json, registered in INDEX.json; registration snapshot retained. Scratch after cleanup: 9.5 MiB. No background process remains, no publish/push, no MAIN or plugin source edits.

inference:
- Packaging-only changes preserve the audited bundle integrity checks without distributing developer validation material. This is not a new pixel-conformance or native-host claim.
- Standalone handoff smoke now requires --mac-package with real signed binaries and copies its sidecar; the former synthetic binaries could not satisfy existing codesign/hash checks. Full handoff/reference-request smoke is outside this release ZIP audit.

changed_files:
- scripts/package_mac_plugins.sh
- scripts/verify_mac_plugin_package.py
- scripts/run_olm_release_gate_v2.py (static layout contract only)
- scripts/install_mac_plugins_to_mediacore.sh
- scripts/package_olm_handoff.sh
- scripts/verify_ae_host_return.py
- scripts/intake_olm_return.py
- scripts/list_olm_return_candidates.py
- scripts/README.md
- refs/scripts/smoke_mac_plugin_package_verifier.py
- refs/scripts/smoke_olm_handoff_package_verifier.py
- tests/test_release_package_layout.py
- orchestra/reports/R12-evidence/build.sh
- orchestra/reports/R12-evidence/verify.py
- orchestra/reports/R13-release-gate-green.md (current recipe note; historical evidence preserved)
- orchestra/reports/R14-slim-release-zip.md
- orchestra/reports/R14-evidence/*

verify:
```sh
mkdir -p orchestra/state/R14-slim-release-zip/review
export TMPDIR="$PWD/orchestra/state/R14-slim-release-zip/review"
python3 -B orchestra/reports/R14-evidence/recheck.py "$HOME/.cache/olm-emu/release-R14/OLM_for_Mac.zip" "$TMPDIR/recheck"
python3 -B orchestra/reports/R12-evidence/verify.py "$HOME/.cache/olm-emu/release-R14/OLM_for_Mac.zip" "$TMPDIR/audit"
bash -n scripts/package_mac_plugins.sh scripts/package_olm_handoff.sh
 git diff --check
```
Expected: 15 tests PASS, four negative cases rejected, real package and intake classification PASS; audit prints the ZIP SHA above and ten verified bundles; shell/diff checks exit 0.

To rebuild, use a fresh state/cache with the build command under facts, then run the same two verifiers on the new ZIP. Time/git metadata makes the sidecar non-identical; new source/build identities must not be confused with this retained ZIP's identity.

next:
- Orchestrator review/merge only; do not publish this artifact automatically.
