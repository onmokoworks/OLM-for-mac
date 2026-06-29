# OLMBlur 16bpc ASM Writer Audit - 2026-06-29

## Summary

This audit extracts the relevant writer windows from
`disasm/OLMBlur.aex.asm.txt` so the 16bpc residual discussion is tied
to reproducible binary evidence rather than a hand-copied note.

## Writer Windows

| Window | Classification | 0.5 loads | ADDSS | helper calls | CVTTSS2SI XMM0 | CVTTSS2SI memory | word stores | byte stores |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `standard_16bpc_word_writer` | `round-add-helper-truncate-word-store` | 1 | 3 | 3 | 3 | 0 | 3 | 0 |
| `alternate_16bpc_direct_word_writer` | `direct-memory-truncate-word-store` | 0 | 0 | 0 | 0 | 6 | 6 | 0 |
| `legacy_8bpc_byte_writer_family` | `round-add-helper-truncate-byte-store` | 1 | 3 | 3 | 3 | 0 | 0 | 3 |

## Interpretation

- The standard 16bpc word writer adds the 0.5 constant, calls helper 0x18000ccb4, truncates with CVTTSS2SI, then stores 16-bit channel words.
- The nearby alternate 16bpc word writer branches to a direct memory CVTTSS2SI word-store family, so Legacy/edge witnesses must keep writer family separate from the standard path.
- The known 8bpc legacy byte writer at 0x180007fdf is a byte-store analogue of the round-add-helper path and should not be confused with the 16bpc word-store family.

## Excerpts

### standard_16bpc_word_writer

```asm
180002fad  MOVSS XMM6,dword ptr [0x18000d24c]
180002fb5  MOV RCX,qword ptr [RSP + 0x58]
180002fba  MOV EDX,dword ptr [RSP + 0x50]
180002fbe  NOP
180002fc0  XOR ESI,ESI
180002fc2  TEST R13D,R13D
180002fc5  JLE 0x18000304f
180002fcb  XOR R15D,R15D
180002fce  MOV RDI,RAX
180002fd1  XOR EBX,EBX
180002fd3  CMP ESI,dword ptr [R14 + 0x24]
180002fd7  JGE 0x180002ff1
180002fd9  CMP R12D,dword ptr [R14 + 0x28]
180002fdd  JGE 0x180002ff1
180002fdf  MOV EAX,R12D
180002fe2  IMUL EAX,dword ptr [R14 + 0x20]
180002fe7  MOVSXD RBX,EAX
180002fea  ADD RBX,qword ptr [R14 + 0x18]
180002fee  ADD RBX,R15
180002ff1  MOVSS XMM0,dword ptr [RDI + -0x8]
180002ff6  ADDSS XMM0,XMM6
180002ffa  CALL 0x18000ccb4
180002fff  CVTTSS2SI EAX,XMM0
180003003  MOV word ptr [RBX + 0x2],AX
180003007  MOVSS XMM0,dword ptr [RDI + -0x4]
18000300c  ADDSS XMM0,XMM6
180003010  CALL 0x18000ccb4
180003015  CVTTSS2SI EAX,XMM0
180003019  MOV word ptr [RBX + 0x4],AX
18000301d  MOVSS XMM0,dword ptr [RDI]
180003021  ADDSS XMM0,XMM6
180003025  CALL 0x18000ccb4
18000302a  CVTTSS2SI EAX,XMM0
18000302e  MOV word ptr [RBX + 0x6],AX
```

### alternate_16bpc_direct_word_writer

