// Generated from olmsmoother_v1_classifier16_cfg_20260811.json; do not hand edit.
L_180006a90:
  R.rsp-=8; M.write64(R.rsp,R.rbx); goto L_180006a92;
L_180006a92:
  R.rsp-=8; M.write64(R.rsp,R.rbp); goto L_180006a93;
L_180006a93:
  R.rsp-=8; M.write64(R.rsp,R.rsi); goto L_180006a94;
L_180006a94:
  R.rsp-=8; M.write64(R.rsp,R.rdi); goto L_180006a95;
L_180006a95:
  R.rsp-=8; M.write64(R.rsp,R.r14); goto L_180006a97;
L_180006a97:
  R.rsp-=8; M.write64(R.rsp,R.r15); goto L_180006a99;
L_180006a99:
  T=M.subflags(R.rsp,0x48ull,64);
  R.rsp=uint64_t(T);
  goto L_180006a9d;
L_180006a9d:
  R.rbx=uint64_t(M.read64((R.r9+0x20ull))); goto L_180006aa1;
L_180006aa1:
  R.rsi=uint64_t(R.r9); goto L_180006aa4;
L_180006aa4:
  R.r15=uint32_t(M.read32((R.rcx+0xcull))); goto L_180006aa8;
L_180006aa8:
  T=(uint32_t(R.rdi)) ^ (uint32_t(R.rdi)); M.logicflags(T,32);
  R.rdi=uint32_t(T);
  goto L_180006aaa;
L_180006aaa:
  R.r14=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180006ab2;
L_180006ab2:
  R.rcx=uint64_t(R.rbx); goto L_180006ab5;
L_180006ab5:
  R.rbp=uint64_t(M.read64((R.r9+(R.r14*8ull)))); goto L_180006ab9;
L_180006ab9:
  R.rdx=uint64_t(R.rbp); goto L_180006abc;
L_180006abc:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180006ac1;
L_180006ac1:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180006ac3;
L_180006ac3:
  R.rax=uint32_t(uint32_t(R.r15)); goto L_180006ac6;
L_180006ac6:
  T=M.subflags(0,uint32_t(R.rax),32); R.rax=uint32_t(T); goto L_180006ac8;
L_180006ac8:
  R.rax=uint32_t((uint32_t(R.rax))<<((7ull)&0x3f)); goto L_180006acb;
L_180006acb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180006acd;
L_180006acd:
  if (M.sf==M.of) goto L_18000804c; goto L_180006ad3;
L_180006ad3:
  R.r8=uint64_t(M.read64((R.rsi+0x30ull))); goto L_180006ad7;
L_180006ad7:
  R.r10=(R.r10&~0xffull)|(uint8_t(1ull)); goto L_180006ada;
L_180006ada:
  M.write64((R.rsp+0x88ull), R.r12); goto L_180006ae2;
L_180006ae2:
  M.write64((R.rsp+0x40ull), R.r13); goto L_180006ae7;
L_180006ae7:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180006aea;
L_180006aea:
  if (!M.zf) goto L_180006d1b; goto L_180006af0;
L_180006af0:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006af3;
L_180006af3:
  if (M.zf) goto L_180006b31; goto L_180006af5;
L_180006af5:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180006af8;
L_180006af8:
  if (M.zf) goto L_180006b31; goto L_180006afa;
L_180006afa:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180006aff;
L_180006aff:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006b03;
L_180006b03:
  if (!M.zf) goto L_180006b28; goto L_180006b05;
L_180006b05:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180006b0a;
L_180006b0a:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006b0e;
L_180006b0e:
  if (!M.zf) goto L_180006b28; goto L_180006b10;
L_180006b10:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180006b15;
L_180006b15:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006b19;
L_180006b19:
  if (!M.zf) goto L_180006b28; goto L_180006b1b;
L_180006b1b:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180006b1f;
L_180006b1f:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180006b22;
L_180006b22:
  if (M.zf) goto L_1800070a6; goto L_180006b28;
L_180006b28:
  R.rcx=uint64_t(M.read64((R.rsi+0x40ull))); goto L_180006b2c;
L_180006b2c:
  R.rdx=uint64_t(R.rbx); goto L_180006b2f;
L_180006b2f:
  goto L_180006b3d;
L_180006b31:
  R.rcx=uint64_t(M.read64((R.rsi+0x40ull))); goto L_180006b35;
L_180006b35:
  R.rdx=uint64_t(R.rbx); goto L_180006b38;
L_180006b38:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006b3b;
L_180006b3b:
  if (M.zf) goto L_180006b75; goto L_180006b3d;
L_180006b3d:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006b40;
L_180006b40:
  if (M.zf) goto L_180006b75; goto L_180006b42;
L_180006b42:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006b46;
L_180006b46:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006b4a;
L_180006b4a:
  if (!M.zf) goto L_180006b6c; goto L_180006b4c;
L_180006b4c:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006b50;
L_180006b50:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006b54;
L_180006b54:
  if (!M.zf) goto L_180006b6c; goto L_180006b56;
L_180006b56:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006b5a;
L_180006b5a:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006b5e;
L_180006b5e:
  if (!M.zf) goto L_180006b6c; goto L_180006b60;
L_180006b60:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006b63;
L_180006b63:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006b66;
L_180006b66:
  if (M.zf) goto L_1800070a6; goto L_180006b6c;
L_180006b6c:
  R.rcx=uint64_t(M.read64((R.rsi+0x10ull))); goto L_180006b70;
L_180006b70:
  R.rdx=uint64_t(R.rbx); goto L_180006b73;
L_180006b73:
  goto L_180006b81;
L_180006b75:
  R.rcx=uint64_t(M.read64((R.rsi+0x10ull))); goto L_180006b79;
L_180006b79:
  R.rdx=uint64_t(R.rbx); goto L_180006b7c;
L_180006b7c:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006b7f;
L_180006b7f:
  if (M.zf) goto L_180006bb8; goto L_180006b81;
L_180006b81:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006b84;
L_180006b84:
  if (M.zf) goto L_180006bb8; goto L_180006b86;
L_180006b86:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006b8a;
L_180006b8a:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006b8e;
L_180006b8e:
  if (!M.zf) goto L_180006bb0; goto L_180006b90;
L_180006b90:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006b94;
L_180006b94:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006b98;
L_180006b98:
  if (!M.zf) goto L_180006bb0; goto L_180006b9a;
L_180006b9a:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006b9e;
L_180006b9e:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006ba2;
L_180006ba2:
  if (!M.zf) goto L_180006bb0; goto L_180006ba4;
L_180006ba4:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006ba7;
L_180006ba7:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006baa;
L_180006baa:
  if (M.zf) goto L_1800070a6; goto L_180006bb0;
L_180006bb0:
  R.rcx=uint64_t(M.read64((R.rsi))); goto L_180006bb3;
L_180006bb3:
  R.rdx=uint64_t(R.rbx); goto L_180006bb6;
L_180006bb6:
  goto L_180006bc3;
L_180006bb8:
  R.rcx=uint64_t(M.read64((R.rsi))); goto L_180006bbb;
L_180006bbb:
  R.rdx=uint64_t(R.rbx); goto L_180006bbe;
L_180006bbe:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006bc1;
L_180006bc1:
  if (M.zf) goto L_180006bfb; goto L_180006bc3;
L_180006bc3:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006bc6;
L_180006bc6:
  if (M.zf) goto L_180006bfb; goto L_180006bc8;
L_180006bc8:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006bcc;
L_180006bcc:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006bd0;
L_180006bd0:
  if (!M.zf) goto L_180006bf2; goto L_180006bd2;
L_180006bd2:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006bd6;
L_180006bd6:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006bda;
L_180006bda:
  if (!M.zf) goto L_180006bf2; goto L_180006bdc;
L_180006bdc:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006be0;
L_180006be0:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006be4;
L_180006be4:
  if (!M.zf) goto L_180006bf2; goto L_180006be6;
L_180006be6:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006be9;
L_180006be9:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006bec;
L_180006bec:
  if (M.zf) goto L_1800070a6; goto L_180006bf2;
L_180006bf2:
  R.rcx=uint64_t(M.read64((R.rsi+0x18ull))); goto L_180006bf6;
L_180006bf6:
  R.rdx=uint64_t(R.rbx); goto L_180006bf9;
L_180006bf9:
  goto L_180006c07;
L_180006bfb:
  R.rcx=uint64_t(M.read64((R.rsi+0x18ull))); goto L_180006bff;
L_180006bff:
  R.rdx=uint64_t(R.rbx); goto L_180006c02;
L_180006c02:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006c05;
L_180006c05:
  if (M.zf) goto L_180006c3f; goto L_180006c07;
L_180006c07:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006c0a;
L_180006c0a:
  if (M.zf) goto L_180006c3f; goto L_180006c0c;
L_180006c0c:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006c10;
L_180006c10:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006c14;
L_180006c14:
  if (!M.zf) goto L_180006c36; goto L_180006c16;
L_180006c16:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006c1a;
L_180006c1a:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006c1e;
L_180006c1e:
  if (!M.zf) goto L_180006c36; goto L_180006c20;
L_180006c20:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006c24;
L_180006c24:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006c28;
L_180006c28:
  if (!M.zf) goto L_180006c36; goto L_180006c2a;
L_180006c2a:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006c2d;
L_180006c2d:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006c30;
L_180006c30:
  if (M.zf) goto L_1800070a6; goto L_180006c36;
L_180006c36:
  R.rcx=uint64_t(M.read64((R.rsi+0x28ull))); goto L_180006c3a;
L_180006c3a:
  R.rdx=uint64_t(R.rbx); goto L_180006c3d;
L_180006c3d:
  goto L_180006c4b;
L_180006c3f:
  R.rcx=uint64_t(M.read64((R.rsi+0x28ull))); goto L_180006c43;
L_180006c43:
  R.rdx=uint64_t(R.rbx); goto L_180006c46;
L_180006c46:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006c49;
L_180006c49:
  if (M.zf) goto L_180006c83; goto L_180006c4b;
L_180006c4b:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006c4e;
L_180006c4e:
  if (M.zf) goto L_180006c83; goto L_180006c50;
L_180006c50:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006c54;
L_180006c54:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006c58;
L_180006c58:
  if (!M.zf) goto L_180006c7a; goto L_180006c5a;
L_180006c5a:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006c5e;
L_180006c5e:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006c62;
L_180006c62:
  if (!M.zf) goto L_180006c7a; goto L_180006c64;
L_180006c64:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006c68;
L_180006c68:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006c6c;
L_180006c6c:
  if (!M.zf) goto L_180006c7a; goto L_180006c6e;
L_180006c6e:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006c71;
L_180006c71:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006c74;
L_180006c74:
  if (M.zf) goto L_1800070a6; goto L_180006c7a;
L_180006c7a:
  R.rcx=uint64_t(M.read64((R.rsi+0x8ull))); goto L_180006c7e;
L_180006c7e:
  R.rdx=uint64_t(R.rbx); goto L_180006c81;
L_180006c81:
  goto L_180006c8f;
L_180006c83:
  R.rcx=uint64_t(M.read64((R.rsi+0x8ull))); goto L_180006c87;
L_180006c87:
  R.rdx=uint64_t(R.rbx); goto L_180006c8a;
L_180006c8a:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006c8d;
L_180006c8d:
  if (M.zf) goto L_180006cc7; goto L_180006c8f;
L_180006c8f:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006c92;
L_180006c92:
  if (M.zf) goto L_180006cc7; goto L_180006c94;
L_180006c94:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006c98;
L_180006c98:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006c9c;
L_180006c9c:
  if (!M.zf) goto L_180006cbe; goto L_180006c9e;
L_180006c9e:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006ca2;
L_180006ca2:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006ca6;
L_180006ca6:
  if (!M.zf) goto L_180006cbe; goto L_180006ca8;
L_180006ca8:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006cac;
L_180006cac:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006cb0;
L_180006cb0:
  if (!M.zf) goto L_180006cbe; goto L_180006cb2;
L_180006cb2:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006cb5;
L_180006cb5:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006cb8;
L_180006cb8:
  if (M.zf) goto L_1800070a6; goto L_180006cbe;
L_180006cbe:
  R.rcx=uint64_t(M.read64((R.rsi+0x38ull))); goto L_180006cc2;
L_180006cc2:
  R.rdx=uint64_t(R.rbx); goto L_180006cc5;
L_180006cc5:
  goto L_180006cd7;
L_180006cc7:
  R.rcx=uint64_t(M.read64((R.rsi+0x38ull))); goto L_180006ccb;
L_180006ccb:
  R.rdx=uint64_t(R.rbx); goto L_180006cce;
