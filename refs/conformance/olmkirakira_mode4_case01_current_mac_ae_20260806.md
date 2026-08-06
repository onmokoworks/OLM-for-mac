# OLMKiraKira Mode 4 current Mac AE natural route — 2026-08-06

Status: **exact for the retained representative**.

The installed Universal `OLMKiraKira.plugin` was exercised through the natural
After Effects effect application and render path, rather than by calling the
Mode 4 helper or typed writers independently.

- After Effects: `26.3x87`
- renderer: Software
- project depth: PF32 / 32 bpc
- geometry: `1920x1080`, full resolution
- retained case: `final_random10_olm_kira_kira_01`
- Blur Mode readback: `4` (Exponential)
- installed binary SHA-256:
  `cd97c6f328bf6a4adbe001662f35c12af405f89a2374046f185f68673df96719`
- input SHA-256:
  `8c1d418c7b853cc6f79087215ee86ab0b9eac423953c1a3409af3e120891a7f0`
- retained Windows output SHA-256:
  `810b76cde27a6590f0f2913d2e4f7bc2c1649c77b128a7c174d46b0088215c1d`
- current Mac output SHA-256:
  `dcfc1b98eea2d5f777b65651a0116346da2be8a1442411b11ad0024f4bdb5810`

The Mac and retained Windows EXRs compare equal for every raw FLOAT32 value:
`nonzero_count=0`, `max_absolute_error=0`.  The same AE PID remained active
and exactly one loaded KiraKira module path was observed before and after the
render. Parameter application and readback are retained in the JSON report.

Evidence:
`refs/conformance/olmkirakira_mode4_case01_current_mac_ae_20260806.json`.

This closes one natural full owner-to-writer representative required by the
frozen release matrix. It does not generalize Mode 4 equality to other
geometries, lengths, parameter tuples, bit depths, renderers, AE versions, or
color-management settings. Those remain explicit evidence boundaries.
