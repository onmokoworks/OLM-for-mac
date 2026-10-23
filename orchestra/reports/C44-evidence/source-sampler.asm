0x180001520 mov qword ptr [rsp + 8], rbx
0x180001525 mov qword ptr [rsp + 0x10], rbp
0x18000152a mov qword ptr [rsp + 0x18], rsi
0x18000152f mov dword ptr [rsp + 0x20], r9d
0x180001534 push rdi
0x180001535 push r12
0x180001537 push r13
0x180001539 push r14
0x18000153b push r15
0x18000153d sub rsp, 0x20
0x180001541 movss xmm5, dword ptr [rsp + 0x78]
0x180001547 lea ebx, [r9 - 1]
0x18000154b xor esi, esi
0x18000154d movaps xmmword ptr [rsp + 0x10], xmm6
0x180001552 movss xmm6, dword ptr [rip + 0x1fd7a]
0x18000155a mov r14, rdx
0x18000155d mov qword ptr [rdx + 8], rsi
0x180001561 mov rdi, rcx
0x180001564 mov qword ptr [rdx], rsi
0x180001567 mov r10d, r8d
0x18000156a cvttss2si r8d, xmm5
0x18000156f mov eax, esi
0x180001571 mov ecx, esi
0x180001573 mov r12d, esi
0x180001576 movaps xmmword ptr [rsp], xmm7
0x18000157a movaps xmm4, xmm6
0x18000157d movss xmm7, dword ptr [rsp + 0x80]
0x180001586 cmp r8d, -2
0x18000158a cvttss2si r13d, xmm7
0x18000158f setg al
0x180001592 mov edx, r8d
0x180001595 cmp r8d, r10d
0x180001598 lea r9d, [r8 + 1]
0x18000159c cmovl ecx, eax
0x18000159f lea eax, [r10 - 1]
0x1800015a3 movd xmm0, r8d
0x1800015a8 movaps xmm3, xmm6
0x1800015ab cmp r13d, -2
0x1800015af cvtdq2ps xmm0, xmm0
0x1800015b2 cmovg r12d, ecx
0x1800015b6 cmp eax, r8d
0x1800015b9 mov ecx, r13d
0x1800015bc cmovl edx, eax
0x1800015bf cmp eax, r9d
0x1800015c2 cmovl r9d, eax
0x1800015c6 movd xmm1, r13d
0x1800015cb subss xmm5, xmm0
0x1800015cf cmp ebx, r13d
0x1800015d2 cvtdq2ps xmm1, xmm1
0x1800015d5 cmovl ecx, ebx
0x1800015d8 mov eax, esi
0x1800015da test ecx, ecx
0x1800015dc cmovg eax, ecx
0x1800015df imul eax, dword ptr [rsp + 0x70]
0x1800015e4 subss xmm4, xmm5
0x1800015e8 subss xmm7, xmm1
0x1800015ec test edx, edx
0x1800015ee movsxd r8, eax
0x1800015f1 movaps xmm2, xmm4
0x1800015f4 mov eax, esi
0x1800015f6 subss xmm3, xmm7
0x1800015fa cmovg eax, edx
0x1800015fd shl eax, 2
0x180001600 movsxd r10, eax
0x180001603 lea rax, [r8 + 3]
0x180001607 add rax, r10
0x18000160a lea rcx, [rdi + rax*4]
0x18000160e mulss xmm2, xmm3
0x180001612 test r9d, r9d
0x180001615 mov eax, esi
0x180001617 cmovg eax, r9d
0x18000161b mulss xmm2, dword ptr [rcx]
0x18000161f shl eax, 2
0x180001622 movsxd r9, eax
0x180001625 lea rax, [r8 + 3]
0x180001629 add rax, r9
0x18000162c movaps xmm0, xmm2
0x18000162f movaps xmm1, xmm2
0x180001632 addss xmm0, dword ptr [r14 + 0xc]
0x180001638 movss dword ptr [r14 + 0xc], xmm0
0x18000163e movaps xmm0, xmm2
0x180001641 mulss xmm1, dword ptr [rcx - 4]
0x180001646 addss xmm1, dword ptr [r14 + 8]
0x18000164c movss dword ptr [r14 + 8], xmm1
0x180001652 mulss xmm0, dword ptr [rcx - 8]
0x180001657 addss xmm0, dword ptr [r14 + 4]
0x18000165d movss dword ptr [r14 + 4], xmm0
0x180001663 mulss xmm2, dword ptr [rcx - 0xc]
0x180001668 lea rcx, [rdi + rax*4]
0x18000166c addss xmm2, dword ptr [r14]
0x180001671 movss dword ptr [r14], xmm2
0x180001676 mulss xmm4, xmm7
0x18000167a mov eax, esi
0x18000167c mulss xmm3, xmm5
0x180001680 mulss xmm7, xmm5
0x180001684 mulss xmm3, dword ptr [rcx]
0x180001688 movaps xmm0, xmm3
0x18000168b movaps xmm1, xmm3
0x18000168e addss xmm0, dword ptr [r14 + 0xc]
0x180001694 movss dword ptr [r14 + 0xc], xmm0
0x18000169a movaps xmm0, xmm3
0x18000169d mulss xmm1, dword ptr [rcx - 4]
0x1800016a2 addss xmm1, dword ptr [r14 + 8]
0x1800016a8 movss dword ptr [r14 + 8], xmm1
0x1800016ae mulss xmm0, dword ptr [rcx - 8]
0x1800016b3 addss xmm0, dword ptr [r14 + 4]
0x1800016b9 movss dword ptr [r14 + 4], xmm0
0x1800016bf mulss xmm3, dword ptr [rcx - 0xc]
0x1800016c4 lea ecx, [r13 + 1]
0x1800016c8 cmp ebx, ecx
0x1800016ca cmovl ecx, ebx
0x1800016cd addss xmm3, dword ptr [r14]
0x1800016d2 test ecx, ecx
0x1800016d4 cmovg eax, ecx
0x1800016d7 imul eax, dword ptr [rsp + 0x70]
0x1800016dc movss dword ptr [r14], xmm3
0x1800016e1 movsxd rdx, eax
0x1800016e4 lea rax, [r10 + 3]
0x1800016e8 add rax, rdx
0x1800016eb mulss xmm4, dword ptr [rdi + rax*4]
0x1800016f0 lea rcx, [rdi + rax*4]
0x1800016f4 lea rax, [r9 + 3]
0x1800016f8 add rax, rdx
0x1800016fb movaps xmm0, xmm4
0x1800016fe movaps xmm1, xmm4
0x180001701 addss xmm0, dword ptr [r14 + 0xc]
0x180001707 movss dword ptr [r14 + 0xc], xmm0
0x18000170d movaps xmm0, xmm4
0x180001710 mulss xmm1, dword ptr [rcx - 4]
0x180001715 addss xmm1, dword ptr [r14 + 8]
0x18000171b movss dword ptr [r14 + 8], xmm1
0x180001721 mulss xmm0, dword ptr [rcx - 8]
0x180001726 addss xmm0, dword ptr [r14 + 4]
0x18000172c movss dword ptr [r14 + 4], xmm0
0x180001732 mulss xmm4, dword ptr [rcx - 0xc]
0x180001737 lea rcx, [rdi + rax*4]
0x18000173b addss xmm4, dword ptr [r14]
0x180001740 movss dword ptr [r14], xmm4
0x180001745 mulss xmm7, dword ptr [rcx]
0x180001749 movaps xmm0, xmm7
0x18000174c movaps xmm1, xmm7
0x18000174f addss xmm0, dword ptr [r14 + 0xc]
0x180001755 movaps xmm2, xmm7
0x180001758 movss dword ptr [r14 + 0xc], xmm0
0x18000175e xorps xmm0, xmm0
0x180001761 mulss xmm1, dword ptr [rcx - 4]
0x180001766 addss xmm1, dword ptr [r14 + 8]
0x18000176c movss dword ptr [r14 + 8], xmm1
0x180001772 mulss xmm2, dword ptr [rcx - 8]
0x180001777 addss xmm2, dword ptr [r14 + 4]
0x18000177d movss dword ptr [r14 + 4], xmm2
0x180001783 mulss xmm7, dword ptr [rcx - 0xc]
0x180001788 addss xmm7, dword ptr [r14]
0x18000178d movss dword ptr [r14], xmm7
0x180001792 movss xmm1, dword ptr [r14 + 0xc]
0x180001798 ucomiss xmm1, xmm0
0x18000179b jne 0x1800017a1
0x18000179d xor eax, eax
0x18000179f jmp 0x1800017cf
0x1800017a1 cmp r13d, dword ptr [rsp + 0x68]
0x1800017a6 divss xmm6, xmm1
0x1800017aa cmovl esi, r12d
0x1800017ae mov eax, esi
0x1800017b0 mulss xmm7, xmm6
0x1800017b4 mulss xmm2, xmm6
0x1800017b8 movss dword ptr [r14], xmm7
0x1800017bd movss dword ptr [r14 + 4], xmm2
0x1800017c3 mulss xmm6, dword ptr [r14 + 8]
0x1800017c9 movss dword ptr [r14 + 8], xmm6
0x1800017cf mov rbx, qword ptr [rsp + 0x50]
0x1800017d4 mov rbp, qword ptr [rsp + 0x58]
0x1800017d9 mov rsi, qword ptr [rsp + 0x60]
0x1800017de movaps xmm6, xmmword ptr [rsp + 0x10]
0x1800017e3 movaps xmm7, xmmword ptr [rsp]
0x1800017e7 add rsp, 0x20
0x1800017eb pop r15
0x1800017ed pop r14
0x1800017ef pop r13
0x1800017f1 pop r12
0x1800017f3 pop rdi
0x1800017f4 ret 
0x1800017f5 int3 
0x1800017f6 int3 
0x1800017f7 int3 
0x1800017f8 int3 
0x1800017f9 int3 
0x1800017fa int3 
0x1800017fb int3 
0x1800017fc int3 
0x1800017fd int3 
0x1800017fe int3 
0x1800017ff int3 
0x180001800 push rbx
0x180001802 sub rsp, 0x10
0x180001806 movss xmm4, dword ptr [rsp + 0x40]
0x18000180c mov rbx, rcx