L_180006cce:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006cd1;
L_180006cd1:
  if (M.zf) goto L_1800070a9; goto L_180006cd7;
L_180006cd7:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180006cda;
L_180006cda:
  if (M.zf) goto L_1800070a9; goto L_180006ce0;
L_180006ce0:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180006ce4;
L_180006ce4:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180006ce8;
L_180006ce8:
  if (!M.zf) goto L_1800070a9; goto L_180006cee;
L_180006cee:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180006cf2;
L_180006cf2:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_180006cf6;
L_180006cf6:
  if (!M.zf) goto L_1800070a9; goto L_180006cfc;
L_180006cfc:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180006d00;
L_180006d00:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180006d04;
L_180006d04:
  if (!M.zf) goto L_1800070a9; goto L_180006d0a;
L_180006d0a:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_180006d0d;
L_180006d0d:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_180006d10;
L_180006d10:
  if (!M.zf) goto L_1800070a9; goto L_180006d16;
L_180006d16:
  goto L_1800070a6;
L_180006d1b:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006d1e;
L_180006d1e:
  if (M.zf) goto L_180006d8a; goto L_180006d20;
L_180006d20:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180006d23;
L_180006d23:
  if (M.zf) goto L_180006d8a; goto L_180006d25;
L_180006d25:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180006d2a;
L_180006d2a:
  R.r9=uint32_t(uint32_t(R.r15)); goto L_180006d2d;
L_180006d2d:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006d31;
L_180006d31:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006d33;
L_180006d33:
  R.r9=uint32_t((uint32_t(R.r9))<<((7ull)&0x3f)); goto L_180006d37;
L_180006d37:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006d39;
L_180006d39:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006d3a;
L_180006d3a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006d3c;
L_180006d3c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006d3e;
L_180006d3e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180006d41;
L_180006d41:
  if (!M.zf&&(M.sf==M.of)) goto L_180006d8a; goto L_180006d43;
L_180006d43:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180006d48;
L_180006d48:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006d4c;
L_180006d4c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006d4e;
L_180006d4e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006d50;
L_180006d50:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006d51;
L_180006d51:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006d53;
L_180006d53:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006d55;
L_180006d55:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180006d58;
L_180006d58:
  if (!M.zf&&(M.sf==M.of)) goto L_180006d8a; goto L_180006d5a;
L_180006d5a:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180006d5f;
L_180006d5f:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006d63;
L_180006d63:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006d65;
L_180006d65:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006d67;
L_180006d67:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006d68;
L_180006d68:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006d6a;
L_180006d6a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006d6c;
L_180006d6c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180006d6f;
L_180006d6f:
  if (!M.zf&&(M.sf==M.of)) goto L_180006d8a; goto L_180006d71;
L_180006d71:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180006d75;
L_180006d75:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006d78;
L_180006d78:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006d7a;
L_180006d7a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006d7c;
L_180006d7c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006d7d;
L_180006d7d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006d7f;
L_180006d7f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006d81;
L_180006d81:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r9),32);
  goto L_180006d84;
L_180006d84:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006d8a;
L_180006d8a:
  R.r9=uint64_t(M.read64((R.rsi+0x40ull))); goto L_180006d8e;
L_180006d8e:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006d91;
L_180006d91:
  if (M.zf) goto L_180006dfd; goto L_180006d93;
L_180006d93:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006d96;
L_180006d96:
  if (M.zf) goto L_180006dfd; goto L_180006d98;
L_180006d98:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006d9d;
L_180006d9d:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006da0;
L_180006da0:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006da4;
L_180006da4:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006da6;
L_180006da6:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006daa;
L_180006daa:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006dac;
L_180006dac:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006dad;
L_180006dad:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006daf;
L_180006daf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006db1;
L_180006db1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006db4;
L_180006db4:
  if (!M.zf&&(M.sf==M.of)) goto L_180006dfd; goto L_180006db6;
L_180006db6:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006dbb;
L_180006dbb:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006dbf;
L_180006dbf:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006dc1;
L_180006dc1:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006dc3;
L_180006dc3:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006dc4;
L_180006dc4:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006dc6;
L_180006dc6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006dc8;
L_180006dc8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006dcb;
L_180006dcb:
  if (!M.zf&&(M.sf==M.of)) goto L_180006dfd; goto L_180006dcd;
L_180006dcd:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180006dd2;
L_180006dd2:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006dd6;
L_180006dd6:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006dd8;
L_180006dd8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006dda;
L_180006dda:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006ddb;
L_180006ddb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006ddd;
L_180006ddd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006ddf;
L_180006ddf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006de2;
L_180006de2:
  if (!M.zf&&(M.sf==M.of)) goto L_180006dfd; goto L_180006de4;
L_180006de4:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180006de8;
L_180006de8:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006deb;
L_180006deb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006ded;
L_180006ded:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006def;
L_180006def:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006df0;
L_180006df0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006df2;
L_180006df2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006df4;
L_180006df4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006df7;
L_180006df7:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006dfd;
L_180006dfd:
  R.r9=uint64_t(M.read64((R.rsi+0x10ull))); goto L_180006e01;
L_180006e01:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006e04;
L_180006e04:
  if (M.zf) goto L_180006e70; goto L_180006e06;
L_180006e06:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006e09;
L_180006e09:
  if (M.zf) goto L_180006e70; goto L_180006e0b;
L_180006e0b:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006e10;
L_180006e10:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006e13;
L_180006e13:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006e17;
L_180006e17:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006e19;
L_180006e19:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006e1d;
L_180006e1d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006e1f;
L_180006e1f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006e20;
L_180006e20:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006e22;
L_180006e22:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006e24;
L_180006e24:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006e27;
L_180006e27:
  if (!M.zf&&(M.sf==M.of)) goto L_180006e70; goto L_180006e29;
L_180006e29:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006e2e;
L_180006e2e:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006e32;
L_180006e32:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006e34;
L_180006e34:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006e36;
L_180006e36:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006e37;
L_180006e37:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006e39;
L_180006e39:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006e3b;
L_180006e3b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006e3e;
L_180006e3e:
  if (!M.zf&&(M.sf==M.of)) goto L_180006e70; goto L_180006e40;
L_180006e40:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180006e45;
L_180006e45:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006e49;
L_180006e49:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006e4b;
L_180006e4b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006e4d;
L_180006e4d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006e4e;
L_180006e4e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006e50;
L_180006e50:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006e52;
L_180006e52:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006e55;
L_180006e55:
  if (!M.zf&&(M.sf==M.of)) goto L_180006e70; goto L_180006e57;
L_180006e57:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180006e5b;
L_180006e5b:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006e5e;
L_180006e5e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006e60;
L_180006e60:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006e62;
L_180006e62:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006e63;
L_180006e63:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006e65;
L_180006e65:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006e67;
L_180006e67:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006e6a;
L_180006e6a:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006e70;
L_180006e70:
  R.r9=uint64_t(M.read64((R.rsi))); goto L_180006e73;
L_180006e73:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006e76;
L_180006e76:
  if (M.zf) goto L_180006ee2; goto L_180006e78;
L_180006e78:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006e7b;
L_180006e7b:
  if (M.zf) goto L_180006ee2; goto L_180006e7d;
L_180006e7d:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006e82;
L_180006e82:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006e85;
L_180006e85:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006e89;
L_180006e89:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006e8b;
L_180006e8b:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006e8f;
L_180006e8f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006e91;
L_180006e91:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006e92;
L_180006e92:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006e94;
L_180006e94:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006e96;
L_180006e96:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006e99;
L_180006e99:
  if (!M.zf&&(M.sf==M.of)) goto L_180006ee2; goto L_180006e9b;
L_180006e9b:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006ea0;
L_180006ea0:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006ea4;
L_180006ea4:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006ea6;
L_180006ea6:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006ea8;
L_180006ea8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006ea9;
L_180006ea9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006eab;
L_180006eab:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006ead;
L_180006ead:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006eb0;
L_180006eb0:
  if (!M.zf&&(M.sf==M.of)) goto L_180006ee2; goto L_180006eb2;
L_180006eb2:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180006eb7;
L_180006eb7:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006ebb;
L_180006ebb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006ebd;
L_180006ebd:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006ebf;
L_180006ebf:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006ec0;
L_180006ec0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006ec2;
L_180006ec2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006ec4;
L_180006ec4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006ec7;
L_180006ec7:
  if (!M.zf&&(M.sf==M.of)) goto L_180006ee2; goto L_180006ec9;
L_180006ec9:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180006ecd;
L_180006ecd:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006ed0;
L_180006ed0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006ed2;
L_180006ed2:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006ed4;
L_180006ed4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006ed5;
L_180006ed5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006ed7;
L_180006ed7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006ed9;
L_180006ed9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006edc;
L_180006edc:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006ee2;
L_180006ee2:
  R.r9=uint64_t(M.read64((R.rsi+0x18ull))); goto L_180006ee6;
L_180006ee6:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006ee9;
L_180006ee9:
  if (M.zf) goto L_180006f55; goto L_180006eeb;
L_180006eeb:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006eee;
L_180006eee:
  if (M.zf) goto L_180006f55; goto L_180006ef0;
L_180006ef0:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006ef5;
L_180006ef5:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006ef8;
L_180006ef8:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006efc;
L_180006efc:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006efe;
L_180006efe:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006f02;
L_180006f02:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f04;
L_180006f04:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f05;
L_180006f05:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f07;
L_180006f07:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f09;
L_180006f09:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f0c;
L_180006f0c:
  if (!M.zf&&(M.sf==M.of)) goto L_180006f55; goto L_180006f0e;
L_180006f0e:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006f13;
L_180006f13:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006f17;
L_180006f17:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006f19;
L_180006f19:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f1b;
L_180006f1b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f1c;
L_180006f1c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f1e;
L_180006f1e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f20;
L_180006f20:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f23;
L_180006f23:
  if (!M.zf&&(M.sf==M.of)) goto L_180006f55; goto L_180006f25;
L_180006f25:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180006f2a;
L_180006f2a:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006f2e;
L_180006f2e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006f30;
L_180006f30:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f32;
L_180006f32:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f33;
L_180006f33:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f35;
L_180006f35:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f37;
L_180006f37:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f3a;
L_180006f3a:
  if (!M.zf&&(M.sf==M.of)) goto L_180006f55; goto L_180006f3c;
L_180006f3c:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180006f40;
L_180006f40:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006f43;
L_180006f43:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006f45;
L_180006f45:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f47;
L_180006f47:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f48;
L_180006f48:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f4a;
L_180006f4a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f4c;
L_180006f4c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f4f;
L_180006f4f:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006f55;
L_180006f55:
  R.r9=uint64_t(M.read64((R.rsi+0x28ull))); goto L_180006f59;
L_180006f59:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006f5c;
L_180006f5c:
  if (M.zf) goto L_180006fc8; goto L_180006f5e;
L_180006f5e:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006f61;
L_180006f61:
  if (M.zf) goto L_180006fc8; goto L_180006f63;
L_180006f63:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006f68;
L_180006f68:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006f6b;
L_180006f6b:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006f6f;
L_180006f6f:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006f71;
L_180006f71:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006f75;
L_180006f75:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f77;
L_180006f77:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f78;
L_180006f78:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f7a;
L_180006f7a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f7c;
L_180006f7c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f7f;
L_180006f7f:
  if (!M.zf&&(M.sf==M.of)) goto L_180006fc8; goto L_180006f81;
L_180006f81:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006f86;
L_180006f86:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006f8a;
L_180006f8a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006f8c;
L_180006f8c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006f8e;
L_180006f8e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006f8f;
L_180006f8f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006f91;
L_180006f91:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006f93;
L_180006f93:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006f96;
L_180006f96:
  if (!M.zf&&(M.sf==M.of)) goto L_180006fc8; goto L_180006f98;
L_180006f98:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180006f9d;
L_180006f9d:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180006fa1;
L_180006fa1:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006fa3;
L_180006fa3:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006fa5;
L_180006fa5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006fa6;
L_180006fa6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006fa8;
L_180006fa8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006faa;
L_180006faa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006fad;
L_180006fad:
  if (!M.zf&&(M.sf==M.of)) goto L_180006fc8; goto L_180006faf;
L_180006faf:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180006fb3;
L_180006fb3:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180006fb6;
L_180006fb6:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006fb8;
L_180006fb8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006fba;
L_180006fba:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006fbb;
L_180006fbb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006fbd;
L_180006fbd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006fbf;
L_180006fbf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006fc2;
L_180006fc2:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180006fc8;
L_180006fc8:
  R.r9=uint64_t(M.read64((R.rsi+0x8ull))); goto L_180006fcc;
L_180006fcc:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180006fcf;
L_180006fcf:
  if (M.zf) goto L_180007037; goto L_180006fd1;
