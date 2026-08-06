// Generated from olmsmoother_v1_edgewalker16_cfg_20260806.json; do not hand edit.
L_180009960:
  M.write64((R.rsp+0x10ull), R.rbx); goto L_180009965;
L_180009965:
  M.write64((R.rsp+0x18ull), R.rbp); goto L_18000996a;
L_18000996a:
  M.write64((R.rsp+0x20ull), R.rsi); goto L_18000996f;
L_18000996f:
  M.write64((R.rsp+0x8ull), R.rcx); goto L_180009974;
L_180009974:
  R.rsp-=8; M.write64(R.rsp,R.rdi); goto L_180009975;
L_180009975:
  R.rsp-=8; M.write64(R.rsp,R.r12); goto L_180009977;
L_180009977:
  R.rsp-=8; M.write64(R.rsp,R.r13); goto L_180009979;
L_180009979:
  R.rsp-=8; M.write64(R.rsp,R.r14); goto L_18000997b;
L_18000997b:
  R.rsp-=8; M.write64(R.rsp,R.r15); goto L_18000997d;
L_18000997d:
  R.r15=uint64_t(M.read64((R.rsp+0x58ull))); goto L_180009982;
L_180009982:
  R.r11=uint64_t((0x180009989-0x9989ull)); goto L_180009989;
L_180009989:
  R.r12=uint64_t(M.read64((R.rsp+0x60ull))); goto L_18000998e;
L_18000998e:
  T=(uint32_t(R.rbp)) ^ (uint32_t(R.rbp)); M.logicflags(T,32);
  R.rbp=uint32_t(T);
  goto L_180009990;
L_180009990:
  R.r14=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009995;
L_180009995:
  R.r10=uint64_t(int64_t(int32_t(uint32_t(R.rdx)))); goto L_180009998;
L_180009998:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.r9)))); goto L_18000999b;
L_18000999b:
  R.r9=uint64_t(((R.rax*4ull))); goto L_1800099a3;
L_1800099a3:
  R.rsi=uint32_t(M.read32((R.r9+R.r11+0xf0c8ull))); goto L_1800099ab;
L_1800099ab:
  R.rdi=uint32_t(M.read32((R.r9+R.r11+0xf0f0ull))); goto L_1800099b3;
L_1800099b3:
  T=M.addflags(uint32_t(R.rsi),uint32_t(R.r10),32); R.rsi=uint32_t(T); goto L_1800099b6;
L_1800099b6:
  M.write32((R.r15), uint32_t(R.r10)); goto L_1800099b9;
L_1800099b9:
  T=M.addflags(uint32_t(R.rdi),uint32_t(R.r8),32); R.rdi=uint32_t(T); goto L_1800099bc;
L_1800099bc:
  M.write32((R.r12), uint32_t(R.r8)); goto L_1800099c0;
L_1800099c0:
  R.r9=uint32_t(uint32_t(R.rbp)); goto L_1800099c3;
L_1800099c3:
  R.rdx=uint64_t(M.read64((R.rcx+0x18ull))); goto L_1800099c7;
L_1800099c7:
  T=(uint32_t(R.r10)) & (uint32_t(R.r10)); M.logicflags(T,32);
  goto L_1800099ca;
L_1800099ca:
  if (M.sf) goto L_1800099ed; goto L_1800099cc;
L_1800099cc:
  T=M.subflags(uint32_t(R.r10),M.read32((R.rdx+0x24ull)),32);
  goto L_1800099d0;
L_1800099d0:
  if (M.sf==M.of) goto L_1800099ed; goto L_1800099d2;
L_1800099d2:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_1800099d5;
L_1800099d5:
  if (M.sf) goto L_1800099ed; goto L_1800099d7;
L_1800099d7:
  T=M.subflags(uint32_t(R.r8),M.read32((R.rdx+0x28ull)),32);
  goto L_1800099db;
L_1800099db:
  if (M.sf==M.of) goto L_1800099ed; goto L_1800099dd;
