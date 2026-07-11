# OLMToonDilate 32bpc Mac Candidates - 2026-07-10

## Result

Mac AE `26.3x87` rendered all three declared OLMToonDilate 32bpc cases through
the `OLM EXR 32 Float` Output Module template. The fail-closed candidate-index
validator accepted all three artifacts.

| Case | SHA-256 | Dimensions | Channels | Type | Compression |
| --- | --- | --- | --- | --- | --- |
| `olmtoondilate__case_0001` | `46677fb262438bb5bdb5250b4ee0dcbbe4db1c2128a3ed87e4c30eca481c2518` | `1920x1080` | `A,B,G,R` | FLOAT | none |
| `olmtoondilate__case_0002` | `2bcc1e013658fa7062e37b78499f9474755357e927113b0ae6c978c61e072a06` | `1920x1080` | `A,B,G,R` | FLOAT | none |
| `olmtoondilate__case_0003` | `184c9d1d84343849ccfef75270fde191a411ed0797b3ffd02e7556932f6b3a02` | `1920x1080` | `A,B,G,R` | FLOAT | none |

Each file contains `8,294,400` finite float samples and no NaN or infinity.

The attempted template name `OLM EXR 32 Float 2` is not registered in the
current AE profile. The verified template remains `OLM EXR 32 Float`.

## Boundary

These are reproducible Mac host candidates, not `AE exact`. The accepted
Windows AE26.3 EXRs still have a cross-platform no-effect RGB split, so direct
effect EXR subtraction cannot attribute differences to OLMToonDilate until the
host baseline is neutralized or comparison moves to typed plug-in buffers.

## Verification

```bash
python3 scripts/verify_32bpc_float_return.py \
  --mac-candidate-index /tmp/olm_ae_32bpc_toondilate_float_20260710/MAC_32BPC_CANDIDATE_INDEX.json
```

Result: `rendered=3 pending=0`.
