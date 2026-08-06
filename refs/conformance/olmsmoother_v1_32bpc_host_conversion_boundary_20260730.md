# OLMSmoother v1 32bpc Host-Conversion Boundary — 2026-07-30

## Result

Standalone OLMSmoother v1 has no proven native PF32 callback lane. The retained
Windows AE 26.3 Software renders made in a 32bpc project are evidence of the
host-conversion/classic 8/16 lane, not evidence that the AEX received native
float pixels.

The strict raw-FLOAT EXR comparison classifies the ten Windows random cases as:

- effect-changing: `01`, `02`, `03`, `04`, `06`, `08`, `09`, `10`;
- exact pass-through: `05`, `07`.

Every pair is uncompressed FLOAT RGBA at `1920x1080`. The executable audit
reports the per-case mismatched-float count, maximum raw-u32 delta, dimensions,
and SHA-256 of both the effect and before-effects EXRs.

The audit pins and verifies the complete manifest, request, standalone
disassembly, Mac source, PiPL, and all 20 EXR SHA-256 values before accepting
their parsed contents. This makes unrelated drift, an injected dispatcher
branch, duplicate metadata, and payload-only EXR drift fail closed.

## Binary and Mac boundary

The pinned standalone disassembly's `FUN_1800096f0` dispatcher is a two-way
split: `FUN_180001400` for PF8 and `FUN_1800011e0` for PF16. It contains no
third PF32 branch.

The Mac source and PiPL both declare `out_flags2=0x08000000`. This is bit 27
(threaded rendering); bit 10 (Smart Render support) and bit 12 (Float Color
Aware) are both clear. Classic `Render` chooses only 8 or 16 via
`PF_WORLD_IS_DEEP`. Float iterate/pass-through callback source exists, but the
declared flags do not advertise the Smart/float path, so it is outside the
declared reachable host contract.

## Claim boundary

The changing Windows 32bpc outputs do not justify inventing a native-float
algorithm or asserting an exact numeric formula for AE's depth conversion.
A same-contract Mac AE effect/control capture and strict comparison are required
before making a Mac parity claim.

Run:

```sh
python3 scripts/audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730.py
python3 refs/scripts/smoke_audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730.py
python3 -m py_compile \
  scripts/audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730.py \
  refs/scripts/smoke_audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730.py
```

This audit is read-only with respect to AE, Windows, NAS, release ledgers, and
the retained reference artifacts. Its adversarial smoke uses real independent
copies for every mutation target (never symlinks or hardlinks), then verifies
before/after hashes for every authoritative audit input and all 20 EXRs.
