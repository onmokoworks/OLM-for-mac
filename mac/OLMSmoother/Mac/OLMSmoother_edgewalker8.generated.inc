// Generated from olmsmoother_v1_edgewalker8_cfg_20260805.json; do not hand edit.
L_180009e30:
  M.write64((R.rsp+0x10ull), R.rbx); goto L_180009e35;
L_180009e35:
  M.write64((R.rsp+0x18ull), R.rbp); goto L_180009e3a;
L_180009e3a:
  M.write64((R.rsp+0x20ull), R.rsi); goto L_180009e3f;
L_180009e3f:
  M.write64((R.rsp+0x8ull), R.rcx); goto L_180009e44;
L_180009e44:
  R.rsp-=8; M.write64(R.rsp,R.rdi); goto L_180009e45;
L_180009e45:
  R.rsp-=8; M.write64(R.rsp,R.r12); goto L_180009e47;
L_180009e47:
  R.rsp-=8; M.write64(R.rsp,R.r13); goto L_180009e49;
L_180009e49:
  R.rsp-=8; M.write64(R.rsp,R.r14); goto L_180009e4b;
L_180009e4b:
  R.rsp-=8; M.write64(R.rsp,R.r15); goto L_180009e4d;
L_180009e4d:
  R.r15=uint64_t(M.read64((R.rsp+0x58ull))); goto L_180009e52;
L_180009e52:
  R.r11=uint64_t((0x180009e59-0x9e59ull)); goto L_180009e59;
L_180009e59:
  R.r12=uint64_t(M.read64((R.rsp+0x60ull))); goto L_180009e5e;
L_180009e5e:
  T=(uint32_t(R.r14)) ^ (uint32_t(R.r14)); M.logicflags(T,32);
  R.r14=uint32_t(T);
  goto L_180009e61;
L_180009e61:
  R.rbx=uint32_t(M.read32((R.rsp+0x68ull))); goto L_180009e65;
L_180009e65:
  R.r10=uint64_t(int64_t(int32_t(uint32_t(R.rdx)))); goto L_180009e68;
L_180009e68:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.r9)))); goto L_180009e6b;
L_180009e6b:
  R.r9=uint64_t(((R.rax*4ull))); goto L_180009e73;
L_180009e73:
  R.rbp=uint32_t(M.read32((R.r9+R.r11+0xf0c8ull))); goto L_180009e7b;
L_180009e7b:
  R.rsi=uint32_t(M.read32((R.r9+R.r11+0xf0f0ull))); goto L_180009e83;
L_180009e83:
  T=M.addflags(uint32_t(R.rbp),uint32_t(R.r10),32); R.rbp=uint32_t(T); goto L_180009e86;
L_180009e86:
  M.write32((R.r15), uint32_t(R.r10)); goto L_180009e89;
L_180009e89:
  T=M.addflags(uint32_t(R.rsi),uint32_t(R.r8),32); R.rsi=uint32_t(T); goto L_180009e8c;
L_180009e8c:
  M.write32((R.r12), uint32_t(R.r8)); goto L_180009e90;
L_180009e90:
  R.r9=uint32_t(uint32_t(R.r14)); goto L_180009e93;
L_180009e93:
  R.rdx=uint64_t(M.read64((R.rcx+0x10ull))); goto L_180009e97;
L_180009e97:
  T=(uint32_t(R.r10)) & (uint32_t(R.r10)); M.logicflags(T,32);
  goto L_180009e9a;
L_180009e9a:
  if (M.sf) goto L_180009ebd; goto L_180009e9c;
L_180009e9c:
  T=M.subflags(uint32_t(R.r10),M.read32((R.rdx+0x24ull)),32);
  goto L_180009ea0;
L_180009ea0:
  if (M.sf==M.of) goto L_180009ebd; goto L_180009ea2;
L_180009ea2:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_180009ea5;
L_180009ea5:
  if (M.sf) goto L_180009ebd; goto L_180009ea7;
L_180009ea7:
  T=M.subflags(uint32_t(R.r8),M.read32((R.rdx+0x28ull)),32);
  goto L_180009eab;