```asm
1800031d0  XOR ECX,ECX
1800031d2  TEST R8D,R8D
1800031d5  JS 0x1800031f9
1800031d7  CMP R8D,dword ptr [R14 + 0x24]
1800031db  JGE 0x1800031f9
1800031dd  CMP R9D,dword ptr [R14 + 0x28]
1800031e1  JGE 0x1800031f9
1800031e3  MOV EAX,R9D
1800031e6  IMUL EAX,dword ptr [R14 + 0x20]
1800031eb  MOVSXD RCX,EAX
1800031ee  ADD RCX,-0x10
1800031f2  ADD RCX,qword ptr [R14 + 0x18]
1800031f6  ADD RCX,R10
1800031f9  CVTTSS2SI EAX,dword ptr [RDX + -0x8]
1800031fe  MOV word ptr [RCX + 0x2],AX
180003202  CVTTSS2SI EAX,dword ptr [RDX + -0x4]
180003207  MOV word ptr [RCX + 0x4],AX
18000320b  CVTTSS2SI EAX,dword ptr [RDX]
18000320f  MOV word ptr [RCX + 0x6],AX
180003213  XOR ECX,ECX
180003215  LEA EAX,[R11 + -0x1]
180003219  TEST EAX,EAX
18000321b  JS 0x18000323f
18000321d  CMP EAX,dword ptr [R14 + 0x24]
180003221  JGE 0x18000323f
180003223  CMP R9D,dword ptr [R14 + 0x28]
180003227  JGE 0x18000323f
180003229  MOV EAX,R9D
18000322c  IMUL EAX,dword ptr [R14 + 0x20]
180003231  MOVSXD RCX,EAX
180003234  ADD RCX,-0x8
180003238  ADD RCX,qword ptr [R14 + 0x18]
18000323c  ADD RCX,R10
18000323f  CVTTSS2SI EAX,dword ptr [RDX + 0x4]
180003244  MOV word ptr [RCX + 0x2],AX
180003248  CVTTSS2SI EAX,dword ptr [RDX + 0x8]
18000324d  MOV word ptr [RCX + 0x4],AX
180003251  CVTTSS2SI EAX,dword ptr [RDX + 0xc]
180003256  MOV word ptr [RCX + 0x6],AX
```

### legacy_8bpc_byte_writer_family

```asm
180007f8c  MOVSS XMM6,dword ptr [0x18000d24c]
180007f94  MOV RCX,qword ptr [RSP + 0x70]
180007f99  MOV EDX,dword ptr [RSP + 0x60]
180007f9d  NOP dword ptr [RAX]
180007fa0  XOR ESI,ESI
180007fa2  TEST R13D,R13D
180007fa5  JLE 0x18000802c
180007fab  XOR R15D,R15D
180007fae  MOV RDI,RAX
180007fb1  XOR EBX,EBX
180007fb3  CMP ESI,dword ptr [R14 + 0x24]
180007fb7  JGE 0x180007fd1
180007fb9  CMP R12D,dword ptr [R14 + 0x28]
180007fbd  JGE 0x180007fd1
180007fbf  MOV EAX,R12D
180007fc2  IMUL EAX,dword ptr [R14 + 0x20]
180007fc7  MOVSXD RBX,EAX
180007fca  ADD RBX,qword ptr [R14 + 0x18]
180007fce  ADD RBX,R15
180007fd1  MOVSS XMM0,dword ptr [RDI + -0x8]
180007fd6  ADDSS XMM0,XMM6
180007fda  CALL 0x18000ccb4
180007fdf  CVTTSS2SI EAX,XMM0
180007fe3  MOV byte ptr [RBX + 0x1],AL
180007fe6  MOVSS XMM0,dword ptr [RDI + -0x4]
180007feb  ADDSS XMM0,XMM6
180007fef  CALL 0x18000ccb4
180007ff4  CVTTSS2SI EAX,XMM0
180007ff8  MOV byte ptr [RBX + 0x2],AL
180007ffb  MOVSS XMM0,dword ptr [RDI]
180007fff  ADDSS XMM0,XMM6
180008003  CALL 0x18000ccb4
180008008  CVTTSS2SI EAX,XMM0
18000800c  MOV byte ptr [RBX + 0x3],AL
```
