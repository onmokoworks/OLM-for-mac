# OLMDirectionalBlur Writer Buffer Provenance Checkpoint

- Status: `pass`.
- Scope: natural Mac-local Unicorn angle-0 8bpc path, tracing writes to output `params+0x8090` before output Iterate8.
- Static AEX writes were enumerated at `0x180003f4b`, `0x18000489d`, `0x180004cdb`, `0x180005a66`, `0x18000636d`, and `0x18000562d`.
- The nearest natural producer is `FUN_180004A20`; its final-path write at `0x18000562d` stores `R15` into `0x8090(%RBX)` immediately before constructing the output callback and entering `FUN_180006700`.
- Dynamic memory tracing confirms the write lands at the output refcon's `params+0x8090` address before callback `0x180006b30`.
- The pointer's upstream allocation owner remains unresolved. No missing suite or ABI was fabricated, no Windows values were used, and no AE-exact claim is made.

Reproduction:

```sh
python3 tools/emulation/test_olmdirectionalblur_writer_buffer_provenance_20260717.py
```