L_180009eab:
  if (M.sf==M.of) goto L_180009ebd; goto L_180009ead;
L_180009ead:
  R.r8=uint32_t(int64_t(int32_t(uint32_t(R.r8)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180009eb2;
L_180009eb2:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.r8)))); goto L_180009eb5;
L_180009eb5:
  R.r9=uint64_t((R.rcx+(R.r10*4ull))); goto L_180009eb9;
L_180009eb9:
  T=M.addflags(R.r9,M.read64((R.rdx+0x18ull)),64); R.r9=uint64_t(T); goto L_180009ebd;
L_180009ebd:
  R.r10=uint64_t(R.r14); goto L_180009ec0;
L_180009ec0:
  T=(uint32_t(R.rbp)) & (uint32_t(R.rbp)); M.logicflags(T,32);
  goto L_180009ec2;
L_180009ec2:
  if (M.sf) goto L_180009ee6; goto L_180009ec4;
L_180009ec4:
  T=M.subflags(uint32_t(R.rbp),M.read32((R.rdx+0x24ull)),32);
  goto L_180009ec7;
L_180009ec7:
  if (M.sf==M.of) goto L_180009ee6; goto L_180009ec9;
L_180009ec9:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_180009ecb;
L_180009ecb:
  if (M.sf) goto L_180009ee6; goto L_180009ecd;
L_180009ecd:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.rdx+0x28ull)),32);
  goto L_180009ed0;
L_180009ed0:
  if (M.sf==M.of) goto L_180009ee6; goto L_180009ed2;
L_180009ed2:
  R.rax=uint32_t(uint32_t(R.rsi)); goto L_180009ed4;
L_180009ed4:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180009ed8;
L_180009ed8:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180009edb;
L_180009edb:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rbp)))); goto L_180009ede;
L_180009ede:
  R.r10=uint64_t((R.rcx+(R.rax*4ull))); goto L_180009ee2;
L_180009ee2:
  T=M.addflags(R.r10,M.read64((R.rdx+0x18ull)),64); R.r10=uint64_t(T); goto L_180009ee6;
L_180009ee6:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x50ull))))); goto L_180009eeb;
L_180009eeb:
  R.r8=uint32_t(M.read32((R.r11+(R.rax*4ull)+0xf0f0ull))); goto L_180009ef3;
L_180009ef3:
  R.r13=uint32_t(M.read32((R.r11+(R.rax*4ull)+0xf0c8ull))); goto L_180009efb;
L_180009efb:
  M.write32((R.rsp+0x68ull), uint32_t(R.r8)); goto L_180009f00;
L_180009f00:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_180009f02;
L_180009f02:
  if (!M.zf) goto L_180009f65; goto L_180009f04;
L_180009f04:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009f07;
L_180009f07:
  R.rdi=(R.rdi&~0xffull)|(uint8_t(uint8_t(!M.zf))); goto L_180009f0b;
L_180009f0b:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009f0e;
L_180009f0e:
  R.r11=(R.r11&~0xffull)|(uint8_t(uint8_t(!M.zf))); goto L_180009f12;
L_180009f12:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009f15;
L_180009f15:
  if (M.zf) goto L_180009fe9; goto L_180009f1b;
L_180009f1b:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009f1e;
L_180009f1e:
  if (M.zf) goto L_180009fe9; goto L_180009f24;
L_180009f24:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_180009f29;
L_180009f29:
  T=M.subflags(M.read8((R.r9+0x1ull)),uint8_t(R.rax),8);
  goto L_180009f2d;
L_180009f2d:
  if (!M.zf) goto L_180009fe9; goto L_180009f33;
L_180009f33:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_180009f38;
L_180009f38:
  T=M.subflags(M.read8((R.r9+0x3ull)),uint8_t(R.rax),8);
  goto L_180009f3c;
L_180009f3c:
  if (!M.zf) goto L_180009fe9; goto L_180009f42;
L_180009f42:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_180009f47;
L_180009f47:
  T=M.subflags(M.read8((R.r9+0x2ull)),uint8_t(R.rax),8);
  goto L_180009f4b;
L_180009f4b:
  if (!M.zf) goto L_180009fe9; goto L_180009f51;