L_1800099dd:
  R.r8=uint32_t(int64_t(int32_t(uint32_t(R.r8)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_1800099e2;
L_1800099e2:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.r8)))); goto L_1800099e5;
L_1800099e5:
  R.r9=uint64_t((R.rcx+(R.r10*8ull))); goto L_1800099e9;
L_1800099e9:
  T=M.addflags(R.r9,M.read64((R.rdx+0x18ull)),64); R.r9=uint64_t(T); goto L_1800099ed;
L_1800099ed:
  R.r10=uint64_t(R.rbp); goto L_1800099f0;
L_1800099f0:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_1800099f2;
L_1800099f2:
  if (M.sf) goto L_180009a16; goto L_1800099f4;
L_1800099f4:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.rdx+0x24ull)),32);
  goto L_1800099f7;
L_1800099f7:
  if (M.sf==M.of) goto L_180009a16; goto L_1800099f9;
L_1800099f9:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_1800099fb;
L_1800099fb:
  if (M.sf) goto L_180009a16; goto L_1800099fd;
L_1800099fd:
  T=M.subflags(uint32_t(R.rdi),M.read32((R.rdx+0x28ull)),32);
  goto L_180009a00;
L_180009a00:
  if (M.sf==M.of) goto L_180009a16; goto L_180009a02;
L_180009a02:
  R.rax=uint32_t(uint32_t(R.rdi)); goto L_180009a04;
L_180009a04:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180009a08;
L_180009a08:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180009a0b;
L_180009a0b:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rsi)))); goto L_180009a0e;
L_180009a0e:
  R.r10=uint64_t((R.rcx+(R.rax*8ull))); goto L_180009a12;
L_180009a12:
  T=M.addflags(R.r10,M.read64((R.rdx+0x18ull)),64); R.r10=uint64_t(T); goto L_180009a16;
L_180009a16:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x50ull))))); goto L_180009a1b;
L_180009a1b:
  R.rcx=uint32_t(M.read32((R.r11+(R.rax*4ull)+0xf0f0ull))); goto L_180009a23;
L_180009a23:
  R.r13=uint32_t(M.read32((R.r11+(R.rax*4ull)+0xf0c8ull))); goto L_180009a2b;
L_180009a2b:
  M.write32((R.rsp+0x68ull), uint32_t(R.rcx)); goto L_180009a2f;
L_180009a2f:
  T=(uint32_t(R.r14)) & (uint32_t(R.r14)); M.logicflags(T,32);
  goto L_180009a32;
L_180009a32:
  if (!M.zf) goto L_180009a98; goto L_180009a34;
L_180009a34:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009a37;
L_180009a37:
  R.rbx=(R.rbx&~0xffull)|(uint8_t(uint8_t(!M.zf))); goto L_180009a3a;
L_180009a3a:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009a3d;
L_180009a3d:
  R.r11=(R.r11&~0xffull)|(uint8_t(uint8_t(!M.zf))); goto L_180009a41;
L_180009a41:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009a44;
L_180009a44:
  if (M.zf) goto L_180009b33; goto L_180009a4a;
L_180009a4a:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009a4d;
L_180009a4d:
  if (M.zf) goto L_180009b33; goto L_180009a53;
L_180009a53:
  R.rax=uint32_t(M.read16((R.r10+0x2ull))); goto L_180009a58;
L_180009a58:
  T=M.subflags(M.read16((R.r9+0x2ull)),uint16_t(R.rax),16);
  goto L_180009a5d;
L_180009a5d:
  if (!M.zf) goto L_180009b33; goto L_180009a63;
L_180009a63:
  R.rax=uint32_t(M.read16((R.r10+0x6ull))); goto L_180009a68;
L_180009a68:
  T=M.subflags(M.read16((R.r9+0x6ull)),uint16_t(R.rax),16);
  goto L_180009a6d;
L_180009a6d:
  if (!M.zf) goto L_180009b33; goto L_180009a73;
L_180009a73:
  R.rax=uint32_t(M.read16((R.r10+0x4ull))); goto L_180009a78;
L_180009a78:
  T=M.subflags(M.read16((R.r9+0x4ull)),uint16_t(R.rax),16);
  goto L_180009a7d;
L_180009a7d:
  if (!M.zf) goto L_180009b33; goto L_180009a83;
