# OLMColorKey 16bpc current-AEX follow-up audit

- Return zip: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/returns/olm_runtime_trace_colorkey_16bpc_case0009_current_aex_followup_20260627_return_windows_20260628_1338.zip`
- Raw status: `answered_partial_current_aex_positive_edge_thin`
- Trace file: `evidence\cdb_witness_1110_149\cdb_trace_88c8_2026-06-28_12-59-52-616.log`

## Witness `(1110,149)`

- Parsed coordinate: `(1110,149)`
- Distance: `2.0` (`0x40000000`)
- Copy path taken: `True`
- Matte before: `[0, 0, 0, 0]`
- Matte after: `[32768, 0, 0, 0]`

## Conclusion

- The returned JSON summary is stale for the primary witness, but the raw CDB log is actionable.
- The primary residual witness (1110,149) does hit the current-AEX +0x9237/+0x9247/+0x924c/+0x92b7 path.
- Windows consumes dist=2.0 at (1110,149), takes the copy path, and changes matte word0 from 0x0000 to 0x8000.
- This proves the primary residual is not merely outside the +0x9000 positive Edge Thin loop; at least this witness is removed by that loop.
- The local exported-PNG Lab76 seed model puts the same witness at taxicab distance 43 from the current hit set, so the remaining mismatch is now specifically the seed/matte world feeding current-AEX positive Edge Thin.
