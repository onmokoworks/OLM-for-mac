# OLMBlur full-entry host-layout probe

Date: 2026-07-10

## FACT

- New harness: `tools/emulation/test_olmblur_fullentry.py`.
- Target: `plugins_2025/OLMBlur.aex`, `FUN_180005f20`.
- The harness uses only offsets observed in `decomp/OLMBlur.aex.c.txt` and
  `disasm/OLMBlur.aex.asm.txt`: context `+0x11c/+0x120/+0x180`, parameter
  `+0x18/+0x20/+0x24/+0x2c`, and world `+0x18/+0x20/+0x24/+0x28/+0x2c`.
- PF Handle Suite callbacks are reused structurally from the existing
  `test_dg_fieldgen_p1b.py` and `test_dblur_case0001_rowdriver.py` probes.
- The synthetic source and output worlds are 8x2, 16bpc, four unsigned-short
  channels with rowbytes `width * 8`.

## Command and observed output

Command:

```text
python3 tools/emulation/test_olmblur_fullentry.py
```

The command output is recorded below after the focused run. It is a local
Unicorn/mock-host observation only; it does not claim AE exactness.

```text
FACT entry 0x180005f20
FACT grounded_context_offsets {'scale_num': '0x11c', 'scale_den': '0x120', 'spbasic': '0x180'}
FACT grounded_param_offsets {'bit_depth': '0x18', 'radius': '0x20', 'strength': '0x24', 'mode': '0x2c'}
FACT grounded_world_offsets {'data': '0x18', 'rowbytes': '0x20', 'width': '0x24', 'height': '0x28', 'bit_depth': '0x2c'}
FACT status return
FACT error None
FACT result_rax 0x0
FACT callbacks [('AcquireSuite', 2), ('new', 192), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('new', 192), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('new', 12), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('new', 16), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('lock', 1073742704), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('lock', 1073742720), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('lock', 1073742736), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('lock', 1073742752), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('unlock', 1073742720), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('unlock', 1073742704), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('unlock', 1073742736), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('unlock', 1073742752), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('dispose', 1073742720), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('dispose', 1073742704), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('dispose', 1073742736), ('ReleaseSuite', 0), ('AcquireSuite', 2), ('dispose', 1073742752), ('ReleaseSuite', 0)]
FACT code_hits [('entry', '0x180005f20')]
FACT output_head_hex 00006400c8002c0100006500c8002d0100006600c8002e0100006700c8002f01
INFERENCE final_store_reached True
INFERENCE scope: mocked host structs and synthetic 16bpc worlds are layout probes, not AE-exact output evidence
```

## INFERENCE

The full entry returns, the PF Handle lifecycle completes, and the mocked
output-world changes from all zero. The narrowest remaining limitation is
provenance: the run uses synthetic worlds and host callbacks, so it demonstrates
full-entry execution and a final 16bpc store under this layout, not AE-exact
render values or PNG equivalence. The only code hook observed was the entry
itself; the callback trace confirms four temporary allocations and their
complete lock/unlock/dispose lifecycle.

## Changed files

- `tools/emulation/test_olmblur_fullentry.py`
- `refs/conformance/olmblur_fullentry_host_layout_probe_20260710.md`
