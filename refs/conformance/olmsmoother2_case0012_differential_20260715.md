# OLMSmoother2 case_0012 local differential analysis

Date: 2026-07-15

## Scope

Local Smoother2 fixture/return analysis for
`legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`. The analyzer
consumes the requested `e170`, `c280`, and `cce0` typed fields, together with
the `f270`/`e3a0` append evidence and final writer corroboration.

## FACT

- `scripts/analyze_smoother2_case0012_differential.py` accepts a CDB trace,
  return JSON, or return ZIP.
- The complete local fixture is normalized into producer, config, and writer
  snapshots and requires one identity tuple, one event for each required stage,
  and all requested typed fields.
- Missing or duplicate events, identity drift, or incomplete typed fields
  produce `BLOCKED_INCOMPLETE_RETURN`.
- An explicit local reference produces `MATCHES_LOCAL_REFERENCE` or a first
  differing boundary: `DIFF_AT_PRODUCER`, `DIFF_AT_CONFIG`, or `DIFF_AT_WRITER`.

## INFERENCE

- The first differing boundary is an attribution aid for the next local trace
  comparison, not proof of causality in Windows After Effects.
- Without an explicit local reference, `READY_TYPED_FIELDS_ONLY` means only
  that the returned typed evidence is complete; it does not promote fixture
  values to live expectations.

## c280 Entry Binding

### FACT

- `FUN_18000c280` is decompiled with five arguments; its fifth argument is
  `param_5`.
- The disassembly loads that argument from `[RBP+0x100]` after the prologue,
  then reads scale fields at `+0x20` and `+0x24`.
- At the entry breakpoint, the corresponding Windows x64 stack argument is
  `poi(@rsp+0x28)`, so the common-core probe gates and reads c280 through that
  expression rather than through the entry-time `RAX` register.

### INFERENCE

- The stack-slot mapping is the ABI-consistent interpretation of the
  prologue/decompiler evidence. It does not prove that every c280 hit belongs
  to the selected case; the existing writer bind, cce0 pointer identity, and
  fail-closed event cardinality remain required.

## Verification

```text
python3 refs/scripts/smoke_analyze_smoother2_case0012_differential.py
python3 tools/emulation/test_smoother2_case0012_differential.py
```