L_180006fd1:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180006fd4;
L_180006fd4:
  if (M.zf) goto L_180007037; goto L_180006fd6;
L_180006fd6:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180006fdb;
L_180006fdb:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180006fde;
L_180006fde:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180006fe2;
L_180006fe2:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006fe4;
L_180006fe4:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180006fe8;
L_180006fe8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180006fea;
L_180006fea:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180006feb;
L_180006feb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180006fed;
L_180006fed:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180006fef;
L_180006fef:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180006ff2;
L_180006ff2:
  if (!M.zf&&(M.sf==M.of)) goto L_180007037; goto L_180006ff4;
L_180006ff4:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180006ff9;
L_180006ff9:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180006ffd;
L_180006ffd:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180006fff;
L_180006fff:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007001;
L_180007001:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007002;
L_180007002:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007004;
L_180007004:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007006;
L_180007006:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007009;
L_180007009:
  if (!M.zf&&(M.sf==M.of)) goto L_180007037; goto L_18000700b;
L_18000700b:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180007010;
L_180007010:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180007014;
L_180007014:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007016;
L_180007016:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007018;
L_180007018:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007019;
L_180007019:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000701b;
L_18000701b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000701d;
L_18000701d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007020;
L_180007020:
  if (!M.zf&&(M.sf==M.of)) goto L_180007037; goto L_180007022;
L_180007022:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180007026;
L_180007026:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180007029;
L_180007029:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000702b;
L_18000702b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000702d;
L_18000702d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000702e;
L_18000702e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007030;
L_180007030:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007032;
L_180007032:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007035;
L_180007035:
  if (M.zf||(M.sf!=M.of)) goto L_1800070a6; goto L_180007037;
L_180007037:
  R.r9=uint64_t(M.read64((R.rsi+0x38ull))); goto L_18000703b;
L_18000703b:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000703e;
L_18000703e:
  if (M.zf) goto L_1800070a9; goto L_180007040;
L_180007040:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180007043;
L_180007043:
  if (M.zf) goto L_1800070a9; goto L_180007045;
L_180007045:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_18000704a;
L_18000704a:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_18000704d;
L_18000704d:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180007051;
L_180007051:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007053;
L_180007053:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180007057;
L_180007057:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007059;
L_180007059:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000705a;
L_18000705a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000705c;
L_18000705c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000705e;
L_18000705e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007061;
L_180007061:
  if (!M.zf&&(M.sf==M.of)) goto L_1800070a9; goto L_180007063;
L_180007063:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180007068;
L_180007068:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_18000706c;
L_18000706c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000706e;
L_18000706e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007070;
L_180007070:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007071;
L_180007071:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007073;
L_180007073:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007075;
L_180007075:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007078;
L_180007078:
  if (!M.zf&&(M.sf==M.of)) goto L_1800070a9; goto L_18000707a;
L_18000707a:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_18000707f;
L_18000707f:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180007083;
L_180007083:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007085;
L_180007085:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007087;
L_180007087:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007088;
L_180007088:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000708a;
L_18000708a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000708c;
L_18000708c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_18000708f;
L_18000708f:
  if (!M.zf&&(M.sf==M.of)) goto L_1800070a9; goto L_180007091;
L_180007091:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180007095;
L_180007095:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180007098;
L_180007098:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000709a;
L_18000709a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000709c;
L_18000709c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000709d;
L_18000709d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000709f;
L_18000709f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800070a1;
L_1800070a1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800070a4;
L_1800070a4:
  if (!M.zf&&(M.sf==M.of)) goto L_1800070a9; goto L_1800070a6;
L_1800070a6:
  T=(uint8_t(R.r10)) ^ (uint8_t(R.r10)); M.logicflags(T,8);
  R.r10=(R.r10&~0xffull)|(uint8_t(T));
  goto L_1800070a9;
L_1800070a9:
  R.rdx=uint64_t((0x1800070b0-0x70b0ull)); goto L_1800070b0;
L_1800070b0:
  T=(uint8_t(R.r10)) & (uint8_t(R.r10)); M.logicflags(T,8);
  goto L_1800070b3;
L_1800070b3:
  R.rdi=uint64_t(int64_t(int32_t(M.read32((R.rdx+(R.r14*4ull)+0xf050ull))))); goto L_1800070bb;
L_1800070bb:
  R.rax=uint32_t(1ull); goto L_1800070c0;
L_1800070c0:
  R.r13=uint64_t(int64_t(int32_t(M.read32((R.rdx+(R.r14*4ull)+0xf028ull))))); goto L_1800070c8;
L_1800070c8:
  R.r12=uint32_t(4ull); goto L_1800070ce;
L_1800070ce:
  R.r11=uint64_t(int64_t(int32_t(M.read32((R.rdx+(R.r14*4ull)+0xf078ull))))); goto L_1800070d6;
L_1800070d6:
  if(M.zf){R.r12=uint32_t(uint32_t(R.rax));} goto L_1800070da;
L_1800070da:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rdx+(R.r14*4ull)+0xf0a0ull))))); goto L_1800070e2;
L_1800070e2:
  M.write64((R.rsp+0x30ull), R.rax); goto L_1800070e7;
L_1800070e7:
  M.write32((R.rsp+0x80ull), uint32_t(R.rdi)); goto L_1800070ee;
L_1800070ee:
  R.rcx=uint32_t(M.read32((R.rdx+(R.rax*4ull)+0xf050ull))); goto L_1800070f5;
L_1800070f5:
  R.rax=uint32_t(M.read32((R.rdx+(R.rax*4ull)+0xf078ull))); goto L_1800070fc;
L_1800070fc:
  M.write32((R.rsp+0x28ull), uint32_t(R.rax)); goto L_180007100;
L_180007100:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rdx+(R.r14*4ull)+0xf000ull))))); goto L_180007108;
L_180007108:
  M.write32((R.rsp+0x98ull), uint32_t(R.rcx)); goto L_18000710f;
L_18000710f:
  R.r14=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007113;
L_180007113:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180007116;
L_180007116:
  if (!M.zf) goto L_1800072b4; goto L_18000711c;
L_18000711c:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000711f;
L_18000711f:
  if (M.zf) goto L_18000719b; goto L_180007121;
L_180007121:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180007124;
L_180007124:
  if (M.zf) goto L_18000719b; goto L_180007126;
L_180007126:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_18000712b;
L_18000712b:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_18000712f;
L_18000712f:
  if (!M.zf) goto L_18000718c; goto L_180007131;
L_180007131:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_180007136;
L_180007136:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_18000713a;
L_18000713a:
  if (!M.zf) goto L_18000718c; goto L_18000713c;
L_18000713c:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180007141;
L_180007141:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180007145;
L_180007145:
  if (!M.zf) goto L_18000718c; goto L_180007147;
L_180007147:
  R.rax=uint32_t(M.read16((R.r14))); goto L_18000714b;
L_18000714b:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_18000714e;
L_18000714e:
  if (!M.zf) goto L_18000718c; goto L_180007150;
L_180007150:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rdi*8ull)))); goto L_180007154;
L_180007154:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_180007157;
L_180007157:
  if (M.zf) goto L_18000718c; goto L_180007159;
L_180007159:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_18000715c;
L_18000715c:
  if (M.zf) goto L_18000718c; goto L_18000715e;
L_18000715e:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_180007162;
L_180007162:
  T=M.subflags(M.read16((R.rbp+0x2ull)),uint16_t(R.rax),16);
  goto L_180007166;
L_180007166:
  if (!M.zf) goto L_18000718c; goto L_180007168;
L_180007168:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_18000716c;
L_18000716c:
  T=M.subflags(M.read16((R.rbp+0x6ull)),uint16_t(R.rax),16);
  goto L_180007170;
L_180007170:
  if (!M.zf) goto L_18000718c; goto L_180007172;
L_180007172:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180007176;
L_180007176:
  T=M.subflags(M.read16((R.rbp+0x4ull)),uint16_t(R.rax),16);
  goto L_18000717a;
L_18000717a:
  if (!M.zf) goto L_18000718c; goto L_18000717c;
L_18000717c:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_18000717f;
L_18000717f:
  T=M.subflags(M.read16((R.rbp)),uint16_t(R.rax),16);
  goto L_180007183;
L_180007183:
  if (!M.zf) goto L_18000718c; goto L_180007185;
L_180007185:
  T=(uint32_t(R.rdi)) ^ (uint32_t(R.rdi)); M.logicflags(T,32);
  R.rdi=uint32_t(T);
  goto L_180007187;
L_180007187:
  goto L_1800074f2;
L_18000718c:
  R.r8=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_180007190;
L_180007190:
  R.rdx=uint64_t(R.rbx); goto L_180007193;
L_180007193:
  R.r9=uint64_t(R.r8); goto L_180007196;
L_180007196:
  R.rcx=uint64_t(R.r8); goto L_180007199;
L_180007199:
  goto L_1800071ad;
L_18000719b:
  R.r8=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_18000719f;
L_18000719f:
  R.rdx=uint64_t(R.rbx); goto L_1800071a2;
L_1800071a2:
  R.r9=uint64_t(R.r8); goto L_1800071a5;
L_1800071a5:
  R.rcx=uint64_t(R.r8); goto L_1800071a8;
L_1800071a8:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800071ab;
L_1800071ab:
  if (M.zf) goto L_180007219; goto L_1800071ad;
L_1800071ad:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_1800071b0;
L_1800071b0:
  if (M.zf) goto L_180007219; goto L_1800071b2;
L_1800071b2:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_1800071b6;
L_1800071b6:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_1800071ba;
L_1800071ba:
  if (!M.zf) goto L_180007255; goto L_1800071c0;
L_1800071c0:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_1800071c4;
L_1800071c4:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_1800071c8;
L_1800071c8:
  if (!M.zf) goto L_180007255; goto L_1800071ce;
L_1800071ce:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_1800071d2;
L_1800071d2:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_1800071d6;
L_1800071d6:
  if (!M.zf) goto L_180007255; goto L_1800071d8;
L_1800071d8:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_1800071db;
L_1800071db:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_1800071de;
L_1800071de:
  if (!M.zf) goto L_180007255; goto L_1800071e0;
L_1800071e0:
  R.rcx=uint64_t(M.read64((R.rsi+(R.r11*8ull)))); goto L_1800071e4;
L_1800071e4:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_1800071e7;
L_1800071e7:
  if (M.zf) goto L_180007219; goto L_1800071e9;
L_1800071e9:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_1800071ec;
L_1800071ec:
  if (M.zf) goto L_180007219; goto L_1800071ee;
L_1800071ee:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_1800071f2;
L_1800071f2:
  T=M.subflags(M.read16((R.rbp+0x2ull)),uint16_t(R.rax),16);
  goto L_1800071f6;
L_1800071f6:
  if (!M.zf) goto L_180007219; goto L_1800071f8;
L_1800071f8:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_1800071fc;
L_1800071fc:
  T=M.subflags(M.read16((R.rbp+0x6ull)),uint16_t(R.rax),16);
  goto L_180007200;
L_180007200:
  if (!M.zf) goto L_180007219; goto L_180007202;
L_180007202:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180007206;
L_180007206:
  T=M.subflags(M.read16((R.rbp+0x4ull)),uint16_t(R.rax),16);
  goto L_18000720a;
L_18000720a:
  if (!M.zf) goto L_180007219; goto L_18000720c;
L_18000720c:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_18000720f;
L_18000720f:
  T=M.subflags(M.read16((R.rbp)),uint16_t(R.rax),16);
  goto L_180007213;
L_180007213:
  if (M.zf) goto L_1800074e7; goto L_180007219;
L_180007219:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rdi*8ull)))); goto L_18000721d;
L_18000721d:
  R.rdx=uint64_t(R.rbx); goto L_180007220;
L_180007220:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007223;
L_180007223:
  if (M.zf) goto L_18000725e; goto L_180007225;
L_180007225:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180007228;
L_180007228:
  if (M.zf) goto L_18000725e; goto L_18000722a;
L_18000722a:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_18000722e;
L_18000722e:
  T=M.subflags(M.read16((R.rdx+0x2ull)),uint16_t(R.rax),16);
  goto L_180007232;
L_180007232:
  if (!M.zf) goto L_18000725e; goto L_180007234;
L_180007234:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180007238;
L_180007238:
  T=M.subflags(M.read16((R.rdx+0x6ull)),uint16_t(R.rax),16);
  goto L_18000723c;
L_18000723c:
  if (!M.zf) goto L_18000725e; goto L_18000723e;
L_18000723e:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180007242;
L_180007242:
  T=M.subflags(M.read16((R.rdx+0x4ull)),uint16_t(R.rax),16);
  goto L_180007246;
