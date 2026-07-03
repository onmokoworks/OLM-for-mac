# OLM Trace Return Classification

Updated: 2026-07-01

This note fixes the vocabulary for imported Windows runtime-trace returns.
The point is to avoid overvaluing a return just because it contains logs.

## Classes

| Class | Meaning | Implementation may move? |
| --- | --- | --- |
| `answered` | The exact requested witness landed: case, XY, breakpoint/callsite, and requested values are present | Yes |
| `answered_partial` | Part of the requested structure landed, but the proof boundary is still incomplete | Usually no; only if the partial result explicitly closes an alternative |
| `failed_breakpoint_watchpoint` | The planned stop failed, but the failure reason is exact and itself narrows the lane | No direct code move, but may change the next request |
| `trace-too-sparse` | The return contains some logs or structure, but not enough typed values to support a decision | No |
| `not isolated` | The right region/path was hit, but the target witness was not separated from neighboring state | No |
| `non-actionable` | Historically useful context exists, but it does not advance the active proof lane | No |

## Required fields for an actionable return

An `answered` return should usually include all of:

- request id
- target case id
- target XY or representative family name
- exact breakpoint / function / callsite actually hit
- the registers / locals / floats / words named in the request contract
- enough context to compare against the local baseline

If any of those are missing, prefer one of the non-`answered` classes above.

## Hard-plugin stop line

For the current hard lanes, these are not enough by themselves:

- final PNG only
- final writer word only
- branch names without typed values
- old-template merged logs
- “looks close” screenshots

That means:

- `OLMRadialBlur` needs caller-side or source-population witness values
- `OLMSmoother2 legacy` needs producer-path reconstruction from a writer anchor
- `OLMKiraKira` needs compose/writeback hotspot values

## Intake rule

When importing a new runtime return:

1. Assign one class from this note.
2. Record why it is not `answered` if it is partial.
3. Name the next allowed request or explicitly say “do not resend broad package”.
