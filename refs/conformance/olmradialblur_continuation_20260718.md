# OLMRadialBlur continuation probe (2026-07-18)

- Status: `pass_internal_continuation_only`
- Scope: natural AEX Unicorn continuation and internal PF32 plane capture.
- No AE-exact or Windows-exact claim is made.

## Gates

- `aex_hash_validated`: `True`
- `checkpoint_metadata_validated`: `True`
- `geometry_validated`: `True`
- `three_sequential_stops_reached`: `True`
- `normal_return`: `True`
- `checkpoint_unchanged`: `True`

## Sequential stops

- `normalized_polar_plane` at `0x180005d96`; instructions `51685211`
  - `normalized_polar_plane`: `31795200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
  - `pf32_output_frame`: `33177600` bytes, `33c9aff6d23026135eadf5cd36f5784220bf77c05ed774e7c186a0f812ba0c7b`
- `complete_pf32_frame` at `0x180005e8e`; instructions `406445046`
  - `normalized_polar_plane`: `31795200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
  - `pf32_output_frame`: `33177600` bytes, `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
- `pre_return` at `0x1800063a1`; instructions `388`
  - `normalized_polar_plane`: `31795200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
  - `pf32_output_frame`: `33177600` bytes, `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`

- Normal return: `0x90000000`

## Fact / inference

- FACT: The continuation resumes a natural AEX checkpoint under Unicorn.
- FACT: The reported planes are internal PF32 memory, not host-rendered output.
- INFERENCE: A matching internal plane is evidence about the AEX path, not proof of Mac AE equivalence.