L_180007246:
  if (!M.zf) goto L_18000725e; goto L_180007248;
L_180007248:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_18000724b;
L_18000724b:
  T=M.subflags(M.read16((R.rdx)),uint16_t(R.rax),16);
  goto L_18000724e;
L_18000724e:
  if (!M.zf) goto L_18000725e; goto L_180007250;
L_180007250:
  R.r10=(R.r10&~0xffull)|(uint8_t(1ull)); goto L_180007253;
L_180007253:
  goto L_180007261;
L_180007255:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rdi*8ull)))); goto L_180007259;
L_180007259:
  R.rdx=uint64_t(R.rbx); goto L_18000725c;
L_18000725c:
  goto L_180007225;
L_18000725e:
  T=(uint8_t(R.r10)) ^ (uint8_t(R.r10)); M.logicflags(T,8);
  R.r10=(R.r10&~0xffull)|(uint8_t(T));
  goto L_180007261;
L_180007261:
  R.rcx=uint64_t(M.read64((R.rsi+(R.r11*8ull)))); goto L_180007265;
L_180007265:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007268;
L_180007268:
  if (M.zf) goto L_180007ebf; goto L_18000726e;
L_18000726e:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180007271;
L_180007271:
  if (M.zf) goto L_180007ebf; goto L_180007277;
L_180007277:
  R.rax=uint32_t(M.read16((R.rcx+0x2ull))); goto L_18000727b;
L_18000727b:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_18000727f;
L_18000727f:
  if (!M.zf) goto L_180007ebf; goto L_180007285;
L_180007285:
  R.rax=uint32_t(M.read16((R.rcx+0x6ull))); goto L_180007289;
L_180007289:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_18000728d;
L_18000728d:
  if (!M.zf) goto L_180007ebf; goto L_180007293;
L_180007293:
  R.rax=uint32_t(M.read16((R.rcx+0x4ull))); goto L_180007297;
L_180007297:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_18000729b;
L_18000729b:
  if (!M.zf) goto L_180007ebf; goto L_1800072a1;
L_1800072a1:
  R.rax=uint32_t(M.read16((R.rcx))); goto L_1800072a4;
L_1800072a4:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_1800072a7;
L_1800072a7:
  if (!M.zf) goto L_180007ebf; goto L_1800072ad;
L_1800072ad:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_1800072af;
L_1800072af:
  goto L_180007ec1;
L_1800072b4:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800072b7;
L_1800072b7:
  if (M.zf) goto L_1800073b9; goto L_1800072bd;
L_1800072bd:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_1800072c0;
L_1800072c0:
  if (M.zf) goto L_1800073b9; goto L_1800072c6;
L_1800072c6:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_1800072cb;
L_1800072cb:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_1800072ce;
L_1800072ce:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_1800072d2;
L_1800072d2:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800072d4;
L_1800072d4:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_1800072d8;
L_1800072d8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800072da;
L_1800072da:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800072db;
L_1800072db:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800072dd;
L_1800072dd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800072df;
L_1800072df:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800072e2;
L_1800072e2:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_1800072e8;
L_1800072e8:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_1800072ed;
L_1800072ed:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_1800072f1;
L_1800072f1:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800072f3;
L_1800072f3:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800072f5;
L_1800072f5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800072f6;
L_1800072f6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800072f8;
L_1800072f8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800072fa;
L_1800072fa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800072fd;
L_1800072fd:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_180007303;
L_180007303:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180007308;
L_180007308:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_18000730c;
L_18000730c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000730e;
L_18000730e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007310;
L_180007310:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007311;
L_180007311:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007313;
L_180007313:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007315;
L_180007315:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007318;
L_180007318:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_18000731e;
L_18000731e:
  R.rax=uint32_t(M.read16((R.r14))); goto L_180007322;
L_180007322:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180007325;
L_180007325:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007327;
L_180007327:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007329;
L_180007329:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000732a;
L_18000732a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000732c;
L_18000732c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000732e;
L_18000732e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007331;
L_180007331:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_180007333;
L_180007333:
  R.r9=uint64_t(M.read64((R.rsi+(R.rdi*8ull)))); goto L_180007337;
L_180007337:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_18000733a;
L_18000733a:
  if (M.zf) goto L_1800073aa; goto L_18000733c;
L_18000733c:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_18000733f;
L_18000733f:
  if (M.zf) goto L_1800073aa; goto L_180007341;
L_180007341:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180007346;
L_180007346:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180007349;
L_180007349:
  R.rcx=uint32_t(M.read16((R.rbp+0x2ull))); goto L_18000734d;
L_18000734d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000734f;
L_18000734f:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180007353;
L_180007353:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007355;
L_180007355:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007356;
L_180007356:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007358;
L_180007358:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000735a;
L_18000735a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_18000735d;
L_18000735d:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_18000735f;
L_18000735f:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180007364;
L_180007364:
  R.rcx=uint32_t(M.read16((R.rbp+0x6ull))); goto L_180007368;
L_180007368:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000736a;
L_18000736a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000736c;
L_18000736c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000736d;
L_18000736d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000736f;
L_18000736f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007371;
L_180007371:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007374;
L_180007374:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_180007376;
L_180007376:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_18000737b;
L_18000737b:
  R.rcx=uint32_t(M.read16((R.rbp+0x4ull))); goto L_18000737f;
L_18000737f:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007381;
L_180007381:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007383;
L_180007383:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007384;
L_180007384:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007386;
L_180007386:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007388;
L_180007388:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_18000738b;
L_18000738b:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_18000738d;
L_18000738d:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180007391;
L_180007391:
  R.rcx=uint32_t(M.read16((R.rbp))); goto L_180007395;
L_180007395:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007397;
L_180007397:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007399;
L_180007399:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000739a;
L_18000739a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000739c;
L_18000739c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000739e;
L_18000739e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800073a1;
L_1800073a1:
  if (!M.zf&&(M.sf==M.of)) goto L_1800073aa; goto L_1800073a3;
L_1800073a3:
  T=(uint32_t(R.rdi)) ^ (uint32_t(R.rdi)); M.logicflags(T,32);
  R.rdi=uint32_t(T);
  goto L_1800073a5;
L_1800073a5:
  goto L_1800074f2;
L_1800073aa:
  R.r8=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_1800073ae;
L_1800073ae:
  R.r11=uint64_t(R.rbx); goto L_1800073b1;
L_1800073b1:
  R.r9=uint64_t(R.r8); goto L_1800073b4;
L_1800073b4:
  R.r10=uint64_t(R.r8); goto L_1800073b7;
L_1800073b7:
  goto L_1800073cf;
L_1800073b9:
  R.r8=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_1800073bd;
L_1800073bd:
  R.r11=uint64_t(R.rbx); goto L_1800073c0;
L_1800073c0:
  R.r9=uint64_t(R.r8); goto L_1800073c3;
L_1800073c3:
  R.r10=uint64_t(R.r8); goto L_1800073c6;
L_1800073c6:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800073c9;
L_1800073c9:
  if (M.zf) goto L_180007d93; goto L_1800073cf;
L_1800073cf:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_1800073d2;
L_1800073d2:
  if (M.zf) goto L_180007d93; goto L_1800073d8;
L_1800073d8:
  R.rax=uint32_t(M.read16((R.r10+0x2ull))); goto L_1800073dd;
L_1800073dd:
  R.rdi=uint32_t(uint32_t(R.r15)); goto L_1800073e0;
L_1800073e0:
  R.rcx=uint32_t(M.read16((R.r11+0x2ull))); goto L_1800073e5;
L_1800073e5:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800073e7;
L_1800073e7:
  R.rdi=uint32_t((uint32_t(R.rdi))<<((7ull)&0x3f)); goto L_1800073ea;
L_1800073ea:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800073ec;
L_1800073ec:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800073ed;
L_1800073ed:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800073ef;
L_1800073ef:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800073f1;
L_1800073f1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800073f3;
L_1800073f3:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d73; goto L_1800073f9;
L_1800073f9:
  R.rax=uint32_t(M.read16((R.r10+0x6ull))); goto L_1800073fe;
L_1800073fe:
  R.rcx=uint32_t(M.read16((R.r11+0x6ull))); goto L_180007403;
L_180007403:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007405;
L_180007405:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007407;
L_180007407:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007408;
L_180007408:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000740a;
L_18000740a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000740c;
L_18000740c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000740e;
L_18000740e:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d73; goto L_180007414;
L_180007414:
  R.rax=uint32_t(M.read16((R.r10+0x4ull))); goto L_180007419;
L_180007419:
  R.rcx=uint32_t(M.read16((R.r11+0x4ull))); goto L_18000741e;
L_18000741e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007420;
L_180007420:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007422;
L_180007422:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007423;
L_180007423:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007425;
L_180007425:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007427;
L_180007427:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007429;
L_180007429:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d73; goto L_18000742f;
L_18000742f:
  R.rax=uint32_t(M.read16((R.r10))); goto L_180007433;
L_180007433:
  R.rcx=uint32_t(M.read16((R.r11))); goto L_180007437;
L_180007437:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007439;
L_180007439:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000743b;
L_18000743b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000743c;
L_18000743c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000743e;
L_18000743e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007440;
L_180007440:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007442;
L_180007442:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d73; goto L_180007448;
L_180007448:
  R.rdi=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007450;
L_180007450:
  R.rcx=uint64_t((0x180007457-0x7457ull)); goto L_180007457;
L_180007457:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rdi*4ull)+0xf078ull))))); goto L_18000745f;
L_18000745f:
  R.r11=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007463;
L_180007463:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_180007466;
L_180007466:
  if (M.zf) goto L_180007d65; goto L_18000746c;
L_18000746c:
  T=(R.r11) & (R.r11); M.logicflags(T,64);
  goto L_18000746f;
L_18000746f:
  if (M.zf) goto L_180007d65; goto L_180007475;
L_180007475:
  R.rax=uint32_t(M.read16((R.r11+0x2ull))); goto L_18000747a;
L_18000747a:
  R.r10=uint32_t(uint32_t(R.r15)); goto L_18000747d;
L_18000747d:
  R.rcx=uint32_t(M.read16((R.rbp+0x2ull))); goto L_180007481;
L_180007481:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007483;
L_180007483:
  R.r10=uint32_t((uint32_t(R.r10))<<((7ull)&0x3f)); goto L_180007487;
L_180007487:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007489;
L_180007489:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000748a;
L_18000748a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000748c;
L_18000748c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000748e;
L_18000748e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_180007491;
L_180007491:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d5e; goto L_180007497;
L_180007497:
  R.rax=uint32_t(M.read16((R.r11+0x6ull))); goto L_18000749c;
L_18000749c:
  R.rcx=uint32_t(M.read16((R.rbp+0x6ull))); goto L_1800074a0;
L_1800074a0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800074a2;
L_1800074a2:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800074a4;
L_1800074a4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800074a5;
L_1800074a5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800074a7;
L_1800074a7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800074a9;
L_1800074a9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800074ac;
L_1800074ac:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d5e; goto L_1800074b2;
L_1800074b2:
  R.rax=uint32_t(M.read16((R.r11+0x4ull))); goto L_1800074b7;
L_1800074b7:
  R.rcx=uint32_t(M.read16((R.rbp+0x4ull))); goto L_1800074bb;
L_1800074bb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800074bd;
L_1800074bd:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800074bf;
L_1800074bf:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800074c0;
L_1800074c0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800074c2;
L_1800074c2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800074c4;
L_1800074c4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800074c7;
L_1800074c7:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d5e; goto L_1800074cd;
L_1800074cd:
  R.rax=uint32_t(M.read16((R.r11))); goto L_1800074d1;
L_1800074d1:
  R.rcx=uint32_t(M.read16((R.rbp))); goto L_1800074d5;
L_1800074d5:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800074d7;
L_1800074d7:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800074d9;
L_1800074d9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800074da;
L_1800074da:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800074dc;
L_1800074dc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800074de;
L_1800074de:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800074e1;
L_1800074e1:
  if (!M.zf&&(M.sf==M.of)) goto L_180007d5e; goto L_1800074e7;
L_1800074e7:
  T=(uint32_t(R.rdi)) ^ (uint32_t(R.rdi)); M.logicflags(T,32);
  R.rdi=uint32_t(T);
  goto L_1800074e9;
L_1800074e9:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_1800074ec;
L_1800074ec:
  if (M.zf) goto L_18000803f; goto L_1800074f2;
L_1800074f2:
  R.r12=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_1800074f6;
L_1800074f6:
  T=(R.r12) & (R.r12); M.logicflags(T,64);
  goto L_1800074f9;
L_1800074f9:
  if (M.zf) goto L_18000803f; goto L_1800074ff;
