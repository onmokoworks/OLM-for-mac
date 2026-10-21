# OLMBlur PF16 retained Legacy tuples: exported public owner

Status: **PASS_THREE_LEGACY_RETAINED_EXACT_ONE_PUBLIC_MISMATCH_FAIL_CLOSED**

The exact 12x12/Amount3/Repeat2/Bias1 and 18x18/Amount11/Repeat3/Bias2
constant-alpha Legacy rows, plus 18x12/Amount3/Repeat2/Bias2 mixed-alpha, are
raw exact.  The exact 20x16 Smoothness62.5 word-boundary row differs by 369
active bytes and remains fail-closed.  Padding is untouched in all four rows.

Repository AexLoader/Unicorn execution of the current Windows exported SmartPreRender/SmartRender owner. The exact 12x12 and 18x18 constant-alpha Legacy rows plus the exact 18x12 mixed-alpha Legacy row are promotable. The exact Smoothness62.5 word-boundary row differs from its retained worker oracle and must remain public fail-closed.
