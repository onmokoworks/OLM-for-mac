# OLMKiraKira Mode 3 sigma sweep actual-AEX evidence

Date: 2026-07-13T02:12:39.777263Z

## FACT

- Each sweep point replays the actual AEX helper path separately and records the captured FUN_181272ec0 boundary rather than reusing a cached hit.
- The decomp callsite multiplies integer length by DAT_18148d670 before calling FUN_181272ec0.
- The disassembly callsite at 0x1811510d5 loads the same DAT_18148d670 qword into mulsd before the Gaussian wrapper call.
- The raw .rdata bytes at virtual address 0x18148d670 decode to IEEE-754 little-endian double 0.5.

## INFERENCE

- The size field is reported exactly as the captured low/high 32-bit unpack of R8 (0x100000000 -> [0, 1]); this report does not rename those words into semantic width/height beyond that raw decode.
- Agreement between observed sigmaX and length * 0.5 is evidence for the helper-side multiplier contract, not a claim about deeper OpenCV internals.
- If any point misses the Gaussian hook, that case remains in the report and weakens the sweep verdict instead of being silently dropped.

## Execution

- Status: `captured`
- AEX: `/Users/onmk/Documents/Projects/Personal/OLM as/aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex`
- AEX SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`
- Single probe: `/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/probe_olmkirakira_mode3_actual_aex.py`
- Single probe SHA-256: `5756f878ee7bfe7383a5b80afa6c1d0c27ad61cc9b41a78cb5c64b299430028c`
- Input: `{"blur_mode": 3, "height": 7, "lengths": [1, 2, 5, 9], "sigma_argument": 0.0, "type": "CV_32FC1", "width": 9}`

## DAT_18148d670 evidence

- Raw data: `{"f64": 0.5, "file_offset": "0x148c870", "image_base": "0x180000000", "next_f64": 1.0, "raw_hex_le_16": "000000000000e03f000000000000f03f", "raw_hex_le_8": "000000000000e03f", "rva": "0x148d670", "section": {"name": ".rdata", "raw_ptr": "0x1484200", "raw_size": "0x39c600", "virtual_address": "0x1485000", "virtual_size": "0x39c4c8"}, "virtual_address": "0x18148d670"}`
- Disasm command: `objdump -d -M intel --start-address=0x1811510c0 --stop-address=0x181151108 /Users/onmk/Documents/Projects/Personal/OLM as/aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex`

### Decomp callsite

```c
    local_218[0] = 0x1010000;
    local_230 = 4;
    local_238 = 0;
    local_210 = param_3;
    FUN_181272ec0(local_218,local_200,0x100000000,(double)(int)param_7 * DAT_18148d670);
  }
  else if (param_8 == 4) {
    iVar1 = param_7 + 1;
    fVar18 = (float)(int)param_7 / (float)iVar1;
```

### Decomp additional use

```c
  local_468 = local_458;
  local_560 = param_4;
  if (0x408 < local_460) {
    local_468 = (undefined1 *)thunk_FUN_18132b27c();
  }
  puVar3 = local_468;
  uVar2 = DAT_18148d670;
  local_5b8 = local_468;
  local_5b0 = local_468 + lVar14 * 4;
  puVar1 = local_5b0 + (longlong)param_8 * 4;
  local_550 = puVar1 + (longlong)(param_7 * 2) * 4;
  iVar11 = 0;
  if (0 < lVar14) {
```

### Disasm callsite

```asm
/Users/onmk/Documents/Projects/Personal/OLM as/aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex:	file format coff-x86-64
Disassembly of section .text:
0000000180001000 <.text>:
1811510c0: c7 44 24 40 00 00 01 01     	mov	dword ptr [rsp + 0x40], 0x1010000
1811510c8: 4c 89 74 24 48              	mov	qword ptr [rsp + 0x48], r14
1811510cd: 66 0f 6e de                 	movd	xmm3, esi
1811510d1: f3 0f e6 db                 	cvtdq2pd	xmm3, xmm3
1811510d5: f2 0f 59 1d 93 c5 33 00     	mulsd	xmm3, qword ptr [rip + 0x33c593] # 0x18148d670
1811510dd: 49 b8 00 00 00 00 01 00 00 00       	movabs	r8, 0x100000000
1811510e7: c7 44 24 28 04 00 00 00     	mov	dword ptr [rsp + 0x28], 0x4
1811510ef: f2 44 0f 11 44 24 20        	movsd	qword ptr [rsp + 0x20], xmm8
1811510f6: 48 8d 54 24 58              	lea	rdx, [rsp + 0x58]
1811510fb: 48 8d 4c 24 40              	lea	rcx, [rsp + 0x40]
181151100: e8 bb 1d 12 00              	call	0x181272ec0 <entry_point+0x11cfa0>
181151105: e9 33 fe ff ff              	jmp	0x181150f3d <.text+0x114ff3d>
```

## Sweep table

| Length | Status | Size | sigmaX | Expected sigmaX (= length * DAT) | Match | Instructions |
| --- | --- | --- | ---: | ---: | --- | ---: |
| 1 | captured | [0, 1] | 0.5 | 0.5 | True | 193071 |
| 2 | captured | [0, 1] | 1.0 | 1.0 | True | 192747 |
| 5 | captured | [0, 1] | 2.5 | 2.5 | True | 193053 |
| 9 | captured | [0, 1] | 4.5 | 4.5 | True | 193053 |

## Execution log

- `{"expected_sigma_x_f64": 0.5, "instructions": 193071, "length": 1, "sigma_x_f64": 0.5, "size": [0, 1], "status": "captured", "target_hit_count": 1}`
- `{"expected_sigma_x_f64": 1.0, "instructions": 192747, "length": 2, "sigma_x_f64": 1.0, "size": [0, 1], "status": "captured", "target_hit_count": 1}`
- `{"expected_sigma_x_f64": 2.5, "instructions": 193053, "length": 5, "sigma_x_f64": 2.5, "size": [0, 1], "status": "captured", "target_hit_count": 1}`
- `{"expected_sigma_x_f64": 4.5, "instructions": 193053, "length": 9, "sigma_x_f64": 4.5, "size": [0, 1], "status": "captured", "target_hit_count": 1}`

## Verdict

- `{"all_points_captured": true, "dat_18148d670_f64": 0.5, "length_count": 4, "observed_size_set": [[0, 1]], "sigma_matches_length_times_dat": true, "size_is_invariant": true}`
