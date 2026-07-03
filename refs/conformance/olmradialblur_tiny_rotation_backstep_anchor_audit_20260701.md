# OLMRadialBlur tiny Rotation Backstep Anchor Audit

- Case: `case_0010`
- Witness: `(1614, 6)`
- Active contract: `refs/conformance/olmradialblur_tiny_rotation_anchor_watch_followup_contract_20260701.md`
- Historical predecessor contract: `refs/conformance/olmradialblur_tiny_rotation_backstep_followup_contract_20260701.md`
- Decision: `anchor-stable-upstream-branch-still-missing`
- Reason: The anchored inverse sampler for `case_0010 (1614,6)` is locally stable: it samples rows 844/845 at angle indices 1603/1604, all direct source cells are black, and the current witness remains near-black before final U8 conversion. The nearest positive family that could still plausibly explain the missing white lobe sits one row above at row 843 around angles 1601..1602, so the next Windows proof still needs the first upstream branch that decides how that family is included, substituted, or discarded before final inverse sampling.
- Why this anchor matters: This anchor removes ambiguity about the last observed sample point. The remaining uncertainty is not where the final bilinear sample lands, but which earlier branch populates or promotes the RGB feeding that sample.

## Inverse-Sampler Anchor

- angle_index: `1603.83948`
- radius_index: `844.317505`
- indices: `[1603, 1604, 844, 845]`
- witness sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- witness sample U8: `[0, 0, 0, 255]`
- current output U8: `[0, 0, 0, 255]`
- validity alpha U8: `255`

## Direct Support At The Anchor

- supporting rows: `[844, 845]`
- same-row direct source cells all black: `True`

| Cell | radius_row | same_row_source_taps | cell_rgb | src_cell_rgba |
| --- | ---: | --- | --- | --- |
| `x0y0` | `844` | `[1603, 1602, 1601]` | `[-0.0147110438, -0.0147110438, -0.0147110438]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x1y0` | `844` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x0y1` | `845` | `[1603, 1602, 1601]` | `[-0.0485489555, -0.0485489555, -0.0485489555]` | `[0.0, 0.0, 0.0, 1.0]` |
| `x1y1` | `845` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |

## Nearest Upstream Positive Family

- dominant cluster rows: `[843]`
- dominant cluster angles: `[1601, 1602]`
- dominant local positive cluster: `[{'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}]`
- strongest positive cells: `[{'xy': [1608, 838], 'rgba': [0.452643, 0.452643, 0.452643, 1], 'luma': 0.45264299999999996}, {'xy': [1601, 843], 'rgba': [0.168253, 0.168253, 0.168253, 1], 'luma': 0.168253}, {'xy': [1602, 843], 'rgba': [0.0893472, 0.0893472, 0.0893472, 1], 'luma': 0.0893472}, {'xy': [1608, 839], 'rgba': [0.0355792, 0.0355792, 0.0355792, 1], 'luma': 0.0355792}]`
- strongest negative cells: `[{'xy': [1601, 845], 'rgba': [-0.624861, -0.624861, -0.624861, 1], 'luma': -0.624861}, {'xy': [1601, 844], 'rgba': [-0.189342, -0.189342, -0.189342, 1], 'luma': -0.189342}]`

## Windows Anchor-Watch Ask

- Start from the reliable inverse-sampler hit near `(angle=1603.83948, radius=844.317505)` for `case_0010 (1614,6)`, then step backward until one typed upstream branch/value explains how the pixel can move from near-black to the final white Windows byte.
- Preferred retained caller-side chain: `['+0xf252', '+0xf250', '+0xe']`

## Reading

- The final sample point is no longer the ambiguous part.
- The witness is already near-black at the anchored inverse-sampler point, with direct source support on rows 844/845 only.
- The closest positive family lives one row above at row 843, so the remaining question is the upstream inclusion/substitute path, not final byte conversion.

