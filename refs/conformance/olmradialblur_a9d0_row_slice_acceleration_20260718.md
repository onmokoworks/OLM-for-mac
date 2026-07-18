# OLMRadialBlur A9D0 row-slice acceleration harness (2026-07-18)

- Status: `blocked_fail_closed_checkpoint_not_safe_for_a9d0_replay`
- Protected PID: `59481`; stopped: `False`
- A9D0 invoked: `False`
- Derived checkpoint emitted: `False`

## FACT

- Source checkpoint: `/private/tmp/olm_radial_case0009_workers_progress6_20260718.aexcp`
- Source SHA-256: `e79e1972df097588a12af17d5510be6104f02ec98cc4ce139af96634bb3520cc`
- Immutable copy: `/tmp/olmradialblur_a9d0_row_slice_20260718/natural_checkpoint6_copy.aexcp`
- Copy SHA-256: `e79e1972df097588a12af17d5510be6104f02ec98cc4ce139af96634bb3520cc`
- Source unchanged after copy: `True`
- Checkpoint RIP: `0x18000af9a`
- The current checkpoint is not an A9D0 entry state, so no AEX worker was resumed.

## Gates

| Gate | Result |
| --- | --- |
| `checkpoint_copy_hash_equal` | `True` |
| `source_unchanged_after_copy` | `True` |
| `protected_pid_alive_before` | `True` |
| `protected_pid_alive_after` | `True` |
| `protected_pid_state_unchanged` | `True` |
| `checkpoint_format` | `True` |
| `aex_identity_pinned` | `True` |
| `natural_harness` | `True` |
| `no_direct_core` | `True` |
| `no_prefill_detour` | `True` |
| `no_worker_detour` | `True` |
| `a9d0_entry_or_callsite` | `False` |
| `caller_state_available` | `False` |
| `pointer_non_alias_proven` | `False` |
| `complete_partition_proven` | `False` |
| `two_phase_provenance_present` | `False` |
| `post_a9d0_return_contract` | `False` |

## Rejection

- checkpoint RIP 0x18000af9a is inside/after A9D0, not an A9D0 entry (required 0x18000a9d0 or caller callsite 0x180005c90)
- pointer non-alias cannot be proven from the supplied checkpoint
- complete row partition cannot be derived from a mid-worker checkpoint
- two-phase B150->A9D0 provenance is absent from the checkpoint
- post-return normalization continuation cannot be reconstructed without guessing

## Required future proof

- Load independent copies of a genuine A9D0-entry checkpoint.
- Invoke the real AEX A9D0 with disjoint row ranges in separate loaders.
- Prove pointer non-alias and a complete half-open partition.
- Prove B150-all -> join -> A9D0-all -> join provenance.
- Compare two-slice output with a serial bounded A9D0 replay byte-for-byte.
- Emit a checkpoint whose RIP is the proven normalization path `0x180005c9f`.

No Windows/AE exactness claim is made by this fail-closed result.
