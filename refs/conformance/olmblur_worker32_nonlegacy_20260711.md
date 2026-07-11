# OLMBlur 32bpc Non-Legacy Complete Worker

Date: 2026-07-11

## Scope

Portable orchestration for the actual AEX `FUN_180004b80`, the 32bpc
Non-Legacy worker. The implementation uses the exact portable
`FUN_180001000` / `FUN_180001980` core and keeps the six contiguous subpasses
and branch map from the AEX.

## Contract

- Input and output pixels are little-endian float32 `A,R,G,B`.
- The destination is initialized with a complete source copy.
- Staging stores raw R/G/B float32 values and an active flag of `A != 0`.
  This preserves negative and out-of-range alpha semantics; the fixture
  inputs include both zero and negative alpha.
- Each repeat computes the captured decay, truncated radius, sigma, and
  float32 Gaussian weights. Bias `1` runs six horizontal calls then six
  vertical calls; bias `2` reverses that order.
- The writer stores only R/G/B back as float32. Alpha remains the copied
  source alpha. There is no clamp, quantization, EXR conversion, or host
  output step.

## Actual-AEX Fixtures

The exporter `tools/emulation/test_olmblur_worker32_nonlegacy.py` executes
`FUN_180004b80` from AEX SHA-256
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` and
writes raw float buffers under
`tools/emulation/fixtures/olmblur_worker32_nonlegacy/`.

| Case | Shape | Amount | Repeat | Bias | Expected SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `32bpc_nonlegacy_basic` | 12x12 | 3 | 2 | 1 | `e5f2a5f11c0dd3b1b9ef4df231017b9b1fdea58730920a9294dee29bdc86cc87` |
| `32bpc_nonlegacy_large_radius_reverse` | 18x18 | 11 | 3 | 2 | `2e98fd35416665c40f618f1a51c0deac2e93a1439865210630cbcef6d5662757` |
| `32bpc_nonlegacy_amount1294_bias1` | 4x3 | 129.4 | 2 | 1 | `864ba02f8d13a0f06964a4baa6a6de2a4fe716a946d73431578a4b0203143f7d` |
| `32bpc_nonlegacy_amount1294_bias2` | 4x3 | 129.4 | 2 | 2 | `00478e6c1c3d4dd5a02e3bfbd7c5c22318864d2e817e387eff3a97cb43c0b6b5` |
| `32bpc_nonlegacy_amount1256_repeat4` | 4x3 | 125.6 | 4 | 1 | `125a0a0590f0572228593a8bc71452ac8642e5d97411a032e3eeb3011652d7f5` |
| `32bpc_nonlegacy_amount5_repeat2` | 7x5 | 5 | 2 | 1 | `fb389dc49dacf988aa5fb7e595805f62994e386ffcb22f55e0ab3441a16d213e` |
| `32bpc_nonlegacy_amount5_repeat10` | 7x5 | 5 | 10 | 1 | `66065bdb3e32f81612ce70f9a6535fc1c475f3618ccb343a53c35612bf921e85` |

All cases use smoothness `100.0`. The five small cases preserve the same
float32 RGBA gradient and zero/negative-alpha boundaries as the existing
fixtures while keeping the 129.4 and 125.6 weight allocations tractable.

The expected buffers are complete A/R/G/B outputs and are compared byte for
byte by the portable replay. No EXR or host-rendered output is used as an
oracle. NaN payloads are not asserted because no NaN-specific AEX support was
needed for these complete-worker fixtures.

## Verification

```text
c++ -std=c++17 -O2 -ffp-contract=off -Icore \
  core/olmblur_helper.cpp core/olmblur_worker32_nonlegacy.cpp \
  tools/emulation/replay_olmblur_worker32_nonlegacy.cpp \
  -o /tmp/replay_olmblur_worker32_nonlegacy
/tmp/replay_olmblur_worker32_nonlegacy \
  tools/emulation/fixtures/olmblur_worker32_nonlegacy
```

Result: `PASS` for all seven complete AEX fixtures, with byte-exact source
and expected-output replay.

This is portable core plus actual-AEX CPU-fixture evidence, not an AE-host
conformance claim. No Mac, ledger, or NAS files were changed.
