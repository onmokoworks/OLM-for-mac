b150 push rbx
b152 push rsi
b153 push rdi
b154 push r12
b156 push r13
b158 sub rsp, 0x50
b15c mov esi, dword ptr [rsp + 0xa0]
b163 mov rbx, rcx
b166 mov ecx, dword ptr [rsp + 0xb0]
b16d mov r10d, esi
b170 imul r10d, ecx
b174 mov dword ptr [rsp + 0xb0], ecx
b17b lea eax, [r10*4]
b183 movsxd r11, eax
b186 mov rax, qword ptr [rsp + 0xc0]
b18e lea rdi, [rdx + r11*4]
b192 movsxd rdx, r10d
b195 lea r13, [r8 + rdx*4]
b199 lea r8, [r9 + rdx*4]
b19d lea r9, [rax + r11*4]
b1a1 mov rax, qword ptr [rsp + 0xc8]
b1a9 lea r12, [rax + rdx*4]
b1ad mov eax, dword ptr [rsp + 0xb8]
b1b4 cmp ecx, eax
b1b6 jg 0x18000b61a
b1bc mov edx, dword ptr [rsp + 0xa8]
b1c3 xor r10d, r10d
b1c6 mov qword ptr [rsp + 0x80], rbp
b1ce mov qword ptr [rsp + 0x88], r14
b1d6 mov qword ptr [rsp + 0x90], r15
b1de movaps xmmword ptr [rsp + 0x40], xmm6
b1e3 xorps xmm6, xmm6
b1e6 movaps xmmword ptr [rsp + 0x30], xmm7
b1eb movaps xmmword ptr [rsp + 0x20], xmm8
b1f1 movaps xmmword ptr [rsp + 0x10], xmm9
b1f7 movaps xmmword ptr [rsp], xmm10
b1fc movss xmm10, dword ptr [rip + 0x160cf]
b205 cmp ecx, edx
b207 jge 0x18000b5e7
b20d mov rdx, rdi
b210 mov ebp, r10d
b213 mov qword ptr [rsp + 0xc0], rdx
b21b test esi, esi
b21d jle 0x18000b5cf
b223 mov ecx, r10d
b226 mov r15d, r10d
b229 mov r14d, esi
b22c jmp 0x18000b238
b22e nop
b230 mov rdx, qword ptr [rsp + 0xc0]
b238 movss xmm2, dword ptr [rdi + 0xc]
b23d movss xmm7, dword ptr [rdi]
b241 movss xmm8, dword ptr [rdi + 4]
b247 movss xmm9, dword ptr [rdi + 8]
b24d add rdi, 0x10
b251 movss xmm5, dword ptr [r8]
b256 add r8, 4
b25a ucomiss xmm2, xmm6
b25d mov qword ptr [rsp + 0xc8], r8
b265 je 0x18000b57d
b26b ucomiss xmm5, xmm6
b26e je 0x18000b57d
b274 movd xmm0, dword ptr [rbx + 0x4200]
b27c mov r10d, ecx
b27f cvtdq2ps xmm0, xmm0
b282 movaps xmm4, xmm10
b286 movaps xmm3, xmm10
b28a mulss xmm0, xmm5
b28e divss xmm4, xmm5
b292 cvttss2si eax, xmm0
b296 cmp eax, ecx
b298 cmovl r10d, eax
b29c lea eax, [rcx*4]
b2a3 movsxd r8, eax
b2a6 dec r8
b2a9 lea r8, [rdx + r8*4]
b2ad mov edx, 1
b2b2 cmp r10d, edx
b2b5 jle 0x18000b3d3
b2bb cmp r10d, 4
b2bf jle 0x18000b3a0
b2c5 lea esi, [r10 - 3]
b2c9 lea r11d, [rdx + 2]
b2cd nop dword ptr [rax]
b2d0 xorps xmm0, xmm0
b2d3 cvtsi2ss xmm0, edx
b2d7 add edx, 4
b2da mulss xmm0, xmm4
b2de cvttss2si eax, xmm0
b2e2 xorps xmm0, xmm0
b2e5 movsxd rcx, eax
b2e8 lea eax, [r11 - 1]
b2ec cvtsi2ss xmm0, eax
b2f0 movss xmm1, dword ptr [rbx + rcx*4 + 0x3ee0]
b2f9 addss xmm3, xmm1
b2fd mulss xmm0, xmm4
b301 mulss xmm1, dword ptr [r8]
b306 cvttss2si eax, xmm0
b30a addss xmm2, xmm1
b30e xorps xmm0, xmm0
b311 cvtsi2ss xmm0, r11d
b316 movsxd rcx, eax
b319 movss xmm1, dword ptr [rbx + rcx*4 + 0x3ee0]
b322 addss xmm3, xmm1
b326 mulss xmm0, xmm4
b32a mulss xmm1, dword ptr [r8 - 0x10]
b330 cvttss2si eax, xmm0
b334 addss xmm2, xmm1
b338 xorps xmm0, xmm0
b33b movsxd rcx, eax
b33e lea eax, [r11 + 1]
b342 cvtsi2ss xmm0, eax
b346 add r11d, 4
b34a movss xmm1, dword ptr [rbx + rcx*4 + 0x3ee0]
b353 addss xmm3, xmm1
b357 mulss xmm0, xmm4
b35b mulss xmm1, dword ptr [r8 - 0x20]
b361 cvttss2si eax, xmm0
b365 addss xmm2, xmm1
b369 movsxd rcx, eax
b36c movss xmm1, dword ptr [rbx + rcx*4 + 0x3ee0]
b375 addss xmm3, xmm1
b379 mulss xmm1, dword ptr [r8 - 0x30]
b37f sub r8, 0x40
b383 addss xmm2, xmm1
b387 cmp edx, esi
b389 jl 0x18000b2d0
b38f cmp edx, r10d
b392 jge 0x18000b3d3
b394 nop dword ptr [rax]
b398 nop dword ptr [rax + rax]
b3a0 movd xmm0, edx
b3a4 inc edx
b3a6 cvtdq2ps xmm0, xmm0
b3a9 mulss xmm0, xmm4
b3ad cvttss2si eax, xmm0
b3b1 movsxd rcx, eax
b3b4 movss xmm1, dword ptr [rbx + rcx*4 + 0x3ee0]
b3bd addss xmm3, xmm1
b3c1 mulss xmm1, dword ptr [r8]
b3c6 sub r8, 0x10
b3ca addss xmm2, xmm1
b3ce cmp edx, r10d
b3d1 jl 0x18000b3a0
b3d3 movd xmm0, dword ptr [rbx + 0x4204]
b3db mov r10d, r14d
b3de mov rcx, qword ptr [rsp + 0xc0]
b3e6 mov edx, 1
b3eb cvtdq2ps xmm0, xmm0
b3ee movsxd r8, r15d
b3f1 mulss xmm0, xmm5
b3f5 cvttss2si eax, xmm0
b3f9 cmp eax, r14d
b3fc cmovl r10d, eax
b400 add rcx, 0x1c
b404 lea r8, [rcx + r8*4]
b408 cmp r10d, edx
b40b jle 0x18000b533
b411 cmp r10d, 4
b415 jle 0x18000b500
b41b lea esi, [r10 - 3]
b41f lea r11d, [rdx + 2]
b423 nop dword ptr [rax]
b427 nop word ptr [rax + rax]
b430 xorps xmm0, xmm0
b433 cvtsi2ss xmm0, edx
b437 add edx, 4
b43a mulss xmm0, xmm4
b43e cvttss2si eax, xmm0
b442 xorps xmm0, xmm0
b445 movsxd rcx, eax
b448 lea eax, [r11 - 1]
b44c cvtsi2ss xmm0, eax
b450 movss xmm1, dword ptr [rbx + rcx*4 + 0x4070]
b459 addss xmm3, xmm1
b45d mulss xmm0, xmm4
b461 mulss xmm1, dword ptr [r8]
b466 cvttss2si eax, xmm0
b46a addss xmm2, xmm1
b46e xorps xmm0, xmm0
b471 cvtsi2ss xmm0, r11d
b476 movsxd rcx, eax
b479 movss xmm1, dword ptr [rbx + rcx*4 + 0x4070]
b482 addss xmm3, xmm1
b486 mulss xmm0, xmm4
b48a mulss xmm1, dword ptr [r8 + 0x10]
b490 cvttss2si eax, xmm0
b494 addss xmm2, xmm1
b498 xorps xmm0, xmm0
b49b movsxd rcx, eax
b49e lea eax, [r11 + 1]
b4a2 cvtsi2ss xmm0, eax
b4a6 add r11d, 4
b4aa movss xmm1, dword ptr [rbx + rcx*4 + 0x4070]
b4b3 addss xmm3, xmm1
b4b7 mulss xmm0, xmm4
b4bb mulss xmm1, dword ptr [r8 + 0x20]
b4c1 cvttss2si eax, xmm0
b4c5 addss xmm2, xmm1
b4c9 movsxd rcx, eax
b4cc movss xmm1, dword ptr [rbx + rcx*4 + 0x4070]
b4d5 addss xmm3, xmm1
b4d9 mulss xmm1, dword ptr [r8 + 0x30]
b4df add r8, 0x40
b4e3 addss xmm2, xmm1
b4e7 cmp edx, esi
b4e9 jl 0x18000b430
b4ef cmp edx, r10d
b4f2 jge 0x18000b533
b4f4 nop dword ptr [rax]
b4f8 nop dword ptr [rax + rax]
b500 movd xmm0, edx
b504 inc edx
b506 cvtdq2ps xmm0, xmm0
b509 mulss xmm0, xmm4
b50d cvttss2si eax, xmm0
b511 movsxd rcx, eax
b514 movss xmm1, dword ptr [rbx + rcx*4 + 0x4070]
b51d addss xmm3, xmm1
b521 mulss xmm1, dword ptr [r8]
b526 add r8, 0x10
b52a addss xmm2, xmm1
b52e cmp edx, r10d
b531 jl 0x18000b500
b533 mov r8, qword ptr [rsp + 0xc8]
b53b mov esi, dword ptr [rsp + 0xa0]
b542 divss xmm2, xmm3
b546 movaps xmm0, xmm2
b549 movaps xmm1, xmm2
b54c mulss xmm0, xmm7
b550 mulss xmm1, xmm8
b555 movss dword ptr [r9], xmm0
b55a movaps xmm0, xmm2
b55d mulss xmm0, xmm9
b562 movss dword ptr [r9 + 4], xmm1
b568 movss dword ptr [r9 + 0xc], xmm2
b56e movss dword ptr [r9 + 8], xmm0
b574 add r9, 0x10
b578 xor r10d, r10d
b57b jmp 0x18000b593
b57d mov qword ptr [r9], 0
b584 movaps xmm2, xmm6
b587 mov qword ptr [r9 + 8], 0
b58f add r9, 0x10
b593 inc ebp
b595 movss dword ptr [r12], xmm2
b59b dec r14d
b59e movss dword ptr [r13], xmm2
b5a4 add r15d, 4
b5a8 lea rax, [r12 + 4]
