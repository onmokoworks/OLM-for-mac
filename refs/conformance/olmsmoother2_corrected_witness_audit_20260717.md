# OLMSmoother2 corrected current-AEX witness audit - 2026-07-17

- Verdict: `PASS_CORRECTED_E170_EXTRACTED_CODE_WITNESS_AUDIT`
- Scope: `legacy_case_0012_gamma5_red_blue_current_aex`, exactly `(x=92,y=841)`.
- Primary evidence is the extracted corrected returned JSON fixture; all facts below are machine-parsed.

## Pinned Inputs

- Source ZIP provenance attestation only (not clean-clone re-proof): `refs/windows_returns/20260716/20260716_150500__RETURN__OLMSMOOTHER2_RDX_DESCRIPTOR_CORRECTED/RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip` (`RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.zip`)
- Extracted member: `RETURN_OLMSMOOTHER2_LEGACY_KEY_PRODUCER.json`
- Fixture metadata: `refs/conformance/fixtures/olmsmoother2_corrected_witness_20260717/metadata.json`
- `source ZIP SHA-256 provenance attestation (not clean-clone re-proof)`: `8c031837ac6a2e95fec657cd444ca303ba3c8fb66bf2235f3c038b37e207efcf`
- `source_member`: `c5f48309d9cc995f324ce7345caf8e993755db7d73e0745d36adbe252ed065bd`
- `function_code`: `90503de993f8891f72003eef21eff906ff9ed5cb0be4654295549a9aebc6378d`
- `source_aex`: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`

## Parsed Windows Facts

- Identity: `{'ae_pid': '59192', 'aex_sha256': '7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7', 'module_base': '0x7ffa99cd0000', 'project_bpc': '8', 'renderer': 'Software', 'run_id': 'smoother2-legacy-producer-inprocess-fcefd3f4d8b9410b93ede5dff562675b', 'case_id': 'legacy_case_0012_gamma5_red_blue_current_aex', 'witness_id': 'olmsmoother2-legacy-key-producer-common-core-v1'}`
- Live `RDX p2[0..5]`: `[92, 841, 1, 92, 842, 2]`; sample: `[92, 841]`.
- Retained class bytes: `{'center': [255, 255, 0, 255], 'previous': [255, 0, 0, 0], 'left': [0, 255, 0, 255]}`.
- Windows `e170_c`: `7`; event order: `['f270_entry', 'e170_entry', 'e170_return', 'e3a0_entry', 'e3a0_return', 'f270_return']`.
- Validated e170 addresses: `{'class_base': 2618300760320, 'class_stride': 7680, 'center_addr': 2618307219568, 'prev_addr': 2618307211888, 'left_addr': 2618307219565}`; center and previous equal `class_base + y * class_stride + x * 4`, while the reported left byte equals `class_base + y * class_stride + (x - 1) * 4 + 1`.
- The returned artifact also contains a retired bind hint for `91,841`; this audit does not use it as sample identity.

## Narrow Local Check

- The extracted `FUN_18000e170` bytes were run with the exact retained class bytes and returned `7`.
- Local branch logic: `previous_b0` must be nonzero.
- Windows witness separately reports `previous_b0=255`.

## Claims Not Made

- No mixed-identity bind event is used as the corrected sample identity.
- No claim that c280 is solved.
- No claim that cce0 is solved.
- No claim about x=91,y=841 or any ZIP carrying that retired witness.
- No AE exactness, full-AEX reproducibility, or final-writer claim.

## Smoke

```sh
python3 tools/emulation/audit_olmsmoother2_corrected_witness_20260717.py \
  --output-json refs/conformance/olmsmoother2_corrected_witness_audit_20260717.json \
  --output-md refs/conformance/olmsmoother2_corrected_witness_audit_20260717.md
python3 tools/emulation/audit_olmsmoother2_corrected_witness_20260717.py --self-test-tampered-relation
```
