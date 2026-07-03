# OLMDistanceGradation case_0023 Output-word Triplet Return Acceptance - 2026-07-01

Judge `olmdistancegradation_case0023_output_word_triplet_followup_20260701`
like this.

`answered`

- the return binds one of the witness triplet pixels from the output-word
  address or compose refcon at `FUN_181170480`
- and it provides typed helper/compose values that explain the
  `35.014 -> 36.013 -> 37.013` crossing at that exact hook

`failed_partial`

- the return preserves useful output-word / compose-refcon context
- but it still does not bind the witness triplet strongly enough to expose the
  consumed helper/compose values for the same pixel

`trace-too-sparse` / `not isolated`

- only final endpoint colors again
- broad callback activity with no output-word or compose-refcon binding
- no typed helper/compose values
- no exact failed bind/watchpoint reason

Do not treat “the crossing still exists” as answered. The point here is the
triplet-specific consumed value at the real hook.