L_180009f51:
  R.rax=uint32_t(M.read8((R.r10))); goto L_180009f55;
L_180009f55:
  T=M.subflags(M.read8((R.r9)),uint8_t(R.rax),8);
  goto L_180009f58;
L_180009f58:
  if (!M.zf) goto L_180009fe9; goto L_180009f5e;
L_180009f5e:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009f60;
L_180009f60:
  goto L_180009feb;
L_180009f65:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009f68;
L_180009f68:
  if (M.zf) goto L_180009f72; goto L_180009f6a;
L_180009f6a:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_180009f6c;
L_180009f6c:
  R.rdi=(R.rdi&~0xffull)|(uint8_t(uint8_t(!M.sf))); goto L_180009f70;
L_180009f70:
  goto L_180009f75;
L_180009f72:
  T=(uint8_t(R.rdi)) ^ (uint8_t(R.rdi)); M.logicflags(T,8);
  R.rdi=(R.rdi&~0xffull)|(uint8_t(T));
  goto L_180009f75;
L_180009f75:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009f78;
L_180009f78:
  if (M.zf) goto L_180009f82; goto L_180009f7a;
L_180009f7a:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_180009f7c;
L_180009f7c:
  R.r11=(R.r11&~0xffull)|(uint8_t(uint8_t(!M.sf))); goto L_180009f80;
L_180009f80:
  goto L_180009f85;
L_180009f82:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_180009f85;
L_180009f85:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180009f88;
L_180009f88:
  if (M.zf) goto L_180009fe9; goto L_180009f8a;
L_180009f8a:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009f8d;
L_180009f8d:
  if (M.zf) goto L_180009fe9; goto L_180009f8f;
L_180009f8f:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_180009f94;
L_180009f94:
  R.rcx=uint32_t(M.read8((R.r9+0x1ull))); goto L_180009f99;
L_180009f99:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009f9b;
L_180009f9b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009f9d;
L_180009f9d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009f9e;
L_180009f9e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009fa0;
L_180009fa0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009fa2;
L_180009fa2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_180009fa4;
L_180009fa4:
  if (!M.zf&&(M.sf==M.of)) goto L_180009fe9; goto L_180009fa6;
L_180009fa6:
  R.rcx=uint32_t(M.read8((R.r10+0x3ull))); goto L_180009fab;
L_180009fab:
  R.rax=uint32_t(M.read8((R.r9+0x3ull))); goto L_180009fb0;
L_180009fb0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180009fb2;
L_180009fb2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009fb3;
L_180009fb3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009fb5;
L_180009fb5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009fb7;
L_180009fb7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_180009fb9;
L_180009fb9:
  if (!M.zf&&(M.sf==M.of)) goto L_180009fe9; goto L_180009fbb;
L_180009fbb:
  R.rcx=uint32_t(M.read8((R.r10+0x2ull))); goto L_180009fc0;
L_180009fc0:
  R.rax=uint32_t(M.read8((R.r9+0x2ull))); goto L_180009fc5;
L_180009fc5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180009fc7;
L_180009fc7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009fc8;
L_180009fc8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009fca;
L_180009fca:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009fcc;
L_180009fcc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_180009fce;
L_180009fce:
  if (!M.zf&&(M.sf==M.of)) goto L_180009fe9; goto L_180009fd0;
L_180009fd0:
  R.rax=uint32_t(M.read8((R.r10))); goto L_180009fd4;
L_180009fd4:
  R.rcx=uint32_t(M.read8((R.r9))); goto L_180009fd8;
L_180009fd8:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009fda;
L_180009fda:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009fdc;
L_180009fdc:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009fdd;
L_180009fdd:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009fdf;
L_180009fdf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009fe1;
L_180009fe1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_180009fe3;
L_180009fe3:
  if (!M.zf&&(M.sf==M.of)) goto L_180009fe9; goto L_180009fe5;
L_180009fe5:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009fe7;
L_180009fe7:
  goto L_180009feb;
L_180009fe9:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180009feb;
L_180009feb:
  T=(uint8_t(R.rdi)) & (uint8_t(R.rdi)); M.logicflags(T,8);
  goto L_180009fee;
