# OLMBlur 8bpc reference/AEX provenance audit

Date: 2026-07-11

## Verdict

The reported formal-batch residual pattern is a reference-generation split,
not evidence that the byte-exact shared core should be reverted:

| case | reported max | archived legacy drift max |
| --- | ---: | ---: |
| `0001/0002` | 59 | 59 |
| `0003` | 14 | 14 |
| `0004` | 58 | 58 |
| `0005/0006` | 0 | 0 |
| `0007` | 1 | legacy family has a separate one-value witness |

The first four values and their red-only shape match the existing
`20260604_olm` legacy-reference audit exactly. They do not match the
normalized 8bpc family used by the clean 20260619 request.

## Reference families

### Legacy 20260604 family

`refs/win_references/20260604_olm/OLMBlur/reference_manifest.json` records:

- Windows AE `25.2x131`
- created `2026-06-04T21:25:17.894+09:00`
- 1920x1080, 24 fps, 8bpc
- source PNGs dated June 4
- the same case parameters used by the later normalized request

The retained comparison audit reports exactly the observed drift:
`0001/0002=59`, `0003=14`, `0004=58`, and `0005..0007=0`.

### Normalized 20260619 request family

The request ZIP is
`refs/reports/ae_host_validation_20260618_232926/normalized_ae_pixel_requests_20260619_003631/olmblur_request.zip`.
Its expected PNG entries are timestamped June 18 and its manifest records:

- Windows AE `26.2x49`
- created `2026-06-18T22:51:05+09:00`
- 1920x1080, 24 fps, 8bpc
- the same seven cases and matching parameter values

The returned Mac AE batch at
`refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619`
compares exact for all seven cases. Its PNGs are byte-identical to the
normalized references, including `case_0001`; they are not byte-identical to
the 20260604 legacy PNG for that case. The older provenance audit therefore
correctly classifies the normalized family as `normalized-software-exact-with-legacy-drift`.

## AEX inventory and hash evidence

The helper fixture manifest records the actual binary used by the current
Unicorn fixtures:

```text
plugins_2025/OLMBlur.aex
SHA-256 f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b
```

That hash is also the 2025 OLMBlur binary in the official ZIP snapshot dated
2026-06-19, and the checked-in `plugins_2025/OLMBlur.aex` is byte-identical to
that snapshot. The inventory contains multiple materially different AEXs,
including 2022/2023 (`97033f...`), 2024 (`4e64b2...`), and 2025 (`f06117...`).

However, neither the 20260604 nor 20260618/19 reference manifest records an
AEX filename, SHA-256, installed plugin path, or plugin build identity. The
reference pixels therefore prove an AE-version/reference-generation split,
but do **not** prove which AEX hash was loaded for either Windows render.

## Decompilation provenance

`decomp/OLMBlur.aex.c.txt` and `disasm/OLMBlur.aex.asm.txt` are local
decompilation/disassembly of the 2025 binary above: their timestamps are
2026-04-18 and the fixture manifest binds the helper evidence to its hash.
The decompilation is not evidence that the 20260604 or 20260618/19 Windows
renders loaded that same binary. It is evidence for the current helper
fixture only.

## Classification

- **Proven:** the reported max-diff pattern is the old 20260604 reference
  family, while the normalized 20260619 expected/candidate family is 7/7
  exact.
- **Proven:** the current helper fixture is grounded to AEX 2025 hash
  `f0611785...e96e5b`.
- **Not proven:** that either Windows reference family was rendered with a
  different AEX hash than the fixture binary. The manifests omit that field.
- **Action:** preserve the exact shared core and Mac implementation. First
  verify the formal batch's expected directory and record its manifest hash;
  if it is the 20260604 family, replace the expected set with the normalized
  20260619 request family before interpreting residuals as implementation
  failures.

No core, Mac, ledger, NAS, or existing report was edited.
