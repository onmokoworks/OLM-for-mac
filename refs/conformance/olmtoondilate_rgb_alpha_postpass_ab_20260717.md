# OLMToonDilate RGB*=alpha Removal A/B - 2026-07-17

## Scope

Candidate analysis for the binary-authorized Mac source fix. The tool is
`tools/emulation/olmtoondilate_rgb_alpha_postpass_ab_20260717.py`; its output
was written to `/tmp/olmtoondilate_rgb_alpha_postpass_ab_20260717.json`.

The candidate disables only the final semi-alpha RGB*=alpha post-pass.
Propagation order, opaque seed threshold, copy source, effective radius, and
quantization are otherwise identical to the typed Mac model. `candidate_no_postpass`
is the authorized candidate; `legacy_postpass` is the A/B control.

## Reference Cases

- 8bpc: canonical Windows Software `refs/win_references/20260604_olm/OLMToonDilate`,
  cases `case_0001..case_0003`. Cases 1/2 are 960x540 with Search Radius 13;
  case 3 is 1920x1080 with Search Radius 27. Case 3 is stored in a 16-bit PNG
  container but belongs to the recorded 8bpc comp, so the probe explicitly
  decodes all three cases to 8-bit RGBA before comparison.
- 16bpc: canonical Windows Software return
  `refs/win_references/olm_reference_return_windows_20260703_combined/OLMbit-depthconformancebatch`,
  cases `case_0001..case_0003` (native 16-bit RGBA PNGs, 1920x1080, Search
  Radius 13/13/27).

## Exact Metrics

| Depth / case | Candidate no post-pass | Legacy post-pass | Candidate-vs-legacy changed pixels |
|---|---:|---:|---:|
| 8 / `case_0001` | max 255, mean 0.476157, 0.373457% nonzero | max 255, mean 0.476157, 0.373457% nonzero | 0 |
| 8 / `case_0002` | **max 0, mean 0, 0% nonzero** | max 64, mean 0.319047, 0.989198% nonzero | 5,128 |
| 8 / `case_0003` | max 255, mean 2.007324, 0.814622% nonzero | max 255, mean 2.046704, 0.937259% nonzero | 2,543 |
| 16 / `case_0001` | **max 0, mean 0, 0% nonzero** | **max 0, mean 0, 0% nonzero** | 0 |
| 16 / `case_0002` | **max 0, mean 0, 0% nonzero** | **max 0, mean 0, 0% nonzero** | 0 |
| 16 / `case_0003` | **max 0, mean 0, 0% nonzero** | **max 0, mean 0, 0% nonzero** | 0 |

The 8-bit `case_0002` candidate removes 15,384 changed RGB channels across
5,128 pixels relative to the legacy post-pass and becomes exact. Case 3 also
improves mean and nonzero-pixel error, although it remains non-exact and its
maximum error remains 255. Alpha remains unchanged by this A/B.

## AE Request / PiPL Alpha Convention Inspection

- Mac Smart Pre-render explicitly sets `req.preserve_rgb_of_zero_alpha = TRUE`
  before checkout in `mac/OLMToonDilate/OLMToonDilate.cpp`.
- Mac setup advertises Smart Render and `PF_OutFlag2_FLOAT_COLOR_AWARE`; PiPL
  advertises the matching `AE_Effect_Global_OutFlags_2 { 0x00801400 }` and
  `AE_Effect_Global_OutFlags { 0x02000040 }`.
- The actual-AEX semialpha fixture
  `refs/conformance/olmtoondilate_semialpha_actual_aex_20260716.md` records
  raw four-channel preservation through the PF8/PF16/PF32 copy-helper boundary
  for both premult-looking and straight-looking inputs. That supports raw copy
  ownership at the worker boundary; it does not by itself prove every AE host
  conversion path.

## FACT / INFERENCE

- FACT: The candidate is exact on canonical 8bpc `case_0002`, neutral on
  `case_0001`, improves but does not close `case_0003`, and is neutral/exact on
  all three covered 16bpc cases in this A/B model.
- FACT: The seeded actual-AEX PF32 witness hits the live propagation helper and
  reports the out-of-radius semi-alpha RGB and alpha unchanged after return.
- INFERENCE: Removing the final postpass is supported for the covered candidate
  path, but this remains candidate/CLI/binary-grounded evidence, not AE exact
  and not a broad host-conversion claim.