L_180009fee:
  if (M.zf) goto L_18000a279; goto L_180009ff4;
L_180009ff4:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_180009ff7;
L_180009ff7:
  if (M.zf) goto L_18000a276; goto L_180009ffd;
L_180009ffd:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180009fff;
L_180009fff:
  if (!M.zf) goto L_18000a276; goto L_18000a005;
L_18000a005:
  T=M.addflags(M.read32((R.r15)),uint32_t(R.r13),32); M.write32((R.r15), T); goto L_18000a008;
L_18000a008:
  T=M.addflags(uint32_t(R.rsi),uint32_t(R.r8),32); R.rsi=uint32_t(T); goto L_18000a00b;
L_18000a00b:
  T=M.addflags(M.read32((R.r12)),uint32_t(R.r8),32); M.write32((R.r12), T); goto L_18000a00f;
L_18000a00f:
  T=M.addflags(uint32_t(R.rbp),uint32_t(R.r13),32); R.rbp=uint32_t(T); goto L_18000a012;
L_18000a012:
  R.rcx=uint64_t(M.read64((R.rsp+0x30ull))); goto L_18000a017;
L_18000a017:
  R.r8=uint64_t(R.r14); goto L_18000a01a;
L_18000a01a:
  R.r11=uint64_t(int64_t(int32_t(M.read32((R.r15))))); goto L_18000a01d;
L_18000a01d:
  R.rax=uint32_t(M.read32((R.r12))); goto L_18000a021;
L_18000a021:
  R.rdx=uint64_t(M.read64((R.rcx+0x10ull))); goto L_18000a025;
L_18000a025:
  T=(uint32_t(R.r11)) & (uint32_t(R.r11)); M.logicflags(T,32);
  goto L_18000a028;
L_18000a028:
  if (M.sf) goto L_18000a048; goto L_18000a02a;
L_18000a02a:
  T=M.subflags(uint32_t(R.r11),M.read32((R.rdx+0x24ull)),32);
  goto L_18000a02e;
L_18000a02e:
  if (M.sf==M.of) goto L_18000a048; goto L_18000a030;
L_18000a030:
  T=(uint32_t(R.rax)) & (uint32_t(R.rax)); M.logicflags(T,32);
  goto L_18000a032;
L_18000a032:
  if (M.sf) goto L_18000a048; goto L_18000a034;
L_18000a034:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rdx+0x28ull)),32);
  goto L_18000a037;
L_18000a037:
  if (M.sf==M.of) goto L_18000a048; goto L_18000a039;
L_18000a039:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_18000a03d;
L_18000a03d:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_18000a040;
L_18000a040:
  R.r8=uint64_t((R.rcx+(R.r11*4ull))); goto L_18000a044;
L_18000a044:
  T=M.addflags(R.r8,M.read64((R.rdx+0x18ull)),64); R.r8=uint64_t(T); goto L_18000a048;
L_18000a048:
  R.rcx=uint64_t(R.r14); goto L_18000a04b;
L_18000a04b:
  T=(uint32_t(R.rbp)) & (uint32_t(R.rbp)); M.logicflags(T,32);
  goto L_18000a04d;
L_18000a04d:
  if (M.sf) goto L_18000a071; goto L_18000a04f;
L_18000a04f:
  T=M.subflags(uint32_t(R.rbp),M.read32((R.rdx+0x24ull)),32);
  goto L_18000a052;
L_18000a052:
  if (M.sf==M.of) goto L_18000a071; goto L_18000a054;
L_18000a054:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_18000a056;
L_18000a056:
  if (M.sf) goto L_18000a071; goto L_18000a058;
L_18000a058:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.rdx+0x28ull)),32);
  goto L_18000a05b;
L_18000a05b:
  if (M.sf==M.of) goto L_18000a071; goto L_18000a05d;
L_18000a05d:
  R.rax=uint32_t(uint32_t(R.rsi)); goto L_18000a05f;
L_18000a05f:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_18000a063;
L_18000a063:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_18000a066;
L_18000a066:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rbp)))); goto L_18000a069;
L_18000a069:
  R.rcx=uint64_t((R.rcx+(R.rax*4ull))); goto L_18000a06d;