L_180009a83:
  R.rax=uint32_t(M.read16((R.r10))); goto L_180009a87;
L_180009a87:
  T=M.subflags(M.read16((R.r9)),uint16_t(R.rax),16);
  goto L_180009a8b;
L_180009a8b:
  if (!M.zf) goto L_180009b33; goto L_180009a91;
L_180009a91:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009a93;
L_180009a93:
  goto L_180009b35;
L_180009a98:
  R.r8=uint32_t(uint32_t(R.r14)); goto L_180009a9b;
L_180009a9b:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009a9e;
L_180009a9e:
  if (M.zf) goto L_180009aac; goto L_180009aa0;
L_180009aa0:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180009aa4;
L_180009aa4:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_180009aa7;
L_180009aa7:
  R.rbx=(R.rbx&~0xffull)|(uint8_t(uint8_t(!M.sf))); goto L_180009aaa;
L_180009aaa:
  goto L_180009ab2;
L_180009aac:
  T=(uint8_t(R.rbx)) ^ (uint8_t(R.rbx)); M.logicflags(T,8);
  R.rbx=(R.rbx&~0xffull)|(uint8_t(T));
  goto L_180009aae;
L_180009aae:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180009ab2;
L_180009ab2:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009ab5;
L_180009ab5:
  if (M.zf) goto L_180009ac0; goto L_180009ab7;
L_180009ab7:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_180009aba;
L_180009aba:
  R.r11=(R.r11&~0xffull)|(uint8_t(uint8_t(!M.sf))); goto L_180009abe;
L_180009abe:
  goto L_180009ac3;
L_180009ac0:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_180009ac3;
L_180009ac3:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009ac6;
L_180009ac6:
  if (M.zf) goto L_180009b33; goto L_180009ac8;
L_180009ac8:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009acb;
L_180009acb:
  if (M.zf) goto L_180009b33; goto L_180009acd;
L_180009acd:
  R.rax=uint32_t(M.read16((R.r10+0x2ull))); goto L_180009ad2;
L_180009ad2:
  R.rcx=uint32_t(M.read16((R.r9+0x2ull))); goto L_180009ad7;
L_180009ad7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009ad9;
L_180009ad9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009adb;
L_180009adb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009adc;
L_180009adc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009ade;
L_180009ade:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009ae0;
L_180009ae0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180009ae3;
L_180009ae3:
  if (!M.zf&&(M.sf==M.of)) goto L_180009b2f; goto L_180009ae5;
L_180009ae5:
  R.rcx=uint32_t(M.read16((R.r10+0x6ull))); goto L_180009aea;
L_180009aea:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180009aef;
L_180009aef:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180009af1;
L_180009af1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009af2;
L_180009af2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009af4;
L_180009af4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009af6;
L_180009af6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180009af9;
L_180009af9:
  if (!M.zf&&(M.sf==M.of)) goto L_180009b2f; goto L_180009afb;
L_180009afb:
  R.rcx=uint32_t(M.read16((R.r10+0x4ull))); goto L_180009b00;
L_180009b00:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180009b05;
L_180009b05:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180009b07;
L_180009b07:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009b08;
L_180009b08:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009b0a;
L_180009b0a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009b0c;
L_180009b0c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180009b0f;
L_180009b0f:
  if (!M.zf&&(M.sf==M.of)) goto L_180009b2f; goto L_180009b11;
L_180009b11:
  R.rax=uint32_t(M.read16((R.r10))); goto L_180009b15;
L_180009b15:
  R.rcx=uint32_t(M.read16((R.r9))); goto L_180009b19;
L_180009b19:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009b1b;
L_180009b1b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009b1d;
L_180009b1d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009b1e;
L_180009b1e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009b20;
L_180009b20:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009b22;
L_180009b22:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180009b25;
L_180009b25:
  if (!M.zf&&(M.sf==M.of)) goto L_180009b2f; goto L_180009b27;
L_180009b27:
  R.rcx=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009b2b;
L_180009b2b:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009b2d;
L_180009b2d:
  goto L_180009b35;