L_1800074ff:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_180007502;
L_180007502:
  if (M.zf) goto L_18000803f; goto L_180007508;
L_180007508:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000750b;
L_18000750b:
  if (M.zf) goto L_1800078b3; goto L_180007511;
L_180007511:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180007514;
L_180007514:
  if (!M.zf) goto L_18000759f; goto L_18000751a;
L_18000751a:
  R.rdx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_18000751e;
L_18000751e:
  T=M.subflags(uint16_t(R.rdx),M.read16((R.r14+0x2ull)),16);
  goto L_180007523;
L_180007523:
  if (!M.zf) goto L_18000758c; goto L_180007525;
L_180007525:
  R.r8=uint32_t(M.read16((R.rbx+0x6ull))); goto L_18000752a;
L_18000752a:
  T=M.subflags(uint16_t(R.r8),M.read16((R.r14+0x6ull)),16);
  goto L_18000752f;
L_18000752f:
  if (!M.zf) goto L_18000758c; goto L_180007531;
L_180007531:
  R.r9=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180007536;
L_180007536:
  T=M.subflags(uint16_t(R.r9),M.read16((R.r14+0x4ull)),16);
  goto L_18000753b;
L_18000753b:
  if (!M.zf) goto L_18000758c; goto L_18000753d;
L_18000753d:
  R.r11=uint32_t(M.read16((R.rbx))); goto L_180007541;
L_180007541:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r14)),16);
  goto L_180007545;
L_180007545:
  if (!M.zf) goto L_18000758c; goto L_180007547;
L_180007547:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_18000754f;
L_18000754f:
  R.rcx=uint64_t((0x180007556-0x7556ull)); goto L_180007556;
L_180007556:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_18000755e;
L_18000755e:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007562;
L_180007562:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180007565;
L_180007565:
  if (M.zf) goto L_18000758c; goto L_180007567;
L_180007567:
  T=M.subflags(uint16_t(R.rdx),M.read16((R.rcx+0x2ull)),16);
  goto L_18000756b;
L_18000756b:
  if (!M.zf) goto L_18000758c; goto L_18000756d;
L_18000756d:
  T=M.subflags(uint16_t(R.r8),M.read16((R.rcx+0x6ull)),16);
  goto L_180007572;
L_180007572:
  if (!M.zf) goto L_18000758c; goto L_180007574;
L_180007574:
  T=M.subflags(uint16_t(R.r9),M.read16((R.rcx+0x4ull)),16);
  goto L_180007579;
L_180007579:
  if (!M.zf) goto L_18000758c; goto L_18000757b;
L_18000757b:
  T=M.subflags(uint16_t(R.r11),M.read16((R.rcx)),16);
  goto L_18000757f;
L_18000757f:
  if (!M.zf) goto L_18000758c; goto L_180007581;
L_180007581:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007584;
L_180007584:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_180007587;
L_180007587:
  goto L_1800076aa;
L_18000758c:
  R.r13=uint32_t(M.read32((R.rsp+0x80ull))); goto L_180007594;
L_180007594:
  R.r9=uint64_t(R.r12); goto L_180007597;
L_180007597:
  R.r8=uint64_t(R.rbx); goto L_18000759a;
L_18000759a:
  goto L_1800076de;
L_18000759f:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_1800075a4;
L_1800075a4:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_1800075a7;
L_1800075a7:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_1800075ab;
L_1800075ab:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800075ad;
L_1800075ad:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_1800075b1;
L_1800075b1:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800075b3;
L_1800075b3:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800075b4;
L_1800075b4:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800075b6;
L_1800075b6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800075b8;
L_1800075b8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800075bb;
L_1800075bb:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_1800075c1;
L_1800075c1:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_1800075c6;
L_1800075c6:
  R.r9=uint32_t(M.read16((R.rbx+0x6ull))); goto L_1800075cb;
L_1800075cb:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_1800075ce;
L_1800075ce:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800075d0;
L_1800075d0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800075d2;
L_1800075d2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800075d3;
L_1800075d3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800075d5;
L_1800075d5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800075d7;
L_1800075d7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800075da;
L_1800075da:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_1800075e0;
L_1800075e0:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_1800075e5;
L_1800075e5:
  R.r11=uint32_t(M.read16((R.rbx+0x4ull))); goto L_1800075ea;
L_1800075ea:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_1800075ed;
L_1800075ed:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800075ef;
L_1800075ef:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800075f1;
L_1800075f1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800075f2;
L_1800075f2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800075f4;
L_1800075f4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800075f6;
L_1800075f6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_1800075f9;
L_1800075f9:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_1800075ff;
L_1800075ff:
  R.rax=uint32_t(M.read16((R.r14))); goto L_180007603;
L_180007603:
  R.r13=uint32_t(M.read16((R.rbx))); goto L_180007607;
L_180007607:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_18000760a;
L_18000760a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000760c;
L_18000760c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000760e;
L_18000760e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000760f;
L_18000760f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007611;
L_180007611:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007613;
L_180007613:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007616;
L_180007616:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_18000761c;
L_18000761c:
  R.rbp=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007624;
L_180007624:
  R.rax=uint64_t((0x18000762b-0x762bull)); goto L_18000762b;
L_18000762b:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rax+(R.rbp*4ull)+0xf078ull))))); goto L_180007633;
L_180007633:
  R.r8=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007637;
L_180007637:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000763a;
L_18000763a:
  if (M.zf) goto L_18000776c; goto L_180007640;
L_180007640:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007645;
L_180007645:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007648;
L_180007648:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_18000764c;
L_18000764c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000764e;
L_18000764e:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_180007651;
L_180007651:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007653;
L_180007653:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007654;
L_180007654:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007656;
L_180007656:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007658;
L_180007658:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_18000765a;
L_18000765a:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_180007660;
L_180007660:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007665;
L_180007665:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_180007668;
L_180007668:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000766a;
L_18000766a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000766c;
L_18000766c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000766d;
L_18000766d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000766f;
L_18000766f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007671;
L_180007671:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007673;
L_180007673:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_180007679;
L_180007679:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_18000767e;
L_18000767e:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180007681;
L_180007681:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007683;
L_180007683:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007685;
L_180007685:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007686;
L_180007686:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007688;
L_180007688:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000768a;
L_18000768a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_18000768c;
L_18000768c:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_180007692;
L_180007692:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007696;
L_180007696:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180007699;
L_180007699:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000769b;
L_18000769b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000769d;
L_18000769d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000769e;
L_18000769e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800076a0;
L_1800076a0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800076a2;
L_1800076a2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_1800076a4;
L_1800076a4:
  if (!M.zf&&(M.sf==M.of)) goto L_180007774; goto L_1800076aa;
L_1800076aa:
  R.r13=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x80ull))))); goto L_1800076b2;
L_1800076b2:
  R.rdx=uint64_t(R.rbx); goto L_1800076b5;
L_1800076b5:
  R.rcx=uint64_t(M.read64((R.rsi+(R.r13*8ull)))); goto L_1800076b9;
L_1800076b9:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_1800076be;
L_1800076be:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_1800076c0;
L_1800076c0:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078ae; goto L_1800076c6;
L_1800076c6:
  R.r9=uint64_t(R.r12); goto L_1800076c9;
L_1800076c9:
  R.r8=uint64_t(R.rbx); goto L_1800076cc;
L_1800076cc:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_1800076cf;
L_1800076cf:
  if (!M.zf) goto L_180007761; goto L_1800076d5;
L_1800076d5:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800076d8;
L_1800076d8:
  if (M.zf) goto L_1800078b3; goto L_1800076de;
L_1800076de:
  R.r10=uint32_t(M.read16((R.r8+0x2ull))); goto L_1800076e3;
L_1800076e3:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r9+0x2ull)),16);
  goto L_1800076e8;
L_1800076e8:
  if (!M.zf) goto L_1800078b3; goto L_1800076ee;
L_1800076ee:
  R.r11=uint32_t(M.read16((R.r8+0x6ull))); goto L_1800076f3;
L_1800076f3:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r9+0x6ull)),16);
  goto L_1800076f8;
L_1800076f8:
  if (!M.zf) goto L_1800078b3; goto L_1800076fe;
L_1800076fe:
  R.rbp=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007703;
L_180007703:
  T=M.subflags(uint16_t(R.rbp),M.read16((R.r9+0x4ull)),16);
  goto L_180007708;
L_180007708:
  if (!M.zf) goto L_1800078b3; goto L_18000770e;
L_18000770e:
  R.r8=uint32_t(M.read16((R.r8))); goto L_180007712;
L_180007712:
  T=M.subflags(uint16_t(R.r8),M.read16((R.r9)),16);
  goto L_180007716;
L_180007716:
  if (!M.zf) goto L_1800078b3; goto L_18000771c;
L_18000771c:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.r13)))); goto L_18000771f;
L_18000771f:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007723;
L_180007723:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180007726;
L_180007726:
  if (M.zf) goto L_1800078b3; goto L_18000772c;
L_18000772c:
  T=M.subflags(uint16_t(R.r10),M.read16((R.rcx+0x2ull)),16);
  goto L_180007731;
L_180007731:
  if (!M.zf) goto L_1800078b3; goto L_180007737;
L_180007737:
  T=M.subflags(uint16_t(R.r11),M.read16((R.rcx+0x6ull)),16);
  goto L_18000773c;
L_18000773c:
  if (!M.zf) goto L_1800078b3; goto L_180007742;
L_180007742:
  T=M.subflags(uint16_t(R.rbp),M.read16((R.rcx+0x4ull)),16);
  goto L_180007746;
L_180007746:
  if (!M.zf) goto L_1800078b3; goto L_18000774c;
L_18000774c:
  T=M.subflags(uint16_t(R.r8),M.read16((R.rcx)),16);
  goto L_180007750;
L_180007750:
  if (!M.zf) goto L_1800078b3; goto L_180007756;
L_180007756:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007759;
L_180007759:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_18000775c;
L_18000775c:
  goto L_180007887;
L_180007761:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007764;
L_180007764:
  if (M.zf) goto L_1800078b3; goto L_18000776a;
L_18000776a:
  goto L_18000777a;
L_18000776c:
  R.r9=uint64_t(R.r12); goto L_18000776f;
L_18000776f:
  R.r8=uint64_t(R.rbx); goto L_180007772;
L_180007772:
  goto L_180007782;
L_180007774:
  R.r8=uint64_t(R.rbx); goto L_180007777;
L_180007777:
  R.r9=uint64_t(R.r12); goto L_18000777a;
L_18000777a:
  R.rbp=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007782;
L_180007782:
  R.rcx=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007787;
L_180007787:
  R.r10=uint32_t(uint32_t(R.r15)); goto L_18000778a;
L_18000778a:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_18000778f;
L_18000778f:
  M.write32((R.rsp+0x80ull), uint32_t(R.rcx)); goto L_180007796;
L_180007796:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007798;
L_180007798:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000779a;
L_18000779a:
  R.r10=uint32_t((uint32_t(R.r10))<<((7ull)&0x3f)); goto L_18000779e;
L_18000779e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000779f;
L_18000779f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800077a1;
L_1800077a1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800077a3;
L_1800077a3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800077a6;
L_1800077a6:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_1800077ac;
L_1800077ac:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_1800077b1;
L_1800077b1:
  R.r13=uint32_t(M.read16((R.r8+0x6ull))); goto L_1800077b6;
L_1800077b6:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_1800077b9;
L_1800077b9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800077bb;
L_1800077bb:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800077bd;
L_1800077bd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800077be;
L_1800077be:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800077c0;
L_1800077c0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800077c2;
L_1800077c2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800077c5;
L_1800077c5:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_1800077cb;
L_1800077cb:
  R.rcx=uint32_t(M.read16((R.r8+0x4ull))); goto L_1800077d0;
L_1800077d0:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_1800077d5;
L_1800077d5:
  M.write32((R.rsp+0x20ull), uint32_t(R.rcx)); goto L_1800077d9;
L_1800077d9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800077db;
L_1800077db:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800077dd;
L_1800077dd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800077de;
L_1800077de:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800077e0;
L_1800077e0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800077e2;
L_1800077e2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_1800077e5;
L_1800077e5:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_1800077eb;
L_1800077eb:
  R.rcx=uint32_t(M.read16((R.r8))); goto L_1800077ef;
L_1800077ef:
  R.rax=uint32_t(M.read16((R.r9))); goto L_1800077f3;
L_1800077f3:
  M.write32((R.rsp+0x24ull), uint32_t(R.rcx)); goto L_1800077f7;
L_1800077f7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800077f9;
L_1800077f9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800077fb;
L_1800077fb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800077fc;
L_1800077fc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800077fe;
L_1800077fe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007800;
L_180007800:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r10),32);
  goto L_180007803;