L_18000a06d:
  T=M.addflags(R.rcx,M.read64((R.rdx+0x18ull)),64); R.rcx=uint64_t(T); goto L_18000a071;
L_18000a071:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_18000a073;
L_18000a073:
  if (!M.zf) goto L_18000a13c; goto L_18000a079;
L_18000a079:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_18000a07c;
L_18000a07c:
  if (M.zf) goto L_18000a0b2; goto L_18000a07e;
L_18000a07e:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000a081;
L_18000a081:
  if (M.zf) goto L_18000a0b2; goto L_18000a083;
L_18000a083:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_18000a088;
L_18000a088:
  T=M.subflags(M.read8((R.r9+0x1ull)),uint8_t(R.rax),8);
  goto L_18000a08c;
L_18000a08c:
  if (!M.zf) goto L_18000a0b2; goto L_18000a08e;
L_18000a08e:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_18000a093;
L_18000a093:
  T=M.subflags(M.read8((R.r9+0x3ull)),uint8_t(R.rax),8);
  goto L_18000a097;
L_18000a097:
  if (!M.zf) goto L_18000a0b2; goto L_18000a099;
L_18000a099:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_18000a09e;
L_18000a09e:
  T=M.subflags(M.read8((R.r9+0x2ull)),uint8_t(R.rax),8);
  goto L_18000a0a2;
L_18000a0a2:
  if (!M.zf) goto L_18000a0b2; goto L_18000a0a4;
L_18000a0a4:
  R.rax=uint32_t(M.read8((R.r8))); goto L_18000a0a8;
L_18000a0a8:
  T=M.subflags(M.read8((R.r9)),uint8_t(R.rax),8);
  goto L_18000a0ab;
L_18000a0ab:
  if (!M.zf) goto L_18000a0b2; goto L_18000a0ad;
L_18000a0ad:
  R.rdi=(R.rdi&~0xffull)|(uint8_t(1ull)); goto L_18000a0b0;
L_18000a0b0:
  goto L_18000a0b5;
L_18000a0b2:
  T=(uint8_t(R.rdi)) ^ (uint8_t(R.rdi)); M.logicflags(T,8);
  R.rdi=(R.rdi&~0xffull)|(uint8_t(T));
  goto L_18000a0b5;
L_18000a0b5:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_18000a0b8;
L_18000a0b8:
  if (M.zf) goto L_18000a0ea; goto L_18000a0ba;
L_18000a0ba:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_18000a0bd;
L_18000a0bd:
  if (M.zf) goto L_18000a0ea; goto L_18000a0bf;
L_18000a0bf:
  R.rax=uint32_t(M.read8((R.rcx+0x1ull))); goto L_18000a0c3;
L_18000a0c3:
  T=M.subflags(M.read8((R.r10+0x1ull)),uint8_t(R.rax),8);
  goto L_18000a0c7;
L_18000a0c7:
  if (!M.zf) goto L_18000a0ea; goto L_18000a0c9;
L_18000a0c9:
  R.rax=uint32_t(M.read8((R.rcx+0x3ull))); goto L_18000a0cd;
L_18000a0cd:
  T=M.subflags(M.read8((R.r10+0x3ull)),uint8_t(R.rax),8);
  goto L_18000a0d1;
L_18000a0d1:
  if (!M.zf) goto L_18000a0ea; goto L_18000a0d3;
L_18000a0d3:
  R.rax=uint32_t(M.read8((R.rcx+0x2ull))); goto L_18000a0d7;
L_18000a0d7:
  T=M.subflags(M.read8((R.r10+0x2ull)),uint8_t(R.rax),8);
  goto L_18000a0db;
L_18000a0db:
  if (!M.zf) goto L_18000a0ea; goto L_18000a0dd;
L_18000a0dd:
  R.rax=uint32_t(M.read8((R.rcx))); goto L_18000a0e0;
L_18000a0e0:
  T=M.subflags(M.read8((R.r10)),uint8_t(R.rax),8);
  goto L_18000a0e3;
