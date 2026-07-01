# OLMBlur Writer-Only Hypothesis Audit

- Date: `2026-06-30`
- Baseline: `refs/conformance/olmblur_current_word_baseline_20260629.json`
- Diagnosis counts: `{'floor05-only-match': 1, 'writer-rule-irrelevant-at-this-witness': 2, 'nearby-only-match': 1, 'both-writer-rules-match': 2}`

## Witness Matrix

| Case | Bit depth | XY | Reference | Candidate | nearby | floor05 | Best | Diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `olmblur__case_0006` | `16bpc` | `(314,14)` | `[2201, 2201, 2201, 65535]` | `[2199, 2199, 2199, 65535]` | `[2199, 2199, 2199, 65535]` | `[2201, 2201, 2201, 65535]` | `floor05` | `floor05-only-match` |
| `olmblur__case_0006` | `16bpc` | `(29,71)` | `[725, 725, 725, 65535]` | `[727, 727, 727, 65535]` | `[727, 727, 727, 65535]` | `[727, 727, 727, 65535]` | `tie` | `writer-rule-irrelevant-at-this-witness` |
| `olmblur__case_0007` | `16bpc` | `(345,672)` | `[1247, 0, 25087, 65535]` | `[1247, 0, 25089, 65535]` | `[1247, 0, 25087, 65535]` | `[1247, 0, 25089, 65535]` | `nearby` | `nearby-only-match` |
| `olmblur__case_0007` | `16bpc` | `(0,0)` | `[0, 0, 0, 65535]` | `[0, 0, 0, 65535]` | `[0, 0, 0, 65535]` | `[0, 0, 0, 65535]` | `tie` | `both-writer-rules-match` |
| `case_0007` | `8bpc-old-normalized` | `(488,941)` | `[251, 0, 0, 255]` | `[250, 0, 0, 255]` | `[250, 0, 0, 255]` | `[250, 0, 0, 255]` | `tie` | `writer-rule-irrelevant-at-this-witness` |
| `case_0007` | `8bpc-old-normalized` | `(488,942)` | `[251, 0, 0, 255]` | `[251, 0, 0, 255]` | `[251, 0, 0, 255]` | `[251, 0, 0, 255]` | `tie` | `both-writer-rules-match` |

## Decision

- `writer-only-swap-cannot-explain-all-active-witnesses`

## Interpretation

- A pure non-Legacy writer swap from nearbyint to floor05 would fix the 16bpc witness (314,14), but it leaves (29,71) unchanged and does not explain the sign-mixed family by itself.
- The surviving 16bpc Legacy witness (345,672) actually prefers nearbyint at the exact Mac-side raw=12544.5 value, and a 2026-06-30 Windows databreak witness now confirms the Windows pre-store blue float is `12544.498046875` before `cvttss2si -> 12544`. So this lane is now directly explained as a pre-store float delta on Windows rather than a different local Legacy writer rule.
- The surviving old 8bpc Legacy witness (488,941) is not solved by either local floor05 or nearbyint because the current raw value is already below 250.5; Windows must either reach a slightly larger pre-store float or differ earlier in state.
- Therefore the pending Windows final-word witness is still required: we need the actual Windows pre-store/helper boundary, not a blind source-side writer rewrite.
