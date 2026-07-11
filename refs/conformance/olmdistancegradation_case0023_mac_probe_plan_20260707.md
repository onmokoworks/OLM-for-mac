# OLMDistanceGradation case_0023 Mac Probe Plan

- Case: `olmdistancegradation_extended__case_0023`
- Request dir: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/request`
- Debug points: `1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394`
- Purpose: Differentiate Mac AE source alpha / mask / field-boundary ownership from 16bpc host output packing for the remaining 73px case_0023 residual.

## Commands

### bg_on

- Output dir: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on`
- Discriminator: If field/debug values match the source-model audit but exported pixels differ, suspect 16bpc host output/source ownership; if alpha/raw_inside/field_x differs, suspect Mac AE source alpha or field-boundary ownership.

```bash
python3 scripts/run_ae_single_case.py --request-dir refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/request --case-id olmdistancegradation_extended__case_0023 --output-dir refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on --param-override 'Use Background Color=1' --ae-env OLM_DG_DEBUG_DUMP_PATH=$(pwd)/refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on/field_debug.txt --ae-env 'OLM_DG_DEBUG_POINTS=1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394'
```

### bg_off

- Output dir: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off`
- Discriminator: If field/debug values match the source-model audit but exported pixels differ, suspect 16bpc host output/source ownership; if alpha/raw_inside/field_x differs, suspect Mac AE source alpha or field-boundary ownership.

```bash
python3 scripts/run_ae_single_case.py --request-dir refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/request --case-id olmdistancegradation_extended__case_0023 --output-dir refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off --param-override 'Use Background Color=0' --ae-env OLM_DG_DEBUG_DUMP_PATH=$(pwd)/refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off/field_debug.txt --ae-env 'OLM_DG_DEBUG_POINTS=1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394'
```

## Interpretation

- Compare alpha/raw_inside/raw_outside/inside_x/outside_x/field_x at (1699,7) and (415,393) against refs/conformance/olmdistancegradation_case0023_source_model_audit_20260707.md.
- If bg_on and bg_off debug fields are identical but PNG deltas differ only at output, keep the investigation on host/source/output ownership.
- If debug alpha or raw distance changes between runs, the remaining seam is source-world or mask provenance before compose.

## Forbidden

- Do not retune compose_pixel from this probe; the 2026-07-07 compose witness already excludes the triplet compose/writeback path.
- Do not retune Both-mode cv::add / saturating-add field merge while AEX CPU simu and the Mac source-model audit match the live witnesses.
- Do not revive the old packaged-stale explanation; packaged/current Windows references are exact in the 2026-07-07 audit.