L_18000a0e3:
  if (!M.zf) goto L_18000a0ea; goto L_18000a0e5;
L_18000a0e5:
  R.r11=(R.r11&~0xffull)|(uint8_t(1ull)); goto L_18000a0e8;
L_18000a0e8:
  goto L_18000a0ed;
L_18000a0ea:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_18000a0ed;
L_18000a0ed:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000a0f0;
L_18000a0f0:
  if (M.zf) goto L_18000a260; goto L_18000a0f6;
L_18000a0f6:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_18000a0f9;
L_18000a0f9:
  if (M.zf) goto L_18000a260; goto L_18000a0ff;
L_18000a0ff:
  R.rax=uint32_t(M.read8((R.rcx+0x1ull))); goto L_18000a103;
L_18000a103:
  T=M.subflags(M.read8((R.r8+0x1ull)),uint8_t(R.rax),8);
  goto L_18000a107;
L_18000a107:
  if (!M.zf) goto L_18000a260; goto L_18000a10d;
L_18000a10d:
  R.rax=uint32_t(M.read8((R.rcx+0x3ull))); goto L_18000a111;
L_18000a111:
  T=M.subflags(M.read8((R.r8+0x3ull)),uint8_t(R.rax),8);
  goto L_18000a115;
L_18000a115:
  if (!M.zf) goto L_18000a260; goto L_18000a11b;
L_18000a11b:
  R.rax=uint32_t(M.read8((R.rcx+0x2ull))); goto L_18000a11f;
L_18000a11f:
  T=M.subflags(M.read8((R.r8+0x2ull)),uint8_t(R.rax),8);
  goto L_18000a123;
L_18000a123:
  if (!M.zf) goto L_18000a260; goto L_18000a129;
L_18000a129:
  R.rax=uint32_t(M.read8((R.rcx))); goto L_18000a12c;
L_18000a12c:
  T=M.subflags(M.read8((R.r8)),uint8_t(R.rax),8);
  goto L_18000a12f;
L_18000a12f:
  if (!M.zf) goto L_18000a260; goto L_18000a135;
L_18000a135:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_18000a137;
L_18000a137:
  goto L_18000a262;
L_18000a13c:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_18000a13f;
L_18000a13f:
  if (M.zf) goto L_18000a19f; goto L_18000a141;
L_18000a141:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000a144;
L_18000a144:
  if (M.zf) goto L_18000a19f; goto L_18000a146;
L_18000a146:
  R.rdx=uint32_t(M.read8((R.r8+0x1ull))); goto L_18000a14b;
L_18000a14b:
  R.rax=uint32_t(M.read8((R.r9+0x1ull))); goto L_18000a150;
L_18000a150:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a152;
L_18000a152:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a153;
L_18000a153:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a155;
L_18000a155:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a157;
L_18000a157:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a159;
L_18000a159:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a19f; goto L_18000a15b;
L_18000a15b:
  R.rdx=uint32_t(M.read8((R.r8+0x3ull))); goto L_18000a160;
L_18000a160:
  R.rax=uint32_t(M.read8((R.r9+0x3ull))); goto L_18000a165;
L_18000a165:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a167;
L_18000a167:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a168;
L_18000a168:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a16a;
L_18000a16a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a16c;
L_18000a16c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a16e;
L_18000a16e:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a19f; goto L_18000a170;
L_18000a170:
  R.rdx=uint32_t(M.read8((R.r8+0x2ull))); goto L_18000a175;
L_18000a175:
  R.rax=uint32_t(M.read8((R.r9+0x2ull))); goto L_18000a17a;
L_18000a17a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a17c;
L_18000a17c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a17d;
L_18000a17d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a17f;
L_18000a17f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a181;
L_18000a181:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a183;
L_18000a183:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a19f; goto L_18000a185;
L_18000a185:
  R.rax=uint32_t(M.read8((R.r8))); goto L_18000a189;
L_18000a189:
  R.rdx=uint32_t(M.read8((R.r9))); goto L_18000a18d;
L_18000a18d:
  T=M.subflags(uint32_t(R.rdx),uint32_t(R.rax),32);
  R.rdx=uint32_t(T);
  goto L_18000a18f;