L_180007803:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_180007809;
L_180007809:
  R.rax=uint64_t((0x180007810-0x7810ull)); goto L_180007810;
L_180007810:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rax+(R.rbp*4ull)+0xf050ull))))); goto L_180007818;
L_180007818:
  R.r8=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_18000781c;
L_18000781c:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000781f;
L_18000781f:
  if (M.zf) goto L_1800078b3; goto L_180007825;
L_180007825:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_18000782a;
L_18000782a:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_18000782d;
L_18000782d:
  R.rcx=uint32_t(M.read16((R.rsp+0x80ull))); goto L_180007835;
L_180007835:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007837;
L_180007837:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_18000783a;
L_18000783a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000783c;
L_18000783c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000783d;
L_18000783d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000783f;
L_18000783f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007841;
L_180007841:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007843;
L_180007843:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_180007845;
L_180007845:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_18000784a;
L_18000784a:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_18000784d;
L_18000784d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000784f;
L_18000784f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007851;
L_180007851:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007852;
L_180007852:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007854;
L_180007854:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007856;
L_180007856:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007858;
L_180007858:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_18000785a;
L_18000785a:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_18000785f;
L_18000785f:
  R.rcx=uint32_t(M.read16((R.rsp+0x20ull))); goto L_180007864;
L_180007864:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007866;
L_180007866:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007868;
L_180007868:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007869;
L_180007869:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000786b;
L_18000786b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000786d;
L_18000786d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_18000786f;
L_18000786f:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_180007871;
L_180007871:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007875;
L_180007875:
  R.rcx=uint32_t(M.read16((R.rsp+0x24ull))); goto L_18000787a;
L_18000787a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000787c;
L_18000787c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000787e;
L_18000787e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000787f;
L_18000787f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007881;
L_180007881:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007883;
L_180007883:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007885;
L_180007885:
  if (!M.zf&&(M.sf==M.of)) goto L_1800078b3; goto L_180007887;
L_180007887:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_18000788f;
L_18000788f:
  R.rcx=uint64_t((0x180007896-0x7896ull)); goto L_180007896;
L_180007896:
  R.rdx=uint64_t(R.rbx); goto L_180007899;
L_180007899:
  R.rcx=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_1800078a1;
L_1800078a1:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rcx*8ull)))); goto L_1800078a5;
L_1800078a5:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_1800078aa;
L_1800078aa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_1800078ac;
L_1800078ac:
  if (M.zf||(M.sf!=M.of)) goto L_1800078b3; goto L_1800078ae;
L_1800078ae:
  R.rdi=uint32_t(2ull); goto L_1800078b3;
L_1800078b3:
  R.r9=uint64_t(M.read64((R.rsp+0x30ull))); goto L_1800078b8;
L_1800078b8:
  R.r9=uint64_t(M.read64((R.rsi+(R.r9*8ull)))); goto L_1800078bc;
L_1800078bc:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_1800078bf;
L_1800078bf:
  if (M.zf) goto L_18000803f; goto L_1800078c5;
L_1800078c5:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800078c8;
L_1800078c8:
  if (M.zf) goto L_18000803f; goto L_1800078ce;
L_1800078ce:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_1800078d1;
L_1800078d1:
  if (!M.zf) goto L_18000791c; goto L_1800078d3;
L_1800078d3:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_1800078d7;
L_1800078d7:
  M.write32((R.rsp+0x80ull), uint32_t(R.rcx)); goto L_1800078de;
L_1800078de:
  T=M.subflags(uint16_t(R.rcx),M.read16((R.r14+0x2ull)),16);
  goto L_1800078e3;
L_1800078e3:
  if (!M.zf) goto L_18000803f; goto L_1800078e9;
L_1800078e9:
  R.r10=uint32_t(M.read16((R.rbx+0x6ull))); goto L_1800078ee;
L_1800078ee:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r14+0x6ull)),16);
  goto L_1800078f3;
L_1800078f3:
  if (!M.zf) goto L_18000803f; goto L_1800078f9;
L_1800078f9:
  R.r11=uint32_t(M.read16((R.rbx+0x4ull))); goto L_1800078fe;
L_1800078fe:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r14+0x4ull)),16);
  goto L_180007903;
L_180007903:
  if (!M.zf) goto L_18000803f; goto L_180007909;
L_180007909:
  R.r13=uint32_t(M.read16((R.rbx))); goto L_18000790d;
L_18000790d:
  T=M.subflags(uint16_t(R.r13),M.read16((R.r14)),16);
  goto L_180007911;
L_180007911:
  if (!M.zf) goto L_18000803f; goto L_180007917;
L_180007917:
  goto L_1800079a5;
L_18000791c:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_180007921;
L_180007921:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180007924;
L_180007924:
  R.rbp=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180007928;
L_180007928:
  R.rcx=uint32_t(uint32_t(R.rbp)); goto L_18000792a;
L_18000792a:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_18000792e;
L_18000792e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007930;
L_180007930:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007932;
L_180007932:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007933;
L_180007933:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007935;
L_180007935:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007937;
L_180007937:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_18000793a;
L_18000793a:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007940;
L_180007940:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_180007945;
L_180007945:
  R.r10=uint32_t(M.read16((R.rbx+0x6ull))); goto L_18000794a;
L_18000794a:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_18000794d;
L_18000794d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000794f;
L_18000794f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007951;
L_180007951:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007952;
L_180007952:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007954;
L_180007954:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007956;
L_180007956:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007959;
L_180007959:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_18000795f;
L_18000795f:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180007964;
L_180007964:
  R.r11=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180007969;
L_180007969:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_18000796c;
L_18000796c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000796e;
L_18000796e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007970;
L_180007970:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007971;
L_180007971:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007973;
L_180007973:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007975;
L_180007975:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007978;
L_180007978:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_18000797e;
L_18000797e:
  R.rax=uint32_t(M.read16((R.r14))); goto L_180007982;
L_180007982:
  R.r13=uint32_t(M.read16((R.rbx))); goto L_180007986;
L_180007986:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180007989;
L_180007989:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000798b;
L_18000798b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000798d;
L_18000798d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000798e;
L_18000798e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007990;
L_180007990:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007992;
L_180007992:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007995;
L_180007995:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_18000799b;
L_18000799b:
  R.rcx=uint32_t(uint16_t(R.rbp)); goto L_18000799e;
L_18000799e:
  M.write32((R.rsp+0x80ull), uint32_t(R.rcx)); goto L_1800079a5;
L_1800079a5:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x28ull))))); goto L_1800079aa;
L_1800079aa:
  R.r8=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_1800079ae;
L_1800079ae:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800079b1;
L_1800079b1:
  if (M.zf) goto L_18000803f; goto L_1800079b7;
L_1800079b7:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_1800079ba;
L_1800079ba:
  if (!M.zf) goto L_180007a26; goto L_1800079bc;
L_1800079bc:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_1800079bf;
L_1800079bf:
  if (M.zf) goto L_18000803f; goto L_1800079c5;
L_1800079c5:
  T=M.subflags(uint16_t(R.rcx),M.read16((R.r8+0x2ull)),16);
  goto L_1800079ca;
L_1800079ca:
  if (!M.zf) goto L_18000803f; goto L_1800079d0;
L_1800079d0:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r8+0x6ull)),16);
  goto L_1800079d5;
L_1800079d5:
  if (!M.zf) goto L_18000803f; goto L_1800079db;
L_1800079db:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r8+0x4ull)),16);
  goto L_1800079e0;
L_1800079e0:
  if (!M.zf) goto L_18000803f; goto L_1800079e6;
L_1800079e6:
  T=M.subflags(uint16_t(R.r13),M.read16((R.r8)),16);
  goto L_1800079ea;
L_1800079ea:
  if (!M.zf) goto L_18000803f; goto L_1800079f0;
L_1800079f0:
  T=M.subflags(uint16_t(R.rcx),M.read16((R.r9+0x2ull)),16);
  goto L_1800079f5;
L_1800079f5:
  if (!M.zf) goto L_18000803f; goto L_1800079fb;
L_1800079fb:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r9+0x6ull)),16);
  goto L_180007a00;
L_180007a00:
  if (!M.zf) goto L_18000803f; goto L_180007a06;
L_180007a06:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r9+0x4ull)),16);
  goto L_180007a0b;
L_180007a0b:
  if (!M.zf) goto L_18000803f; goto L_180007a11;
L_180007a11:
  T=M.subflags(uint16_t(R.r13),M.read16((R.r9)),16);
  goto L_180007a15;
L_180007a15:
  if (!M.zf) goto L_18000803f; goto L_180007a1b;
L_180007a1b:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007a1e;
L_180007a1e:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_180007a21;
L_180007a21:
  goto L_180007b0c;
L_180007a26:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180007a29;
L_180007a29:
  if (M.zf) goto L_18000803f; goto L_180007a2f;
L_180007a2f:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007a34;
L_180007a34:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007a37;
L_180007a37:
  R.rcx=uint32_t(uint16_t(R.rcx)); goto L_180007a3a;
L_180007a3a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007a3c;
L_180007a3c:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_180007a3f;
L_180007a3f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007a41;
L_180007a41:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007a42;
L_180007a42:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007a44;
L_180007a44:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007a46;
L_180007a46:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007a48;
L_180007a48:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007a4e;
L_180007a4e:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007a53;
L_180007a53:
  R.rcx=uint32_t(uint16_t(R.r10)); goto L_180007a57;
L_180007a57:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007a59;
L_180007a59:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007a5b;
L_180007a5b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007a5c;
L_180007a5c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007a5e;
L_180007a5e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007a60;
L_180007a60:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007a62;
L_180007a62:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007a68;
L_180007a68:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007a6d;
L_180007a6d:
  R.rcx=uint32_t(uint16_t(R.r11)); goto L_180007a71;
L_180007a71:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007a73;
L_180007a73:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007a75;
L_180007a75:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007a76;
L_180007a76:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007a78;
L_180007a78:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007a7a;
L_180007a7a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007a7c;
L_180007a7c:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007a82;
L_180007a82:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007a86;
L_180007a86:
  R.rcx=uint32_t(uint16_t(R.r13)); goto L_180007a8a;
L_180007a8a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007a8c;
L_180007a8c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007a8e;
L_180007a8e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007a8f;
L_180007a8f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007a91;
L_180007a91:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007a93;
L_180007a93:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007a95;
L_180007a95:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007a9b;
L_180007a9b:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180007aa0;
L_180007aa0:
  R.rbp=uint32_t(uint32_t(R.r15)); goto L_180007aa3;
L_180007aa3:
  R.rcx=uint32_t(M.read16((R.rsp+0x80ull))); goto L_180007aab;
L_180007aab:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007aad;
L_180007aad:
  R.rbp=uint32_t((uint32_t(R.rbp))<<((7ull)&0x3f)); goto L_180007ab0;
L_180007ab0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007ab2;
L_180007ab2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007ab3;
L_180007ab3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007ab5;
L_180007ab5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007ab7;
L_180007ab7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007ab9;
L_180007ab9:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007abf;
L_180007abf:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180007ac4;
L_180007ac4:
  R.rcx=uint32_t(uint16_t(R.r10)); goto L_180007ac8;
L_180007ac8:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007aca;
L_180007aca:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007acc;
L_180007acc:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007acd;
L_180007acd:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007acf;
L_180007acf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007ad1;
L_180007ad1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007ad3;
L_180007ad3:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007ad9;
L_180007ad9:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180007ade;
L_180007ade:
  R.rcx=uint32_t(uint16_t(R.r11)); goto L_180007ae2;
L_180007ae2:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007ae4;
L_180007ae4:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007ae6;
L_180007ae6:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007ae7;
L_180007ae7:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007ae9;
L_180007ae9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007aeb;
L_180007aeb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007aed;
L_180007aed:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007af3;
L_180007af3:
  R.rax=uint32_t(M.read16((R.r9))); goto L_180007af7;
L_180007af7:
  R.rcx=uint32_t(uint16_t(R.r13)); goto L_180007afb;
L_180007afb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007afd;
L_180007afd:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007aff;
L_180007aff:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007b00;
L_180007b00:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007b02;
L_180007b02:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007b04;
L_180007b04:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007b06;
L_180007b06:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007b0c;
L_180007b0c:
  R.rdx=uint64_t(R.rbx); goto L_180007b0f;
L_180007b0f:
  R.rcx=uint64_t(R.r12); goto L_180007b12;
L_180007b12:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180007b17;
L_180007b17:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007b19;
L_180007b19:
  if (M.zf||(M.sf!=M.of)) goto L_18000803f; goto L_180007b1f;
L_180007b1f:
  R.r14=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007b27;
