# OLMSmoother2 synthetic c280/cce0 float32 witness

Artifact suffix: `20260717`.

## Verdict

- Verdict: `LOCAL_SYNTHETIC_BITWISE_MATCH`.
- Scope: `local checked-in AEX versus portable c280/cce0 float32-word witness; not live Windows, not After Effects host truth, not case_0012 continuation`.
- Fixture exact on both sides: `True`.
- Caller config exact on both sides: `True`.
- All compared float32 words bitwise equal: `True`.

## Caller Config

- Fixed-point words: `65536/65536`.
- Normalized values: `655.36/655.36`.
- Gamma mode byte: `0`.

## Binary Grounding

- AEX function: `FUN_18000b120`.
- Direct scalar divides: `0x18000b17c`, `0x18000b181`, `0x18000b18f` (`DIVSS`).
- Portable rule: divide each RGB channel directly by alpha; a shared reciprocal followed by multiplication changes the float32 rounding point.

## First Divergence

- No differing float32 word was observed in the bounded c280/cce0 sequence.

## Compared Words

| Index | Label | AEX u32 | Portable u32 | Equal |
| --- | --- | --- | --- | --- |
| 0 | `c280_rgba.r` | `0x3f4ccccd` | `0x3f4ccccd` | `True` |
| 1 | `c280_rgba.g` | `0x3dcccccd` | `0x3dcccccd` | `True` |
| 2 | `c280_rgba.b` | `0x3dcccccd` | `0x3dcccccd` | `True` |
| 3 | `c280_rgba.a` | `0x3f7efeff` | `0x3f7efeff` | `True` |
| 4 | `c280_weight` | `0x3effffd9` | `0x3effffd9` | `True` |
| 5 | `cce0_rgba.r` | `0x3f66734b` | `0x3f66734b` | `True` |
| 6 | `cce0_rgba.g` | `0x3f0d06cf` | `0x3f0d06cf` | `True` |
| 7 | `cce0_rgba.b` | `0x3f0d06cf` | `0x3f0d06cf` | `True` |
| 8 | `cce0_rgba.a` | `0x3f7f7f80` | `0x3f7f7f80` | `True` |

## Reproduction

```sh
tmp=$(mktemp -d)
clang++ -std=c++17 -O2 \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_case0012_post_leaf_cce0_adapter_20260717.cpp \
  -o "$tmp/synthetic_c280_cce0"
python3 tools/emulation/test_olmsmoother2_case0012_post_leaf_cce0_20260717.py \
  --adapter "$tmp/synthetic_c280_cce0" \
  --output-json refs/conformance/olmsmoother2_case0012_post_leaf_cce0_20260717.json \
  --output-md refs/conformance/olmsmoother2_case0012_post_leaf_cce0_20260717.md
```

## Claims Not Made

- No live Windows or After Effects host claim.
- No case_0012 continuation claim.
- No post-leaf state transfer claim.
- No production correctness claim.
- No ledger change.
