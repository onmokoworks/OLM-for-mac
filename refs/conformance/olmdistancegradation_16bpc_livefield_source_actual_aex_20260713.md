# OLMDistanceGradation 16bpc livefield/source actual-AEX manifest

Date: 2026-07-13T01:23:56Z

## Status

- `no_exact_livefield_replays`
- Strict rule: replay only if both coordinate-bound source raw words and field raw words are already present in existing Windows returns/traces.
- PNGs were not used to invent missing input words.

## Family summary

| Case | Located live points | Exact replayable | Status | Missing for exact replay |
| --- | ---: | ---: | --- | --- |
| case_0024 | 0 | 0 | no_return_trace_point_with_livefield_source_words_located | live coordinate-bound source input witness, live field raw words |
| case_0025 | 0 | 0 | no_return_trace_point_with_livefield_source_words_located | live coordinate-bound source input witness, live field raw words |
| case_0026 | 4 | 0 | partial_evidence_only | field_raw_words_agrb, field_word_at_rcx_plus_2 |
| case_0027 | 0 | 0 | no_return_trace_point_with_livefield_source_words_located | live coordinate-bound source input witness, live field raw words |

## Located candidates

| Case | XY | Source RGBA16 | Source raw words AGRB | Field X from trace | Carry store AGRB16 | Missing for exact replay |
| --- | --- | --- | --- | ---: | --- | --- |
| case_0026 | `(907, 222)` | `[0, 65535, 10794, 65535]` | `[65535, 65535, 0, 10794]` | `0.121742934` | `[32645, 0, 129, 65535]` | field_raw_words_agrb, field_word_at_rcx_plus_2 |
| case_0026 | `(395, 477)` | `[65535, 0, 0, 65535]` | `[65535, 0, 65535, 0]` | `0.161361381` | `[32513, 0, 268, 65535]` | field_raw_words_agrb, field_word_at_rcx_plus_2 |
| case_0026 | `(1589, 579)` | `[65535, 0, 0, 65535]` | `[65535, 0, 65535, 0]` | `0.783686459` | `[17281, 0, 16238, 65535]` | field_raw_words_agrb, field_word_at_rcx_plus_2 |
| case_0026 | `(898, 670)` | `[0, 0, 0, 65535]` | `[65535, 0, 0, 0]` | `0.888987124` | `[11280, 0, 22529, 65535]` | field_raw_words_agrb, field_word_at_rcx_plus_2 |

## Supplemental trace-only evidence

- `case_0026` row0 ramp trace: `y=0`, `x=0..14`
- Source RGBA16: `[0, 0, 0, 0]`
- Missing: field_raw_words_agrb, field_word_at_rcx_plus_2, per-pixel source raw words beyond semantic zero RGBA16, post-call exact output words

## Verdict

- No exact replays were run because no located family point includes returned field raw words.
- The strongest usable evidence today is `case_0026` only: exact source semantic RGBA16 is present for four traced points, but the matching field raw word at `[RCX+2]` is still absent from the returns/traces.