L_180007b27:
  R.rbx=uint32_t(M.read16((R.r12+0x2ull))); goto L_180007b2d;
L_180007b2d:
  R.r8=uint64_t(M.read64((R.rsi+(R.r14*8ull)))); goto L_180007b31;
L_180007b31:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007b36;
L_180007b36:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180007b39;
L_180007b39:
  if (!M.zf) goto L_180007b77; goto L_180007b3b;
L_180007b3b:
  T=M.subflags(uint16_t(R.rbx),uint16_t(R.rax),16);
  goto L_180007b3e;
L_180007b3e:
  if (!M.zf) goto L_18000803f; goto L_180007b44;
L_180007b44:
  R.r11=uint32_t(M.read16((R.r12+0x6ull))); goto L_180007b4a;
L_180007b4a:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r8+0x6ull)),16);
  goto L_180007b4f;
L_180007b4f:
  if (!M.zf) goto L_18000803f; goto L_180007b55;
L_180007b55:
  R.r10=uint32_t(M.read16((R.r12+0x4ull))); goto L_180007b5b;
L_180007b5b:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r8+0x4ull)),16);
  goto L_180007b60;
L_180007b60:
  if (!M.zf) goto L_18000803f; goto L_180007b66;
L_180007b66:
  R.r9=uint32_t(M.read16((R.r12))); goto L_180007b6b;
L_180007b6b:
  T=M.subflags(uint16_t(R.r9),M.read16((R.r8)),16);
  goto L_180007b6f;
L_180007b6f:
  if (!M.zf) goto L_18000803f; goto L_180007b75;
L_180007b75:
  goto L_180007be5;
L_180007b77:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_180007b79;
L_180007b79:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007b7b;
L_180007b7b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007b7d;
L_180007b7d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007b7e;
L_180007b7e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007b80;
L_180007b80:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007b82;
L_180007b82:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007b84;
L_180007b84:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007b8a;
L_180007b8a:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007b8f;
L_180007b8f:
  R.r11=uint32_t(M.read16((R.r12+0x6ull))); goto L_180007b95;
L_180007b95:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180007b98;
L_180007b98:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007b9a;
L_180007b9a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007b9c;
L_180007b9c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007b9d;
L_180007b9d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007b9f;
L_180007b9f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007ba1;
L_180007ba1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007ba3;
L_180007ba3:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007ba9;
L_180007ba9:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007bae;
L_180007bae:
  R.r10=uint32_t(M.read16((R.r12+0x4ull))); goto L_180007bb4;
L_180007bb4:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_180007bb7;
L_180007bb7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007bb9;
L_180007bb9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007bbb;
L_180007bbb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007bbc;
L_180007bbc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007bbe;
L_180007bbe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007bc0;
L_180007bc0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007bc2;
L_180007bc2:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007bc8;
L_180007bc8:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007bcc;
L_180007bcc:
  R.r9=uint32_t(M.read16((R.r12))); goto L_180007bd1;
L_180007bd1:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_180007bd4;
L_180007bd4:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007bd6;
L_180007bd6:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007bd8;
L_180007bd8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007bd9;
L_180007bd9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007bdb;
L_180007bdb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007bdd;
L_180007bdd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007bdf;
L_180007bdf:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007be5;
L_180007be5:
  R.rax=uint64_t((0x180007bec-0x7becull)); goto L_180007bec;
L_180007bec:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rax+(R.r14*4ull)+0xf050ull))))); goto L_180007bf4;
L_180007bf4:
  R.r8=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007bf8;
L_180007bf8:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180007bfb;
L_180007bfb:
  if (M.zf) goto L_18000803f; goto L_180007c01;
L_180007c01:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180007c04;
L_180007c04:
  if (!M.zf) goto L_180007c75; goto L_180007c06;
L_180007c06:
  T=M.subflags(uint16_t(R.rbx),M.read16((R.r8+0x2ull)),16);
  goto L_180007c0b;
L_180007c0b:
  if (!M.zf) goto L_18000803f; goto L_180007c11;
L_180007c11:
  T=M.subflags(uint16_t(R.r11),M.read16((R.r8+0x6ull)),16);
  goto L_180007c16;
L_180007c16:
  if (!M.zf) goto L_18000803f; goto L_180007c1c;
L_180007c1c:
  T=M.subflags(uint16_t(R.r10),M.read16((R.r8+0x4ull)),16);
  goto L_180007c21;
L_180007c21:
  if (!M.zf) goto L_18000803f; goto L_180007c27;
L_180007c27:
  T=M.subflags(uint16_t(R.r9),M.read16((R.r8)),16);
  goto L_180007c2b;
L_180007c2b:
  if (!M.zf) goto L_18000803f; goto L_180007c31;
L_180007c31:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x98ull))))); goto L_180007c39;
L_180007c39:
  R.rcx=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007c3d;
L_180007c3d:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180007c40;
L_180007c40:
  if (M.zf) goto L_18000803f; goto L_180007c46;
L_180007c46:
  T=M.subflags(uint16_t(R.rbx),M.read16((R.rcx+0x2ull)),16);
  goto L_180007c4a;
L_180007c4a:
  if (!M.zf) goto L_18000803f; goto L_180007c50;
L_180007c50:
  T=M.subflags(uint16_t(R.r11),M.read16((R.rcx+0x6ull)),16);
  goto L_180007c55;
L_180007c55:
  if (!M.zf) goto L_18000803f; goto L_180007c5b;
L_180007c5b:
  T=M.subflags(uint16_t(R.r10),M.read16((R.rcx+0x4ull)),16);
  goto L_180007c60;
L_180007c60:
  if (!M.zf) goto L_18000803f; goto L_180007c66;
L_180007c66:
  T=M.subflags(uint16_t(R.r9),M.read16((R.rcx)),16);
  goto L_180007c6a;
L_180007c6a:
  if (M.zf) goto L_180007d54; goto L_180007c70;
L_180007c70:
  goto L_18000803f;
L_180007c75:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007c7a;
L_180007c7a:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_180007c7c;
L_180007c7c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007c7e;
L_180007c7e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007c80;
L_180007c80:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007c81;
L_180007c81:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007c83;
L_180007c83:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007c85;
L_180007c85:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007c87;
L_180007c87:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007c8d;
L_180007c8d:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007c92;
L_180007c92:
  R.rcx=uint32_t(uint16_t(R.r11)); goto L_180007c96;
L_180007c96:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007c98;
L_180007c98:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007c9a;
L_180007c9a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007c9b;
L_180007c9b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007c9d;
L_180007c9d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007c9f;
L_180007c9f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007ca1;
L_180007ca1:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007ca7;
L_180007ca7:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007cac;
L_180007cac:
  R.rcx=uint32_t(uint16_t(R.r10)); goto L_180007cb0;
L_180007cb0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007cb2;
L_180007cb2:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007cb4;
L_180007cb4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007cb5;
L_180007cb5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007cb7;
L_180007cb7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007cb9;
L_180007cb9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007cbb;
L_180007cbb:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007cc1;
L_180007cc1:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007cc5;
L_180007cc5:
  R.rcx=uint32_t(uint16_t(R.r9)); goto L_180007cc9;
L_180007cc9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007ccb;
L_180007ccb:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007ccd;
L_180007ccd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007cce;
L_180007cce:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007cd0;
L_180007cd0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007cd2;
L_180007cd2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007cd4;
L_180007cd4:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007cda;
L_180007cda:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x98ull))))); goto L_180007ce2;
L_180007ce2:
  R.r8=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007ce6;
L_180007ce6:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180007ce9;
L_180007ce9:
  if (M.zf) goto L_18000803f; goto L_180007cef;
L_180007cef:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007cf4;
L_180007cf4:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_180007cf6;
L_180007cf6:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007cf8;
L_180007cf8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007cfa;
L_180007cfa:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007cfb;
L_180007cfb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007cfd;
L_180007cfd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007cff;
L_180007cff:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007d01;
L_180007d01:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007d07;
L_180007d07:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007d0c;
L_180007d0c:
  R.rcx=uint32_t(uint16_t(R.r11)); goto L_180007d10;
L_180007d10:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007d12;
L_180007d12:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007d14;
L_180007d14:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007d15;
L_180007d15:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007d17;
L_180007d17:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007d19;
L_180007d19:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007d1b;
L_180007d1b:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007d21;
L_180007d21:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007d26;
L_180007d26:
  R.rcx=uint32_t(uint16_t(R.r10)); goto L_180007d2a;
L_180007d2a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007d2c;
L_180007d2c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007d2e;
L_180007d2e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007d2f;
L_180007d2f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007d31;
L_180007d31:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007d33;
L_180007d33:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007d35;
L_180007d35:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007d3b;
L_180007d3b:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007d3f;
L_180007d3f:
  R.rcx=uint32_t(uint16_t(R.r9)); goto L_180007d43;
L_180007d43:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007d45;
L_180007d45:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007d47;
L_180007d47:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007d48;
L_180007d48:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007d4a;
L_180007d4a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007d4c;
L_180007d4c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rbp),32);
  goto L_180007d4e;
L_180007d4e:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007d54;
L_180007d54:
  R.rdi=uint32_t(3ull); goto L_180007d59;
L_180007d59:
  goto L_18000803f;
L_180007d5e:
  R.rcx=uint64_t((0x180007d65-0x7d65ull)); goto L_180007d65;
L_180007d65:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rdi*4ull)+0xf050ull))))); goto L_180007d6d;
L_180007d6d:
  R.r10=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007d71;
L_180007d71:
  goto L_180007da6;
L_180007d73:
  R.rdi=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007d7b;
L_180007d7b:
  R.rcx=uint64_t((0x180007d82-0x7d82ull)); goto L_180007d82;
L_180007d82:
  R.r11=uint64_t(R.rbx); goto L_180007d85;
L_180007d85:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rdi*4ull)+0xf050ull))))); goto L_180007d8d;
L_180007d8d:
  R.r10=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007d91;
L_180007d91:
  goto L_180007db2;
L_180007d93:
  R.r10=uint64_t(M.read64((R.rsi+(R.rdi*8ull)))); goto L_180007d97;
L_180007d97:
  R.rcx=uint64_t((0x180007d9e - 0x7d9eull)); goto L_180007d9e;
L_180007d9e:
  R.rdi=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007da6;
L_180007da6:
  R.r11=uint64_t(R.rbx); goto L_180007da9;
L_180007da9:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007dac;
L_180007dac:
  if (M.zf) goto L_180007e43; goto L_180007db2;
L_180007db2:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180007db5;
L_180007db5:
  if (M.zf) goto L_180007e43; goto L_180007dbb;
L_180007dbb:
  R.rax=uint32_t(M.read16((R.r10+0x2ull))); goto L_180007dc0;
L_180007dc0:
  R.rdi=uint32_t(uint32_t(R.r15)); goto L_180007dc3;
L_180007dc3:
  R.rcx=uint32_t(M.read16((R.r11+0x2ull))); goto L_180007dc8;
L_180007dc8:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007dca;
L_180007dca:
  R.rdi=uint32_t((uint32_t(R.rdi))<<((7ull)&0x3f)); goto L_180007dcd;
L_180007dcd:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007dcf;
L_180007dcf:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007dd0;
L_180007dd0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007dd2;
L_180007dd2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007dd4;
L_180007dd4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007dd6;
L_180007dd6:
  if (!M.zf&&(M.sf==M.of)) goto L_180007e20; goto L_180007dd8;
L_180007dd8:
  R.rax=uint32_t(M.read16((R.r10+0x6ull))); goto L_180007ddd;
L_180007ddd:
  R.rcx=uint32_t(M.read16((R.r11+0x6ull))); goto L_180007de2;
L_180007de2:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007de4;
L_180007de4:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007de6;
L_180007de6:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007de7;
L_180007de7:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007de9;
L_180007de9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007deb;
L_180007deb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007ded;
L_180007ded:
  if (!M.zf&&(M.sf==M.of)) goto L_180007e20; goto L_180007def;
L_180007def:
  R.rax=uint32_t(M.read16((R.r10+0x4ull))); goto L_180007df4;
L_180007df4:
  R.rcx=uint32_t(M.read16((R.r11+0x4ull))); goto L_180007df9;
L_180007df9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007dfb;
L_180007dfb:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007dfd;
L_180007dfd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007dfe;
L_180007dfe:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007e00;
L_180007e00:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007e02;
L_180007e02:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007e04;
L_180007e04:
  if (!M.zf&&(M.sf==M.of)) goto L_180007e20; goto L_180007e06;
L_180007e06:
  R.rax=uint32_t(M.read16((R.r10))); goto L_180007e0a;
L_180007e0a:
  R.rcx=uint32_t(M.read16((R.r11))); goto L_180007e0e;
