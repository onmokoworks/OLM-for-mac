# OLMSmoother2 legacy upstream descriptor local probe - 2026-07-16

- Status: `LOCAL_DIAGNOSTIC_NOT_WINDOWS_TRUTH`
- Case: `legacy_case_0012_gamma5_red_blue_current_aex`
- Input: current-AEX 8bpc before-effects frame
- Mac CLI: current `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`

## Command

`cli/OLMSmoother2/olmsmoother2_cli --input <case_0012_before_effects.png> --params <case_0012.json> --output <output.png> --trace-pixel <x,y>`

The command was run once for `91,841` and once for `92,841`.

## FACT

At the old Mac max-diff coordinate `91,841`, the local path remains:

- `build_polygon idx=105`
- `cardinal6 desc=(91,841,1,91,843,5)`, key `50`
- `e170 c=2`
- one `f270/e3a0` append

At the corrected Windows producer coordinate `92,841`, the local path is:

- `build_polygon idx=67`
- `cardinal6 desc=(92,840,1,92,843,2)`, key `20`
- `e170 c=4`

The accepted Windows actual-AEX run at the corresponding producer lane reports:

- live descriptor `(92,841,1,92,842,2)`
- `e170 c=7`

## Conclusion

Moving the local diagnostic origin from `91,841` to `92,841` does not reproduce
the Windows descriptor. The two scanner endpoints remain displaced by one row:

- first triple: Mac `y=840`, Windows `y=841`
- second triple: Mac `y=843`, Windows `y=842`

This narrows the next proof to the class-plane bytes and stop predicates consumed
by `FUN_18000d3b0` and `FUN_18000da50` around `x=91..93`, `y=840..844`.
It does not justify changing the descriptor coordinates or dispatcher directly.

## Claims Not Made

- No Mac AE exact claim
- No claim that the CLI class plane is host-identical
- No source patch from this local diagnostic alone