L_180009b2f:
  R.rcx=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009b33;
L_180009b33:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180009b35;
L_180009b35:
  T=(uint8_t(R.rbx)) & (uint8_t(R.rbx)); M.logicflags(T,8);
  goto L_180009b37;
L_180009b37:
  if (M.zf) goto L_180009deb; goto L_180009b3d;
L_180009b3d:
  goto L_180009b40;
L_180009b40:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_180009b43;
L_180009b43:
  if (M.zf) goto L_180009de9; goto L_180009b49;
L_180009b49:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180009b4b;
L_180009b4b:
  if (!M.zf) goto L_180009de9; goto L_180009b51;
L_180009b51:
  T=M.addflags(M.read32((R.r15)),uint32_t(R.r13),32); M.write32((R.r15), T); goto L_180009b54;
L_180009b54:
  T=M.addflags(uint32_t(R.rdi),uint32_t(R.rcx),32); R.rdi=uint32_t(T); goto L_180009b56;
L_180009b56:
  T=M.addflags(M.read32((R.r12)),uint32_t(R.rcx),32); M.write32((R.r12), T); goto L_180009b5a;
L_180009b5a:
  T=M.addflags(uint32_t(R.rsi),uint32_t(R.r13),32); R.rsi=uint32_t(T); goto L_180009b5d;
L_180009b5d:
  R.rcx=uint64_t(M.read64((R.rsp+0x30ull))); goto L_180009b62;
L_180009b62:
  R.r8=uint64_t(R.rbp); goto L_180009b65;
L_180009b65:
  R.r11=uint64_t(int64_t(int32_t(M.read32((R.r15))))); goto L_180009b68;
L_180009b68:
  R.rax=uint32_t(M.read32((R.r12))); goto L_180009b6c;
L_180009b6c:
  R.rdx=uint64_t(M.read64((R.rcx+0x18ull))); goto L_180009b70;
L_180009b70:
  T=(uint32_t(R.r11)) & (uint32_t(R.r11)); M.logicflags(T,32);
  goto L_180009b73;
L_180009b73:
  if (M.sf) goto L_180009b93; goto L_180009b75;
L_180009b75:
  T=M.subflags(uint32_t(R.r11),M.read32((R.rdx+0x24ull)),32);
  goto L_180009b79;
L_180009b79:
  if (M.sf==M.of) goto L_180009b93; goto L_180009b7b;
L_180009b7b:
  T=(uint32_t(R.rax)) & (uint32_t(R.rax)); M.logicflags(T,32);
  goto L_180009b7d;
L_180009b7d:
  if (M.sf) goto L_180009b93; goto L_180009b7f;
L_180009b7f:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rdx+0x28ull)),32);
  goto L_180009b82;
L_180009b82:
  if (M.sf==M.of) goto L_180009b93; goto L_180009b84;
L_180009b84:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180009b88;
L_180009b88:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180009b8b;
L_180009b8b:
  R.r8=uint64_t((R.rcx+(R.r11*8ull))); goto L_180009b8f;
L_180009b8f:
  T=M.addflags(R.r8,M.read64((R.rdx+0x18ull)),64); R.r8=uint64_t(T); goto L_180009b93;
L_180009b93:
  R.rcx=uint64_t(R.rbp); goto L_180009b96;
L_180009b96:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_180009b98;
L_180009b98:
  if (M.sf) goto L_180009bbc; goto L_180009b9a;
L_180009b9a:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.rdx+0x24ull)),32);
  goto L_180009b9d;
L_180009b9d:
  if (M.sf==M.of) goto L_180009bbc; goto L_180009b9f;
L_180009b9f:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180009ba1;
L_180009ba1:
  if (M.sf) goto L_180009bbc; goto L_180009ba3;
L_180009ba3:
  T=M.subflags(uint32_t(R.rdi),M.read32((R.rdx+0x28ull)),32);
  goto L_180009ba6;
L_180009ba6:
  if (M.sf==M.of) goto L_180009bbc; goto L_180009ba8;
L_180009ba8:
  R.rax=uint32_t(uint32_t(R.rdi)); goto L_180009baa;
