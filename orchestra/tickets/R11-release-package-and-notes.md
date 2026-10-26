# R11: release package and new release notes (Japanese primary, English translation)

## Why
- The project is close to distributable. `scripts/package_mac_plugins.sh` still ships `refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md`, release notes from August that are now badly out of date.

## Do
1. Write new release notes: `docs/RELEASE_NOTES_JA.md` (primary) and `docs/RELEASE_NOTES_EN.md` (translation), for this release. Base them only on merged facts in `orchestra/reports/`. Cover:
   - what the plugins are;
   - which 10 plugins are included;
   - what was verified, with real numbers from the reports: bit-exact against the original on the emulator, real AE 2026 renders across preview resolutions and depths, Intel == Apple Silicon;
   - what changed since the August beta: preview-resolution/partial-render black frames fixed, the Effect Controls UI (KiraKira editor, hide/disable), speedups;
   - known limitations (link to KNOWN_LIMITATIONS);
   - installation and Gatekeeper (link to INSTALL);
   - the license (inherits the original Apache 2.0).
   Follow the user's doc style:
   - plain, short, concrete Japanese;
   - no bold;
   - no AI-ish phrasing such as "〜のは〜です" clefts, padded meta-sentences, or explaining the obvious.
   Read the current `README.md` for the tone. Proofread with yomiyasu: `python3 ~/.claude/skills/yomiyasu/scripts/yomiyasu_check.py run --source <draft> --final <final> --doc-type manual --reader general`, then `verify`.
2. Update `scripts/package_mac_plugins.sh` to ship the new notes (both languages) instead of the August file, and to include the English docs. Keep the manifest fields consistent.
3. Build a release ZIP from HEAD (`scripts/package_mac_plugins.sh`), and check it:
   - Universal binaries (`lipo`), minos 11.0;
   - 10 bundles, docs present;
   - no absolute local paths in any text file;
   - `codesign -dv` shows the ad-hoc signature as expected.
   Record its SHA-256. Do NOT publish anything: no GitHub release, no upload.
4. Report: the ZIP path, hash, contents listing, and the notes text.

## Rules
- Use 1-2 processes. Make no plugin source changes. Do not touch the release gate or ledger. Do not create tags or releases. The stop rule applies.