L_180007e0e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007e10;
L_180007e10:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007e12;
L_180007e12:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007e13;
L_180007e13:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007e15;
L_180007e15:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007e17;
L_180007e17:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180007e19;
L_180007e19:
  if (!M.zf&&(M.sf==M.of)) goto L_180007e20; goto L_180007e1b;
L_180007e1b:
  R.r10=(R.r10&~0xffull)|(uint8_t(1ull)); goto L_180007e1e;
L_180007e1e:
  goto L_180007e23;
L_180007e20:
  T=(uint8_t(R.r10)) ^ (uint8_t(R.r10)); M.logicflags(T,8);
  R.r10=(R.r10&~0xffull)|(uint8_t(T));
  goto L_180007e23;
L_180007e23:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0xa0ull))))); goto L_180007e2b;
L_180007e2b:
  R.rcx=uint64_t((0x180007e32-0x7e32ull)); goto L_180007e32;
L_180007e32:
  R.rdi=uint64_t(R.rbx); goto L_180007e35;
L_180007e35:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_180007e3d;
L_180007e3d:
  R.r11=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007e41;
L_180007e41:
  goto L_180007e5a;
L_180007e43:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rdi*4ull)+0xf078ull))))); goto L_180007e4b;
L_180007e4b:
  T=(uint8_t(R.r10)) ^ (uint8_t(R.r10)); M.logicflags(T,8);
  R.r10=(R.r10&~0xffull)|(uint8_t(T));
  goto L_180007e4e;
L_180007e4e:
  R.rdi=uint64_t(R.rbx); goto L_180007e51;
L_180007e51:
  R.r11=uint64_t(M.read64((R.rsi+(R.rax*8ull)))); goto L_180007e55;
L_180007e55:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007e58;
L_180007e58:
  if (M.zf) goto L_180007ebf; goto L_180007e5a;
L_180007e5a:
  T=(R.r11) & (R.r11); M.logicflags(T,64);
  goto L_180007e5d;
L_180007e5d:
  if (M.zf) goto L_180007ebf; goto L_180007e5f;
L_180007e5f:
  R.rax=uint32_t(M.read16((R.r11+0x2ull))); goto L_180007e64;
L_180007e64:
  R.rsi=uint32_t(uint32_t(R.r15)); goto L_180007e67;
L_180007e67:
  R.rcx=uint32_t(M.read16((R.rdi+0x2ull))); goto L_180007e6b;
L_180007e6b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007e6d;
L_180007e6d:
  R.rsi=uint32_t((uint32_t(R.rsi))<<((7ull)&0x3f)); goto L_180007e70;
L_180007e70:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007e72;
L_180007e72:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007e73;
L_180007e73:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007e75;
L_180007e75:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007e77;
L_180007e77:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rsi),32);
  goto L_180007e79;
L_180007e79:
  if (!M.zf&&(M.sf==M.of)) goto L_180007ebf; goto L_180007e7b;
L_180007e7b:
  R.rax=uint32_t(M.read16((R.r11+0x6ull))); goto L_180007e80;
L_180007e80:
  R.rcx=uint32_t(M.read16((R.rdi+0x6ull))); goto L_180007e84;
L_180007e84:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007e86;
L_180007e86:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007e88;
L_180007e88:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007e89;
L_180007e89:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007e8b;
L_180007e8b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007e8d;
L_180007e8d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rsi),32);
  goto L_180007e8f;
L_180007e8f:
  if (!M.zf&&(M.sf==M.of)) goto L_180007ebf; goto L_180007e91;
L_180007e91:
  R.rax=uint32_t(M.read16((R.r11+0x4ull))); goto L_180007e96;
L_180007e96:
  R.rcx=uint32_t(M.read16((R.rdi+0x4ull))); goto L_180007e9a;
L_180007e9a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007e9c;
L_180007e9c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007e9e;
L_180007e9e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007e9f;
L_180007e9f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007ea1;
L_180007ea1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007ea3;
L_180007ea3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rsi),32);
  goto L_180007ea5;
L_180007ea5:
  if (!M.zf&&(M.sf==M.of)) goto L_180007ebf; goto L_180007ea7;
L_180007ea7:
  R.rax=uint32_t(M.read16((R.r11))); goto L_180007eab;
L_180007eab:
  R.rcx=uint32_t(M.read16((R.rdi))); goto L_180007eae;
L_180007eae:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007eb0;
L_180007eb0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007eb2;
L_180007eb2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007eb3;
L_180007eb3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007eb5;
L_180007eb5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007eb7;
L_180007eb7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rsi),32);
  goto L_180007eb9;
L_180007eb9:
  if (!M.zf&&(M.sf==M.of)) goto L_180007ebf; goto L_180007ebb;
L_180007ebb:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180007ebd;
L_180007ebd:
  goto L_180007ec1;
L_180007ebf:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180007ec1;
L_180007ec1:
  R.rdi=uint32_t(uint32_t(R.r12)); goto L_180007ec4;
L_180007ec4:
  T=M.subflags(uint8_t(R.rax),uint8_t(R.r10),8);
  goto L_180007ec7;
L_180007ec7:
  if (M.zf) goto L_18000803f; goto L_180007ecd;
L_180007ecd:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180007ed0;
L_180007ed0:
  if (!M.zf) goto L_180007f5f; goto L_180007ed6;
L_180007ed6:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007ed9;
L_180007ed9:
  if (M.zf) goto L_180007f0e; goto L_180007edb;
L_180007edb:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180007ede;
L_180007ede:
  if (M.zf) goto L_180007f0e; goto L_180007ee0;
L_180007ee0:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_180007ee5;
L_180007ee5:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180007ee9;
L_180007ee9:
  if (!M.zf) goto L_180007f0e; goto L_180007eeb;
L_180007eeb:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_180007ef0;
L_180007ef0:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180007ef4;
L_180007ef4:
  if (!M.zf) goto L_180007f0e; goto L_180007ef6;
L_180007ef6:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180007efb;
L_180007efb:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180007eff;
L_180007eff:
  if (!M.zf) goto L_180007f0e; goto L_180007f01;
L_180007f01:
  R.rax=uint32_t(M.read16((R.r14))); goto L_180007f05;
L_180007f05:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180007f08;
L_180007f08:
  if (!M.zf) goto L_180007f0e; goto L_180007f0a;
L_180007f0a:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180007f0c;
L_180007f0c:
  goto L_180007f10;
L_180007f0e:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180007f10;
L_180007f10:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180007f12;
L_180007f12:
  if (M.zf) goto L_18000803f; goto L_180007f18;
L_180007f18:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007f1b;
L_180007f1b:
  if (M.zf) goto L_180007f50; goto L_180007f1d;
L_180007f1d:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180007f20;
L_180007f20:
  if (M.zf) goto L_180007f50; goto L_180007f22;
L_180007f22:
  R.rax=uint32_t(M.read16((R.r8+0x2ull))); goto L_180007f27;
L_180007f27:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180007f2b;
L_180007f2b:
  if (!M.zf) goto L_180007f50; goto L_180007f2d;
L_180007f2d:
  R.rax=uint32_t(M.read16((R.r8+0x6ull))); goto L_180007f32;
L_180007f32:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180007f36;
L_180007f36:
  if (!M.zf) goto L_180007f50; goto L_180007f38;
L_180007f38:
  R.rax=uint32_t(M.read16((R.r8+0x4ull))); goto L_180007f3d;
L_180007f3d:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180007f41;
L_180007f41:
  if (!M.zf) goto L_180007f50; goto L_180007f43;
L_180007f43:
  R.rax=uint32_t(M.read16((R.r8))); goto L_180007f47;
L_180007f47:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180007f4a;
L_180007f4a:
  if (!M.zf) goto L_180007f50; goto L_180007f4c;
L_180007f4c:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180007f4e;
L_180007f4e:
  goto L_180007f52;
L_180007f50:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180007f52;
L_180007f52:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180007f54;
L_180007f54:
  if (M.zf) goto L_18000803f; goto L_180007f5a;
L_180007f5a:
  goto L_18000803d;
L_180007f5f:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180007f62;
L_180007f62:
  if (M.zf) goto L_18000803f; goto L_180007f68;
L_180007f68:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180007f6b;
L_180007f6b:
  if (M.zf) goto L_18000803f; goto L_180007f71;
L_180007f71:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_180007f76;
L_180007f76:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180007f79;
L_180007f79:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180007f7d;
L_180007f7d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007f7f;
L_180007f7f:
  R.r8=uint32_t((uint32_t(R.r8))<<((7ull)&0x3f)); goto L_180007f83;
L_180007f83:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007f85;
L_180007f85:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007f86;
L_180007f86:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007f88;
L_180007f88:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007f8a;
L_180007f8a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007f8d;
L_180007f8d:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007f93;
L_180007f93:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_180007f98;
L_180007f98:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180007f9c;
L_180007f9c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007f9e;
L_180007f9e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007fa0;
L_180007fa0:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007fa1;
L_180007fa1:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007fa3;
L_180007fa3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007fa5;
L_180007fa5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007fa8;
L_180007fa8:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007fae;
L_180007fae:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180007fb3;
L_180007fb3:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180007fb7;
L_180007fb7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007fb9;
L_180007fb9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007fbb;
L_180007fbb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007fbc;
L_180007fbc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007fbe;
L_180007fbe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007fc0;
L_180007fc0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007fc3;
L_180007fc3:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007fc5;
L_180007fc5:
  R.rax=uint32_t(M.read16((R.r14))); goto L_180007fc9;
L_180007fc9:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_180007fcc;
L_180007fcc:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007fce;
L_180007fce:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007fd0;
L_180007fd0:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007fd1;
L_180007fd1:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007fd3;
L_180007fd3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007fd5;
L_180007fd5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180007fd8;
L_180007fd8:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007fda;
L_180007fda:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180007fdd;
L_180007fdd:
  if (M.zf) goto L_18000803f; goto L_180007fdf;
L_180007fdf:
  R.rax=uint32_t(M.read16((R.r9+0x2ull))); goto L_180007fe4;
L_180007fe4:
  R.rcx=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180007fe8;
L_180007fe8:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180007fea;
L_180007fea:
  R.r15=uint32_t((uint32_t(R.r15))<<((7ull)&0x3f)); goto L_180007fee;
L_180007fee:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180007ff0;
L_180007ff0:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180007ff1;
L_180007ff1:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180007ff3;
L_180007ff3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180007ff5;
L_180007ff5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180007ff8;
L_180007ff8:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180007ffa;
L_180007ffa:
  R.rax=uint32_t(M.read16((R.r9+0x6ull))); goto L_180007fff;
L_180007fff:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180008003;
L_180008003:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008005;
L_180008005:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008007;
L_180008007:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008008;
L_180008008:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000800a;
L_18000800a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000800c;
L_18000800c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_18000800f;
L_18000800f:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180008011;
L_180008011:
  R.rax=uint32_t(M.read16((R.r9+0x4ull))); goto L_180008016;
L_180008016:
  R.rcx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_18000801a;
L_18000801a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000801c;
L_18000801c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000801e;
L_18000801e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000801f;
L_18000801f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008021;
L_180008021:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008023;
L_180008023:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180008026;
L_180008026:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_180008028;
L_180008028:
  R.rax=uint32_t(M.read16((R.r9))); goto L_18000802c;
L_18000802c:
  R.rcx=uint32_t(M.read16((R.rbx))); goto L_18000802f;
L_18000802f:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008031;
L_180008031:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008033;
L_180008033:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008034;
L_180008034:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008036;
L_180008036:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008038;
L_180008038:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_18000803b;
L_18000803b:
  if (!M.zf&&(M.sf==M.of)) goto L_18000803f; goto L_18000803d;
L_18000803d:
  T=(uint32_t(R.rdi)) ^ (uint32_t(R.rdi)); M.logicflags(T,32);
  R.rdi=uint32_t(T);
  goto L_18000803f;
L_18000803f:
  R.r12=uint64_t(M.read64((R.rsp+0x88ull))); goto L_180008047;
L_180008047:
  R.r13=uint64_t(M.read64((R.rsp+0x40ull))); goto L_18000804c;
L_18000804c:
  R.rax=uint32_t(uint32_t(R.rdi)); goto L_18000804e;
L_18000804e:
  T=M.addflags(R.rsp,0x48ull,64); R.rsp=uint64_t(T); goto L_180008052;
L_180008052:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180008054;
L_180008054:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180008056;
L_180008056:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180008057;
L_180008057:
  R.rsi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180008058;
L_180008058:
  R.rbp=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180008059;
L_180008059:
  R.rbx=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000805a;
L_18000805a:
  return (int32_t)R.rax;