L_180009baa:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180009bae;
L_180009bae:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180009bb1;
L_180009bb1:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rsi)))); goto L_180009bb4;
L_180009bb4:
  R.rcx=uint64_t((R.rcx+(R.rax*8ull))); goto L_180009bb8;
L_180009bb8:
  T=M.addflags(R.rcx,M.read64((R.rdx+0x18ull)),64); R.rcx=uint64_t(T); goto L_180009bbc;
L_180009bbc:
  T=(uint32_t(R.r14)) & (uint32_t(R.r14)); M.logicflags(T,32);
  goto L_180009bbf;
L_180009bbf:
  if (!M.zf) goto L_180009c92; goto L_180009bc5;
L_180009bc5:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009bc8;
L_180009bc8:
  if (M.zf) goto L_180009c01; goto L_180009bca;
L_180009bca:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180009bcd;
L_180009bcd:
  if (M.zf) goto L_180009c01; goto L_180009bcf;
L_180009bcf:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180009bd4;
L_180009bd4:
  T=M.subflags(M.read16((R.r9+0x2ull)),uint16_t(R.rax),16);
  goto L_180009bd9;
L_180009bd9:
  if (!M.zf) goto L_180009c01; goto L_180009bdb;
L_180009bdb:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180009be0;
L_180009be0:
  T=M.subflags(M.read16((R.r9+0x6ull)),uint16_t(R.rax),16);
  goto L_180009be5;
L_180009be5:
  if (!M.zf) goto L_180009c01; goto L_180009be7;
L_180009be7:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180009bec;
L_180009bec:
  T=M.subflags(M.read16((R.r9+0x4ull)),uint16_t(R.rax),16);
  goto L_180009bf1;
L_180009bf1:
  if (!M.zf) goto L_180009c01; goto L_180009bf3;
L_180009bf3:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180009bf7;
L_180009bf7:
  T=M.subflags(M.read16((R.r9)),uint16_t(R.rax),16);
  goto L_180009bfb;
L_180009bfb:
  if (!M.zf) goto L_180009c01; goto L_180009bfd;
L_180009bfd:
  R.rbx=(R.rbx&~0xffull)|(uint8_t(1ull)); goto L_180009bff;
L_180009bff:
  goto L_180009c03;
L_180009c01:
  T=(uint8_t(R.rbx)) ^ (uint8_t(R.rbx)); M.logicflags(T,8);
  R.rbx=(R.rbx&~0xffull)|(uint8_t(T));
  goto L_180009c03;
L_180009c03:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009c06;
L_180009c06:
  if (M.zf) goto L_180009c3c; goto L_180009c08;
L_180009c08:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180009c0b;
L_180009c0b:
  if (M.zf) goto L_180009c3c; goto L_180009c0d;
L_180009c0d:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180009c11;
L_180009c11:
  T=M.subflags(M.read16((R.r10+0x2ull)),uint16_t(R.rax),16);
  goto L_180009c16;
L_180009c16:
  if (!M.zf) goto L_180009c3c; goto L_180009c18;
L_180009c18:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180009c1c;
L_180009c1c:
  T=M.subflags(M.read16((R.r10+0x6ull)),uint16_t(R.rax),16);
  goto L_180009c21;
L_180009c21:
  if (!M.zf) goto L_180009c3c; goto L_180009c23;
L_180009c23:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180009c27;
L_180009c27:
  T=M.subflags(M.read16((R.r10+0x4ull)),uint16_t(R.rax),16);
  goto L_180009c2c;
L_180009c2c:
  if (!M.zf) goto L_180009c3c; goto L_180009c2e;
L_180009c2e:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180009c31;
L_180009c31:
  T=M.subflags(M.read16((R.r10)),uint16_t(R.rax),16);
  goto L_180009c35;
L_180009c35:
  if (!M.zf) goto L_180009c3c; goto L_180009c37;
L_180009c37:
  R.r11=(R.r11&~0xffull)|(uint8_t(1ull)); goto L_180009c3a;
L_180009c3a:
  goto L_180009c3f;
