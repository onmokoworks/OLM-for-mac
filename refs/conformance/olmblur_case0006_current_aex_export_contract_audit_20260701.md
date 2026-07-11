# OLMBlur case_0006 Current-AEX Export Contract Audit

- Plug-in: `OLMBlur`
- Case: `olmblur__case_0006`
- Bit depth: `16bpc`
- Renderer: `SOFTWARE`
- Decision: `outcome-a-current-aex-matches-canonical`
- Reason: The imported Windows current-AEX export is byte-identical to the canonical 2026-06-25 Windows Software reference.
- Next step: Audit Mac export/run provenance before reopening implementation.

## Parameters

- `Blur Amount=5`
- `Blur Smoothness=100`
- `Number of Repeat=10`
- `Bias Direction=1`
- `Legacy=0`

## File Identity

| Role | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| canonical_ref | `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |
| mac_single_export | `refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485331` | `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` |
| mac_batch_export | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmblur_exact/candidate/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png` | `2485333` | `d99b462a4f273578c616a556cf844db515694706ae3e7fad2bc2b9c4de152974` |
| windows_current_export | `refs/win_references/olmblur_case0006_current_aex_export_20260709/OLMBlur/olmblur_case0006_current_aex_export_20260709__software_16bpc_current_aex_export__fr24__olmblur__case_0006.png` | `2485242` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |

## Required Windows Payload

- exported PNG file
- AE version
- project renderer metadata
- bit depth metadata
- parameter/property snapshot for the same slice
- statement whether the PNG came from the same current-AEX build/path and same render class as the witness run

## Witness Points

| XY | Reason | canonical ref | Mac single | Mac batch | Windows current export |
| --- | --- | --- | --- | --- | --- |
| `(314, 14)` | lane-defining witness A | `[2201, 2201, 2201, 65535]` | `[2199, 2199, 2199, 65535]` | `[2201, 2201, 2201, 65535]` | `[2201, 2201, 2201, 65535]` |
| `(29, 71)` | lane-defining witness B | `[725, 725, 725, 65535]` | `[727, 727, 727, 65535]` | `[727, 727, 727, 65535]` | `[725, 725, 725, 65535]` |
| `(601, 598)` | batch-aligned support point | `[4609, 4609, 4637, 65535]` | `[4607, 4607, 4637, 65535]` | `[4609, 4609, 4637, 65535]` | `[4609, 4609, 4637, 65535]` |
| `(378, 487)` | single-case-aligned support point | `[64767, 35, 35, 65535]` | `[64767, 35, 35, 65535]` | `[64769, 35, 35, 65535]` | `[64767, 35, 35, 65535]` |

## Forbidden Moves

- global 16bpc writer swap
- helper surgery from case_0006 alone
- treat canonical reference as equivalent to current-AEX export without proof
- collapse case_0006 into case_0007 Legacy work
