# OLMRadialBlur A9D0 boundary fork proof (2026-07-18)

- Status: `pass_boundary_fork_prepared`
- Protected PID interactions: `0`
- Original checkpoint unchanged: `True`

## Proven boundary

- RIP: `0x18000b0f9`
- Remaining rows: `[721, 1800)`
- Width / height: `1104 / 1800`
- Caller return: `0x180005c95`; final invocation: `1 / 1`

## Fail-closed gates

| Gate | Result |
| --- | --- |
| `source_copy_hash_identity` | `True` |
| `aex_identity` | `True` |
| `natural_undetoured_lineage` | `True` |
| `row_boundary_reached` | `True` |
| `pointer_identity` | `True` |
| `plane_non_alias` | `True` |
| `final_caller_invocation` | `True` |
| `half_open_complete_partition` | `True` |
| `left_plane_write_bounded` | `True` |
| `right_plane_write_bounded` | `True` |
| `bounded_serial_vs_two_slice_equal` | `True` |
| `normalization_continuation_preserved` | `True` |
| `protected_pid_untouched` | `True` |

## Fork

- `[721, 1260)`: `/tmp/olmradialblur_a9d0_boundary_fork_20260718/full_left_input_20260718.aexcp`
- `[1260, 1800)`: `/tmp/olmradialblur_a9d0_boundary_fork_20260718/full_right_input_20260718.aexcp`

The full slice checkpoints are prepared but not executed by default. Run both fresh-loader commands concurrently, stop at `0x180005c95`, merge only the two owned output planes, then resume the merged checkpoint through normalization at `0x180005c9f`.

No caller state was reconstructed: the preserved worker frame was advanced and range-adjusted in place.
No Windows/AE exactness claim is made; this is an actual-AEX Unicorn checkpoint proof.
