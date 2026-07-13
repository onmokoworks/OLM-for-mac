# OLMDistanceGradation case0026 live field/source witness package

This package is scoped to one fresh Windows current-AEX Software 16bpc run of
`olmdistancegradation_extended__case_0026`.

Required witness points: (907,222), (395,477), (1589,579), (898,670)

The return is valid only when all four points share one AE/CDB run id and each
point carries:

- the live case tuple bound from the callback's parameter block
- source raw `A,G,R,B` words
- field raw `A,G,R,B` words plus `[RCX+2]`
- pre-call output words and post-call output words around `FUN_181170480`

Any missing point or field is `exact_bind_failure`. Partial answers are
forbidden.

The packaged runner relays through Windows PowerShell 5.1 with one explicit
quoted `ArgumentList` string. Do not replace it with an argument array.
