# OLMBlur Mac-Lane Differential

Date: 2026-07-16

## FACT

- The retained local AEX is `plugins_2025/OLMBlur.aex`, SHA-256
  `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- The actual AEX PF16 writer at `0x1800030e2` stores controlled raw values
  `1100.5`, `1101.5`, and `32767.5` as RGB words `1101`, `1102`, and
  `32768`. This matches add-`0.5` then truncate, and rejects nearest-even at
  the `1100.5` tie.
- Portable OLMBlur 16bpc Non-Legacy output matches the actual AEX byte-for-byte
  for two complete fixtures: Repeat 2 / bias 1 and Repeat 3 / bias 2.
- Portable OLMBlur 32bpc Non-Legacy output matches the actual AEX byte-for-byte
  for seven complete fixtures covering Repeat 2, 3, 4, and 10, both bias
  directions, and large-radius controls.
- The 32bpc Repeat 2 and Repeat 10 fixtures use the same source and produce
  different expected hashes, proving Repeat is active in the local float worker
  boundary rather than being ignored or collapsed.
- The existing 8bpc CLI smoke remains green, including its established exact
  cases.

## INFERENCE

- The current portable 16bpc writer conversion is consistent with the actual
  AEX writer boundary. The remaining sign-mixed one-word 16bpc AE residuals
  therefore are not evidence for a global nearest-even writer replacement;
  they remain pre-store/helper or host-reference questions.
- The 32bpc Non-Legacy worker's channel/Repeat semantics are locally
  binary-grounded through the actual AEX CPU boundary. This does not establish
  Windows or AE-host output equivalence, and it does not justify changes to the
  32bpc Mac adapter.
- No production code or global writer rule was changed by this proof.

## Reproduction

```text
python3 tools/emulation/test_olmblur_mac_lane_differential_20260716.py
python3 refs/scripts/smoke_olmblur_mac_lane_differential_20260716.py
```

Both commands passed on 2026-07-16. Windows/SSH output and 32bpc recapture
remain external-pending.