L_180009c3c:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_180009c3f;
L_180009c3f:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180009c42;
L_180009c42:
  if (M.zf) goto L_180009dd5; goto L_180009c48;
L_180009c48:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180009c4b;
L_180009c4b:
  if (M.zf) goto L_180009dd5; goto L_180009c51;
L_180009c51:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180009c55;
L_180009c55:
  T=M.subflags(M.read16((R.r8+0x2ull)),uint16_t(R.rax),16);
  goto L_180009c5a;
L_180009c5a:
  if (!M.zf) goto L_180009dd5; goto L_180009c60;
L_180009c60:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180009c64;
L_180009c64:
  T=M.subflags(M.read16((R.r8+0x6ull)),uint16_t(R.rax),16);
  goto L_180009c69;
L_180009c69:
  if (!M.zf) goto L_180009dd5; goto L_180009c6f;
L_180009c6f:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180009c73;
L_180009c73:
  T=M.subflags(M.read16((R.r8+0x4ull)),uint16_t(R.rax),16);
  goto L_180009c78;
L_180009c78:
  if (!M.zf) goto L_180009dd5; goto L_180009c7e;
L_180009c7e:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180009c81;
L_180009c81:
  T=M.subflags(M.read16((R.r8)),uint16_t(R.rax),16);
  goto L_180009c85;
L_180009c85:
  if (!M.zf) goto L_180009dd5; goto L_180009c8b;
L_180009c8b:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009c8d;
L_180009c8d:
  goto L_180009dd7;
L_180009c92:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009c95;
L_180009c95:
  if (M.zf) goto L_180009cff; goto L_180009c97;
L_180009c97:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180009c9a;
L_180009c9a:
  if (M.zf) goto L_180009cff; goto L_180009c9c;
L_180009c9c:
  R.rdx=uint32_t(M.read16((R.r8+0x2ull))); goto L_180009ca1;
L_180009ca1:
  R.r11=uint32_t(uint32_t(R.r14)); goto L_180009ca4;
L_180009ca4:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180009ca9;
L_180009ca9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cab;
L_180009cab:
  R.r11=uint32_t((uint32_t(R.r11))<<((7ull)&0x3f)); goto L_180009caf;
L_180009caf:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009cb0;
L_180009cb0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009cb2;
L_180009cb2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cb4;
L_180009cb4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r11),32);
  goto L_180009cb7;
L_180009cb7:
  if (!M.zf&&(M.sf==M.of)) goto L_180009cff; goto L_180009cb9;
L_180009cb9:
  R.rdx=uint32_t(M.read16((R.r8+0x6ull))); goto L_180009cbe;
L_180009cbe:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180009cc3;
L_180009cc3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cc5;
L_180009cc5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009cc6;
L_180009cc6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009cc8;
L_180009cc8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cca;
L_180009cca:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r11),32);
  goto L_180009ccd;
L_180009ccd:
  if (!M.zf&&(M.sf==M.of)) goto L_180009cff; goto L_180009ccf;
L_180009ccf:
  R.rdx=uint32_t(M.read16((R.r8+0x4ull))); goto L_180009cd4;
L_180009cd4:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180009cd9;
L_180009cd9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cdb;
L_180009cdb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009cdc;
L_180009cdc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009cde;
L_180009cde:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009ce0;
L_180009ce0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r11),32);
  goto L_180009ce3;
L_180009ce3:
  if (!M.zf&&(M.sf==M.of)) goto L_180009cff; goto L_180009ce5;
L_180009ce5:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180009ce9;
L_180009ce9:
  R.rdx=uint32_t(M.read16((R.r9))); goto L_180009ced;
L_180009ced:
  T=M.subflags(uint32_t(R.rdx),uint32_t(R.rax),32);
  R.rdx=uint32_t(T);
  goto L_180009cef;
L_180009cef:
  R.rax=uint32_t(uint32_t(R.rdx)); goto L_180009cf1;
L_180009cf1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009cf2;
L_180009cf2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009cf4;
L_180009cf4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009cf6;
L_180009cf6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r11),32);
  goto L_180009cf9;
L_180009cf9:
  if (!M.zf&&(M.sf==M.of)) goto L_180009cff; goto L_180009cfb;
