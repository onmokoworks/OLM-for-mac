# OLMSmoother2 PF_Pixel8 premultiply rounding audit - 2026-07-18

- Verdict: `REQUIRED_BYTE_RULE_IDENTIFIED_NOT_AE_EXACT`
- Scope: one retained Windows Software witness at source coordinate `(92,840)`.
- The plug-in source was not edited.

## FACT

- Raw source RGBA: `[174, 174, 174, 174]`.
- Windows before-effects RGBA: `[119, 119, 119, 174]`.
- Integer product: `174 * 174 = 30276` = `255 * 118 + 186`.
- Source SHA-256: `9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265`.
- Windows before-effects SHA-256: `c58d244c327486b689a4a06500c2bc3217216b652aefeea11c1fbcfcee26c520`.
- Exhaustive PF8 mapping check: `65536` pairs, `0` mismatches between integer `+127` and normalized-float nearest.

## Candidate Rules

| Rule | Result | Windows match |
| --- | ---: | --- |
| `truncate_floor` | `118` | no |
| `nearest_integer_plus_127` | `119` | MATCH |
| `float_normalized_then_nearest` | `119` | MATCH |

## Identified Rule

- Byte formula: `(rgb * alpha + 127) // 255`.
- Equivalent mathematical description: `nearest_integer(rgb * alpha / 255)`.
- Witness result: `119`.
- `255 is odd, so product/255 cannot have fractional part exactly 0.5; +127 selects remainder >= 128.`

## Independent Trace Check

The retained Mac trace still shows the un-premultiplied normalized sample `(92,840)` as approximately `0.42325333` with alpha `0.68234253`, and records a neighboring source sample entering the append path. This independently confirms why the current Mac boundary differs from the Windows before-effects byte witness; it does not establish AE exactness.

## INFERENCE

- The retained witness requires integer nearest-code premultiplication, not truncation.
- Across all 65,536 PF8 value/alpha pairs, the tested normalized-float-nearest and integer +127 mappings are byte-equivalent; the byte mapping is identified even though the internal implementation order is not.
- The witness alone cannot prove that every AE host path uses this rule for every pixel format; PF16 and PF32 remain separate contracts.
- The rule is a host-boundary correction candidate for Smoother2 and is not yet a permanent Mac plug-in change.

## Claims Not Made

- No edit to OLMSmoother2_port.cpp
- No Mac AE exactness claim
- No claim that this single witness closes the Smoother2 classifier or writer residual

## Reproduction

```sh
python3 tools/emulation/audit_olmsmoother2_pf8_premultiply_rounding_20260718.py
```
