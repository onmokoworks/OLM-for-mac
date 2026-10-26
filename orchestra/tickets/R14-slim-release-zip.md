# R14: the release ZIP contains only what users need

## Why (user, 2026-10-26)
- The v0.2.0-beta.1 ZIP was 19.3 MB, but most of it was unrelated material:
  - `AE_PIXEL_VALIDATION/` with six nested request ZIPs (14.7 MB);
  - `AE_VALIDATION_CHECKLIST.txt` and `AE_VALIDATION_RESULT.template.json`;
  - `refs/conformance/...matrix_20260806.md`;
  - `manifest.json`;
  - `INSTALL.txt`;
  - every doc twice, once at the root and once under `docs/`.
- The orchestrator already replaced the published asset by hand. The new ZIP is `OLM_for_Mac/` with the 10 bundles, `README.md` (from `docs/PACKAGE_README_JA.md`), `README.en.md` (from `docs/PACKAGE_README_EN.md`) and `LICENSE`. SHA-256: `647c2b64…`.

## Do
- Change `scripts/package_mac_plugins.sh` so that it produces exactly that layout:
  - top folder `OLM_for_Mac`;
  - the 10 `.plugin` bundles, `README.md`, `README.en.md` and `LICENSE`;
  - nothing else.
- Write the build manifest as a sidecar next to the ZIP (`<zip>.manifest.json`), not inside it.
- Delete the AE pixel-validation request packaging from the release path. Keep `scripts/package_ae_pixel_validation_request.py` only if something else still uses it; check by reachability.
- Update every consumer of the old layout:
  - `orchestra/reports/R12-evidence/verify.py` and the R13 recipe;
  - release gate v2 static checks;
  - `tests/` that read the package layout.
  Keep their checks on bundles (Universal, minos, signature, hashes) and on README links. Drop the checks for files that are no longer shipped.
- Build once with the R13 recipe and audit the result. Expected: 14 entries' worth of top-level items, all signatures valid, README links resolve. Do not publish anything.
