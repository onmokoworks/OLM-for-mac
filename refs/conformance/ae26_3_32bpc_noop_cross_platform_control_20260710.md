# AE 26.3 32bpc No-op Cross-platform Control

> 2026-07-11 scope note: this result is not a universal host limitation. With
> the verified `OLM EXR 32 Float` template and linear-light-off workflow,
> OLMBlur cases 0001 through 0004 now reproduce their Windows before-effects
> EXRs byte-exact on Mac. See
> `refs/conformance/olmblur_32bpc_mac_ae_candidate_20260711.md`. Preserve this
> report as evidence for the older ColorKey control run only.

## Verdict

`host-version split` is too narrow for the current 32bpc EXR lane. Even when
the After Effects version is aligned to `26.3x87`, a Windows-to-Mac no-effect
control is not byte exact. This is a host/platform EXR-path difference, not an
OLM plug-in residual.

## Windows reference

- Imported set:
  `refs/win_references/20260710_190500__ae26_3_32bpc_recap/`
- Source: Windows AE `26.3x87`, `SOFTWARE` (`raw=1816`), `32bpc`
- Case: `olmcolorkey__case_0001`
- Reference used: the paired `before_effects` EXR
- Contract coverage: `98` cases / `196` paired FLOAT32 RGBA EXRs,
  compression `None`

## Mac controls

Both controls used the identical Windows `before_effects` EXR as input, Mac
AE `26.3x87`, the `OLM EXR 32 Float` output-module template, and a disabled
ColorKey effect.

| Control | Project working space | Linear blending | Result |
| --- | --- | --- | --- |
| disabled effect | `None` | `false` | `mismatched_values=6220800`, `max_raw_u32_delta=36716840` |
| disabled effect + explicit color-management disable | `None` | `false` | `mismatched_values=6220800`, `max_raw_u32_delta=36716840` |

`6,220,800 = 1920 * 1080 * 3`; all RGB float values differ while alpha is
unchanged. The explicit project color-management override is inert for this
control.

## Commands

```sh
python3 scripts/materialize_32bpc_mac_request.py \
  --spec refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json \
  --source-reference refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch \
  --output /tmp/olm_ae26_3_noop_colorkey_case0001 \
  --case-id olmcolorkey__case_0001

python3 scripts/run_ae_single_case.py \
  --request-dir /tmp/olm_ae26_3_noop_colorkey_case0001 \
  --case-id olmcolorkey__case_0001 \
  --output-dir /tmp/olm_ae26_3_noop_colorkey_case0001_nocm \
  --output-mode exr_render_queue --output-template 'OLM EXR 32 Float' \
  --ae-env OLM_AE_DISABLE_EFFECT=1 \
  --ae-env OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1 \
  --timeout 240 --keep-open

python3 scripts/compare_float_exr.py \
  refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703__software_32bpc__fr24__olmcolorkey__case_0001_before_effects.exr \
  /tmp/olm_ae26_3_noop_colorkey_case0001_nocm/olmcolorkey__case_0001_00000.exr
```

## Consequence

Do not use direct Windows-EXR versus Mac-AE-EXR equality to attribute a 32bpc
effect mismatch. A valid 32bpc conformance path needs an input/output pipeline
that is no-op exact across the two hosts, or a same-host comparison control.
The imported Windows AE26.3 set remains valid reference provenance and is
useful for Windows-side algorithm evidence.