L_180009cfb:
  R.rbx=(R.rbx&~0xffull)|(uint8_t(1ull)); goto L_180009cfd;
L_180009cfd:
  goto L_180009d01;
L_180009cff:
  T=(uint8_t(R.rbx)) ^ (uint8_t(R.rbx)); M.logicflags(T,8);
  R.rbx=(R.rbx&~0xffull)|(uint8_t(T));
  goto L_180009d01;
L_180009d01:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009d04;
L_180009d04:
  if (M.zf) goto L_180009d6b; goto L_180009d06;
L_180009d06:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180009d09;
L_180009d09:
  if (M.zf) goto L_180009d6b; goto L_180009d0b;
L_180009d0b:
  R.rdx=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180009d0f;
L_180009d0f:
  R.r9=uint32_t(uint32_t(R.r14)); goto L_180009d12;
L_180009d12:
  R.rax=uint32_t(M.read16((R.r10+0x2ull))); goto L_180009d17;
L_180009d17:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d19;
L_180009d19:
  R.r9=uint32_t((uint32_t(R.r9))<<((7ull)&0x3f)); goto L_180009d1d;
L_180009d1d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009d1e;
L_180009d1e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009d20;
L_180009d20:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d22;
L_180009d22:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009d25;
L_180009d25:
  if (!M.zf&&(M.sf==M.of)) goto L_180009d6b; goto L_180009d27;
L_180009d27:
  R.rdx=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180009d2b;
L_180009d2b:
  R.rax=uint32_t(M.read16((R.r10+0x6ull))); goto L_180009d30;
L_180009d30:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d32;
L_180009d32:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009d33;
L_180009d33:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009d35;
L_180009d35:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d37;
L_180009d37:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009d3a;
L_180009d3a:
  if (!M.zf&&(M.sf==M.of)) goto L_180009d6b; goto L_180009d3c;
L_180009d3c:
  R.rdx=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180009d40;
L_180009d40:
  R.rax=uint32_t(M.read16((R.r10+0x4ull))); goto L_180009d45;
L_180009d45:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d47;
L_180009d47:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009d48;
L_180009d48:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009d4a;
L_180009d4a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d4c;
L_180009d4c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009d4f;
L_180009d4f:
  if (!M.zf&&(M.sf==M.of)) goto L_180009d6b; goto L_180009d51;
L_180009d51:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180009d54;
L_180009d54:
  R.rdx=uint32_t(M.read16((R.r10))); goto L_180009d58;
L_180009d58:
  T=M.subflags(uint32_t(R.rdx),uint32_t(R.rax),32);
  R.rdx=uint32_t(T);
  goto L_180009d5a;
L_180009d5a:
  R.rax=uint32_t(uint32_t(R.rdx)); goto L_180009d5c;
L_180009d5c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009d5d;
L_180009d5d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009d5f;
L_180009d5f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d61;
L_180009d61:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009d64;
L_180009d64:
  if (!M.zf&&(M.sf==M.of)) goto L_180009d6b; goto L_180009d66;
L_180009d66:
  R.r11=(R.r11&~0xffull)|(uint8_t(1ull)); goto L_180009d69;
L_180009d69:
  goto L_180009d6e;
L_180009d6b:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_180009d6e;
L_180009d6e:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180009d71;
L_180009d71:
  if (M.zf) goto L_180009dd5; goto L_180009d73;
L_180009d73:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180009d76;
L_180009d76:
  if (M.zf) goto L_180009dd5; goto L_180009d78;
L_180009d78:
  R.rdx=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180009d7c;
L_180009d7c:
  R.r9=uint32_t(uint32_t(R.r14)); goto L_180009d7f;
L_180009d7f:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180009d84;
L_180009d84:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d86;
L_180009d86:
  R.r9=uint32_t((uint32_t(R.r9))<<((7ull)&0x3f)); goto L_180009d8a;
L_180009d8a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009d8b;
L_180009d8b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009d8d;
L_180009d8d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d8f;
L_180009d8f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009d92;
L_180009d92:
  if (!M.zf&&(M.sf==M.of)) goto L_180009dd5; goto L_180009d94;
