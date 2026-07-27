# OLMSmoother2 32bpc case-01..10 Mac candidate audit

Superseded by the same-source Windows recapture and full exact closeout in
`refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.md`.

Mac AE `26.3x87` rendered all ten random Smoother2 cases with the final
diagnostic-free binary
`c14bb3424b8b8ce58d09fe372a443f844319d18fec5db5ef1cfc1019e3e839eb`.
Every Mac no-effect result is raw exact with its hash-bound Windows
before-effects EXR at all `8,294,400` FLOAT32 words.

| case | old bulk effect mismatches | max raw-u32 delta | classification |
| --- | ---: | ---: | --- |
| 01 | 21,511 | 102,237,492 | effect mismatch candidate |
| 02 | 134,113 | 67,108,281 | effect mismatch candidate |
| 03 | 15,288 | 110,289,668 | effect mismatch candidate |
| 04 | 0 | 0 | candidate exact; Windows PF32 entry unproven |
| 05 | 12,058 | 106,288,799 | effect mismatch candidate |
| 06 | 0 | 0 | candidate exact; Windows PF32 entry unproven |
| 07 | 0 | 0 | AE exact under independent Preserve-RGB contract |
| 08 | 0 | 0 | candidate exact; Windows PF32 entry unproven |
| 09 | 0 | 0 | AE exact under independent Preserve-RGB contract |
| 10 | 0 | 0 | candidate exact; Windows PF32 entry unproven |

The zero rows for 04/06/08/10 are not promoted yet. The old bulk Windows
effect renders did not import the exported before-effects EXRs, so an exact
Mac no-effect control does not prove identical Windows effect-entry words.
Case-07 is the concrete counterexample: it is exact under its independently
captured Preserve-RGB contract, but the same current Mac render differs from
the old bulk case-07 effect artifact by `4,318,279` words with maximum raw-u32
delta `991,472,415`.

The next fail-closed gate is a Windows AE recapture of cases
01–06/08/10 which imports the same hash-bound Preserve-RGB EXR used on Mac,
and produces same-process no-effect/effect-on FLOAT32 pairs. Alternatively,
a same-run Windows PF32 effect-entry capture may prove equality with the
bound source.

This audit therefore preserves only the already independent case-07 and
case-09 `AE exact` claims. It records 04/06/08/10 as strong candidates and
does not treat CLI output or old bulk EXR agreement as a substitute for the
missing Windows entry contract.