L_18000a18f:
  R.rax=uint32_t(uint32_t(R.rdx)); goto L_18000a191;
L_18000a191:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a192;
L_18000a192:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a194;
L_18000a194:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a196;
L_18000a196:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a198;
L_18000a198:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a19f; goto L_18000a19a;
L_18000a19a:
  R.rdi=(R.rdi&~0xffull)|(uint8_t(1ull)); goto L_18000a19d;
L_18000a19d:
  goto L_18000a1a2;
L_18000a19f:
  T=(uint8_t(R.rdi)) ^ (uint8_t(R.rdi)); M.logicflags(T,8);
  R.rdi=(R.rdi&~0xffull)|(uint8_t(T));
  goto L_18000a1a2;
L_18000a1a2:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_18000a1a5;
L_18000a1a5:
  if (M.zf) goto L_18000a201; goto L_18000a1a7;
L_18000a1a7:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_18000a1aa;
L_18000a1aa:
  if (M.zf) goto L_18000a201; goto L_18000a1ac;
L_18000a1ac:
  R.rdx=uint32_t(M.read8((R.rcx+0x1ull))); goto L_18000a1b0;
L_18000a1b0:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_18000a1b5;
L_18000a1b5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1b7;
L_18000a1b7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a1b8;
L_18000a1b8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a1ba;
L_18000a1ba:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1bc;
L_18000a1bc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a1be;
L_18000a1be:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a201; goto L_18000a1c0;
L_18000a1c0:
  R.rdx=uint32_t(M.read8((R.rcx+0x3ull))); goto L_18000a1c4;
L_18000a1c4:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_18000a1c9;
L_18000a1c9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1cb;
L_18000a1cb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a1cc;
L_18000a1cc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a1ce;
L_18000a1ce:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1d0;
L_18000a1d0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a1d2;
L_18000a1d2:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a201; goto L_18000a1d4;
L_18000a1d4:
  R.rdx=uint32_t(M.read8((R.rcx+0x2ull))); goto L_18000a1d8;
L_18000a1d8:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_18000a1dd;
L_18000a1dd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1df;
L_18000a1df:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a1e0;
L_18000a1e0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a1e2;
L_18000a1e2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1e4;
L_18000a1e4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a1e6;
L_18000a1e6:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a201; goto L_18000a1e8;
L_18000a1e8:
  R.rax=uint32_t(M.read8((R.rcx))); goto L_18000a1eb;
L_18000a1eb:
  R.rdx=uint32_t(M.read8((R.r10))); goto L_18000a1ef;
L_18000a1ef:
  T=M.subflags(uint32_t(R.rdx),uint32_t(R.rax),32);
  R.rdx=uint32_t(T);
  goto L_18000a1f1;
L_18000a1f1:
  R.rax=uint32_t(uint32_t(R.rdx)); goto L_18000a1f3;
L_18000a1f3:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a1f4;
L_18000a1f4:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a1f6;
L_18000a1f6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a1f8;
L_18000a1f8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a1fa;
L_18000a1fa:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a201; goto L_18000a1fc;
L_18000a1fc:
  R.r11=(R.r11&~0xffull)|(uint8_t(1ull)); goto L_18000a1ff;
L_18000a1ff:
  goto L_18000a204;
L_18000a201:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_18000a204;
L_18000a204:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000a207;
L_18000a207:
  if (M.zf) goto L_18000a260; goto L_18000a209;
L_18000a209:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_18000a20c;
L_18000a20c:
  if (M.zf) goto L_18000a260; goto L_18000a20e;
L_18000a20e:
  R.rdx=uint32_t(M.read8((R.rcx+0x1ull))); goto L_18000a212;
L_18000a212:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_18000a217;
L_18000a217:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a219;
L_18000a219:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a21a;
L_18000a21a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a21c;
L_18000a21c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a21e;
L_18000a21e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a220;
L_18000a220:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a260; goto L_18000a222;
L_18000a222:
  R.rdx=uint32_t(M.read8((R.rcx+0x3ull))); goto L_18000a226;
