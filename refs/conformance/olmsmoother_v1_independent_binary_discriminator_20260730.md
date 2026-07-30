# OLMSmoother v1 Independent-Binary Discriminator — 2026-07-30

## Result

The standalone `OLMSmoother.aex` and `OLMSmoother2.aex` forced to
`Smoother Version = 1` are discriminated on all three hash-pinned PF8 inputs.
Their raw PF8 ARGB hashes differ in `3/3` cases. Their decoded worker PNG and
round-premultiplied export comparisons are also non-exact in `3/3`.

Therefore standalone v1 cannot be replaced by, or formally mapped to,
Smoother2 forced-v1 on this evidence.

| Case | Raw PF8 hash | Decoded RGBA mismatched bytes | Premultiplied mismatched bytes | Max diff |
| --- | --- | ---: | ---: | ---: |
| `case_0001` | different | 633 | 633 | 63 |
| `case_0002` | different | 982 | 982 | 63 |
| `case_0003` | different | 1542 | 1543 | 123 |

## Identity and setup gates

- Retained full source report:
  `refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json`
- Full source report SHA-256:
  `3008b8239c48e56c6d0fb0aa707ef7e46df41d311c8f8aa710a79503e2d75735`
- Observed AEXCompat build-source commit:
  `8d2374bba6f618932593589e3a6530682dc6a615`
- Worker SHA-256:
  `d9f0f54c894690b77f848543fbca2a1366a7aaadc0c0984ab9ef643d64d499f1`
- Standalone v1 AEX SHA-256:
  `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`
- Smoother2 AEX SHA-256:
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- Both binaries returned `global_setup_error=0` and
  `params_setup_error=0`.
- The reduced JSON retains the exact three-slot v1 and fifteen-slot Smoother2
  parameter surfaces, including type IDs.

The observed source commit is metadata, not a central claim: it is not
cryptographically bound to the retained worker SHA-256. Worker and AEX byte
identities, full-report identity, setup/readback gates, and measured outputs
carry the discrimination claim.

## Boundary

This is AEXCompat local-execution evidence only. It is not After Effects host
evidence, does not establish `AE exact`, and proves nothing about 16bpc or
32bpc behavior. The conclusion is limited to the three declared,
hash-identified PF8 inputs and the recorded parameter policy.

The full report contains temporary `output_png` paths emitted during execution.
Those paths are ephemeral diagnostics, are not artifact identities, and are
excluded from the reduced attestation and its claims.
