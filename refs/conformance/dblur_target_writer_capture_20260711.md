# DirectionalBlur target-writer capture

- Status: `ok`
- Actual AEX/Unicorn helper calls only; source `(959,169)` was not forced.
- No Mac source, ledger, existing artifact, NAS, coefficient, or PNG edits.

| target | helper calls | source x range | direction | span | B address | pre/post B RGBA | denom | valid |
| --- | ---: | --- | --- | --- | ---: | --- | --- | --- |
| `(494, 169)` | 465 | `[495, 959]` (465) | `[1]` | `[1064]` | `0x20a64ae0` | `[0.0, 0.0, 0.0, 1.0]` | `1.0` | `1.0` |
| `(579, 169)` | 380 | `[580, 959]` (380) | `[1]` | `[1064]` | `0x20a65030` | `[0.0, 0.0, 0.0, 1.0]` | `1.0` | `1.0` |

## Reading

The JSON is aggregated per target. It retains bounded first/last helper representatives plus capped nonzero/change events, never the full 845-call stream. Source RGB and target B RGB are zero for every retained event; alpha/valid remains 1.0. Final host-store bytes are unavailable at the rowdriver boundary, so the next exact boundary is the host output write after rowdriver normalization/rotate-back.