L_180009d94:
  R.rdx=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180009d98;
L_180009d98:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180009d9d;
L_180009d9d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009d9f;
L_180009d9f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009da0;
L_180009da0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009da2;
L_180009da2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009da4;
L_180009da4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009da7;
L_180009da7:
  if (!M.zf&&(M.sf==M.of)) goto L_180009dd5; goto L_180009da9;
L_180009da9:
  R.rdx=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180009dad;
L_180009dad:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180009db2;
L_180009db2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009db4;
L_180009db4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009db5;
L_180009db5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009db7;
L_180009db7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009db9;
L_180009db9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009dbc;
L_180009dbc:
  if (!M.zf&&(M.sf==M.of)) goto L_180009dd5; goto L_180009dbe;
L_180009dbe:
  R.rdx=uint32_t(M.read16((R.rcx))); goto L_180009dc1;
L_180009dc1:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180009dc5;
L_180009dc5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009dc7;
L_180009dc7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009dc8;
L_180009dc8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009dca;
L_180009dca:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009dcc;
L_180009dcc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180009dcf;
L_180009dcf:
  if (!M.zf&&(M.sf==M.of)) goto L_180009dd5; goto L_180009dd1;
L_180009dd1:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009dd3;
L_180009dd3:
  goto L_180009dd7;
L_180009dd5:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180009dd7;
L_180009dd7:
  R.r10=uint64_t(R.rcx); goto L_180009dda;
L_180009dda:
  R.rcx=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009dde;
L_180009dde:
  R.r9=uint64_t(R.r8); goto L_180009de1;
L_180009de1:
  T=(uint8_t(R.rbx)) & (uint8_t(R.rbx)); M.logicflags(T,8);
  goto L_180009de3;
L_180009de3:
  if (!M.zf) goto L_180009b40; goto L_180009de9;
L_180009de9:
  T=(uint8_t(R.rbx)) & (uint8_t(R.rbx)); M.logicflags(T,8);
  goto L_180009deb;
L_180009deb:
  if(!M.zf){R.rbp=uint32_t(M.read32((R.rsp+0x50ull)));} goto L_180009df0;
L_180009df0:
  R.rax=uint32_t(1ull); goto L_180009df5;
L_180009df5:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_180009df8;
L_180009df8:
  if(M.zf){R.rbp=uint32_t(uint32_t(R.rax));} goto L_180009dfb;
L_180009dfb:
  T=(uint8_t(R.rbx)) & (uint8_t(R.rbx)); M.logicflags(T,8);
  goto L_180009dfd;
L_180009dfd:
  if (!M.zf) goto L_180009e0a; goto L_180009dff;
L_180009dff:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_180009e02;
L_180009e02:
  R.rax=uint32_t(2ull); goto L_180009e07;
L_180009e07:
  if(M.zf){R.rbp=uint32_t(uint32_t(R.rax));} goto L_180009e0a;
L_180009e0a:
  R.rax=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009e0e;
L_180009e0e:
  T=M.subflags(M.read32((R.r15)),uint32_t(R.r13),32);
  M.write32((R.r15), T);
  goto L_180009e11;
L_180009e11:
  T=M.subflags(M.read32((R.r12)),uint32_t(R.rax),32);
  M.write32((R.r12), T);
  goto L_180009e15;
L_180009e15:
  R.rax=uint32_t(uint32_t(R.rbp)); goto L_180009e17;
L_180009e17:
  R.rbp=uint64_t(M.read64((R.rsp+0x40ull))); goto L_180009e1c;
L_180009e1c:
  R.rbx=uint64_t(M.read64((R.rsp+0x38ull))); goto L_180009e21;
L_180009e21:
  R.rsi=uint64_t(M.read64((R.rsp+0x48ull))); goto L_180009e26;
L_180009e26:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009e28;
L_180009e28:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009e2a;
L_180009e2a:
  R.r13=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009e2c;
L_180009e2c:
  R.r12=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009e2e;
L_180009e2e:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009e2f;
L_180009e2f:
  return (uint16_t*)(uintptr_t)R.rax;
