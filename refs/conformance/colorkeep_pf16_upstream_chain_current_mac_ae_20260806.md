# ColorKeep PF16 upstream host-chain evidence (2026-08-06)

## Scope

This is a bounded After Effects 2026 (26.3x87) host proof for the current installed
`ColorKeep.plugin`. It does not promote the plugin to a general AE-exact claim.

The test-only `OLM PF16 Fixture Source` effect wrote twelve explicit `PF_Pixel16`
ARGB tuples into a 16-bpc Software-rendered composition. The effect was immediately
followed by the installed `OLM Color Keep`, configured with the three public RGB
keys `(1,1,1)`, `(0.25,0.75,1)`, and `(0,0,0)`.

Both Mach-O images were verified as mapped in the same AE PID during the run:

- fixture source SHA-256: `ca098f4309c53d50eb16c67ecadde777c1ac2d29024d03103d46ea6d030b65b8`
- ColorKeep SHA-256: `ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce`

## Result

The source-only FLOAT EXR retained extended alpha values, including
`32769/32768` and `65535/32768`. Its RGB output also contains values above 1.0,
although RGB is subject to AE output/premultiplication semantics and is not used
as a byte-for-byte PF16 readback.

With ColorKeep enabled, the twelve output alpha values were exactly:

```text
1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0
```

This exactly matches the actual-AEX writer expectation. In particular, the
extended and near-key PF16 cases are cleared rather than being normalized into
the three public keys before ColorKeep. This proves that the current Mac host
chain delivered the extended PF16 values from the upstream effect to ColorKeep
for this discriminator.

Machine-readable evidence is in
`refs/mac_validation_runs/colorkeep_pf16_upstream_chain_20260806_run5/candidate_return.json`.
The status is `host_chain_alpha_discriminator_exact`, while `ae_exact_claim`
intentionally remains `false`.

## Boundary

This closes the specific imported-file ambiguity for the tested inter-effect
PF16 path. It does not prove every AE renderer, color-management setting, output
module, pixel format, or platform produces identical final files.