L_18000a226:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_18000a22b;
L_18000a22b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a22d;
L_18000a22d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a22e;
L_18000a22e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a230;
L_18000a230:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a232;
L_18000a232:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a234;
L_18000a234:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a260; goto L_18000a236;
L_18000a236:
  R.rdx=uint32_t(M.read8((R.rcx+0x2ull))); goto L_18000a23a;
L_18000a23a:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_18000a23f;
L_18000a23f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a241;
L_18000a241:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a242;
L_18000a242:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a244;
L_18000a244:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a246;
L_18000a246:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a248;
L_18000a248:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a260; goto L_18000a24a;
L_18000a24a:
  R.rdx=uint32_t(M.read8((R.rcx))); goto L_18000a24d;
L_18000a24d:
  R.rax=uint32_t(M.read8((R.r8))); goto L_18000a251;
L_18000a251:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a253;
L_18000a253:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000a254;
L_18000a254:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000a256;
L_18000a256:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000a258;
L_18000a258:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbx),32);
  goto L_18000a25a;
L_18000a25a:
  if (!M.zf&&(M.sf==M.of)) goto L_18000a260; goto L_18000a25c;
L_18000a25c:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_18000a25e;
L_18000a25e:
  goto L_18000a262;
L_18000a260:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_18000a262;
L_18000a262:
  R.r9=uint64_t(R.r8); goto L_18000a265;
L_18000a265:
  R.r8=uint32_t(M.read32((R.rsp+0x68ull))); goto L_18000a26a;
L_18000a26a:
  R.r10=uint64_t(R.rcx); goto L_18000a26d;
L_18000a26d:
  T=(uint8_t(R.rdi)) & (uint8_t(R.rdi)); M.logicflags(T,8);
  goto L_18000a270;
L_18000a270:
  if (!M.zf) goto L_180009ff4; goto L_18000a276;
L_18000a276:
  T=(uint8_t(R.rdi)) & (uint8_t(R.rdi)); M.logicflags(T,8);
  goto L_18000a279;
L_18000a279:
  if(!M.zf){R.r14=uint32_t(M.read32((R.rsp+0x50ull)));} goto L_18000a27f;
L_18000a27f:
  R.rax=uint32_t(1ull); goto L_18000a284;
L_18000a284:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_18000a287;
L_18000a287:
  if(M.zf){R.r14=uint32_t(uint32_t(R.rax));} goto L_18000a28b;
L_18000a28b:
  T=(uint8_t(R.rdi)) & (uint8_t(R.rdi)); M.logicflags(T,8);
  goto L_18000a28e;
L_18000a28e:
  if (!M.zf) goto L_18000a29c; goto L_18000a290;
L_18000a290:
  T=(uint8_t(R.r11)) & (uint8_t(R.r11)); M.logicflags(T,8);
  goto L_18000a293;
L_18000a293:
  R.rax=uint32_t(2ull); goto L_18000a298;
L_18000a298:
  if(M.zf){R.r14=uint32_t(uint32_t(R.rax));} goto L_18000a29c;
L_18000a29c:
  T=M.subflags(M.read32((R.r15)),uint32_t(R.r13),32);
  M.write32((R.r15), T);
  goto L_18000a29f;
L_18000a29f:
  R.rax=uint32_t(uint32_t(R.r14)); goto L_18000a2a2;
L_18000a2a2:
  T=M.subflags(M.read32((R.r12)),uint32_t(R.r8),32);
  M.write32((R.r12), T);
  goto L_18000a2a6;
L_18000a2a6:
  R.rbx=uint64_t(M.read64((R.rsp+0x38ull))); goto L_18000a2ab;
L_18000a2ab:
  R.rbp=uint64_t(M.read64((R.rsp+0x40ull))); goto L_18000a2b0;
L_18000a2b0:
  R.rsi=uint64_t(M.read64((R.rsp+0x48ull))); goto L_18000a2b5;
L_18000a2b5:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000a2b7;
L_18000a2b7:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000a2b9;
L_18000a2b9:
  R.r13=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000a2bb;
L_18000a2bb:
  R.r12=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000a2bd;
L_18000a2bd:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000a2be;
L_18000a2be:
  return (uint8_t*)(uintptr_t)R.rax;
