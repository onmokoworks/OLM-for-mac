# OLMDirectionalBlur Final PF Output Contract 20260718
- Status: `pass`.
- Scope: bounded actual-AEX PF8 final-store contract joined to the natural continuation.
- Production source changed: `False`.
- Windows values fabricated: `False`.
- AE exact claim: `False`.

## Result

- Required checks: `{"actual_output_callback": true, "continuation_pass": true, "fail_closed_probe": true, "final_store_samples": true, "nontrivial_store": true, "same_aex": true, "same_fixture": true, "same_source": true, "writer_probe_pass": true}`.
- Actual callback sequence: `['0x180006980', '0x180006b30']`.
- Final-store samples: `7`; first words: `[[255, 255, 0, 0], [255, 255, 0, 0]]`.
- The real `0x180006b30` callback overwrote PF8 destination words through the callback destination pointer.
- A fresh full-frame equivalence claim remains blocked because this proof is not a same-run complete-frame capture.

## Provenance

- AEX: `plugins_2025/OLMDirectionalBlur.aex` sha256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Fixture: `tools/emulation/dblur_fullrender_host_fixture_20260711.py` sha256 `e3216aa5a213efaf2129dd11bf9c4a5e6e4a5c162d034c607df6e0bda1fba80a`.
- Source: `refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png` sha256 `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`.
- Continuation report: `refs/conformance/olmdirectionalblur_natural_continuation_20260718.json`.
- Writer probe: `tools/emulation/test_olmdirectionalblur_natural_writer_owner_20260717.py`.

## Reproduction

`python3 tools/emulation/test_olmdirectionalblur_natural_writer_owner_20260717.py`
