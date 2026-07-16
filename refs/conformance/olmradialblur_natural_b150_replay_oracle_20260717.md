# OLMRadialBlur natural B150 replay and float32 oracle (2026-07-17)

- Status: `pass`
- Classification: `bounded-natural-b150-f32-oracle-match`
- Scope: actual Mac AEX natural prefill and `FUN_18000B150` through one return, compared per operation with an independent float32 oracle; no Windows or AE-exact claim.

- Gates: `{'natural_prefill': True, 'reader_outer_one': True, 'one_entry_one_return': True, 'nonzero_span_table': True, 'all_196_oracle_words_match': True, 'bounded_instructions': True}`
- The natural fixture has span `[1, 0]`; all 196 RGBA and scalar output cells match raw float32 oracle words.
