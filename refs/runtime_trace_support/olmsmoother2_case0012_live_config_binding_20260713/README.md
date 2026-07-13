# OLMSmoother2 case0012 live config binding package

This package is scoped to one fresh Windows current-AEX Software run of
`legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`.

The contract is the existing live-config binding contract:

- capture c280 config raw bytes and decoded `scale_fixed`
- capture cce0 gamma-context raw bytes and decoded `mode_byte` / `mode_name`
- keep every observation on one run id
- fail closed as `exact_bind_failure` if any bind/read is missing

The local replay defaults (`scale_fixed=[65536,65536]`, `mode_byte=0`) are
schema-only evidence and must not be copied into a Windows answer.
