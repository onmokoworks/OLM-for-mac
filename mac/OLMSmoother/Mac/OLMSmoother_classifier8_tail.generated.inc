// Generated from olmsmoother_v1_classifier8_tail_cfg_20260805.json; do not hand edit.
L_1800087f0:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800087f3;
L_1800087f3:
  if (M.zf) goto L_1800088e3; goto L_1800087f9;
L_1800087f9:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_1800087fc;
L_1800087fc:
  if (M.zf) goto L_1800088e3; goto L_180008802;
L_180008802:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_180008807;
L_180008807:
  R.rcx=uint32_t(M.read8((R.rbx+0x1ull))); goto L_18000880b;
L_18000880b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000880d;
L_18000880d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000880f;
L_18000880f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008810;
L_180008810:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008812;
L_180008812:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008814;
L_180008814:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008816;
L_180008816:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_18000881c;
L_18000881c:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_180008821;
L_180008821:
  R.rcx=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180008825;
L_180008825:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008827;
L_180008827:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008829;
L_180008829:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000882a;
L_18000882a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000882c;
L_18000882c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000882e;
L_18000882e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008830;
L_180008830:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_180008836;
L_180008836:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_18000883b;
L_18000883b:
  R.rcx=uint32_t(M.read8((R.rbx+0x2ull))); goto L_18000883f;
L_18000883f:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008841;
L_180008841:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008843;
L_180008843:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008844;
L_180008844:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008846;
L_180008846:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008848;
L_180008848:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000884a;
L_18000884a:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_180008850;
L_180008850:
  R.rax=uint32_t(M.read8((R.r15))); goto L_180008854;
L_180008854:
  R.rcx=uint32_t(M.read8((R.rbx))); goto L_180008857;
L_180008857:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008859;
L_180008859:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000885b;
L_18000885b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000885c;
L_18000885c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000885e;
L_18000885e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008860;
L_180008860:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008862;
L_180008862:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_180008864;
L_180008864:
  R.r8=uint64_t(M.read64((R.r14+(R.rsi*8ull)))); goto L_180008868;
L_180008868:
  T=(R.r13) & (R.r13); M.logicflags(T,64);
  goto L_18000886b;
L_18000886b:
  if (M.zf) goto L_1800088d4; goto L_18000886d;
L_18000886d:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180008870;
L_180008870:
  if (M.zf) goto L_1800088d4; goto L_180008872;
L_180008872:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008877;
L_180008877:
  R.rcx=uint32_t(M.read8((R.r13+0x1ull))); goto L_18000887c;
L_18000887c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000887e;
L_18000887e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008880;
L_180008880:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008881;
L_180008881:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008883;
L_180008883:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008885;
L_180008885:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008887;
L_180008887:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_180008889;
L_180008889:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_18000888e;
L_18000888e:
  R.rcx=uint32_t(M.read8((R.r13+0x3ull))); goto L_180008893;
L_180008893:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008895;
L_180008895:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008897;
L_180008897:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008898;
L_180008898:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000889a;
L_18000889a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000889c;
L_18000889c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000889e;
L_18000889e:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_1800088a0;
L_1800088a0:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_1800088a5;
L_1800088a5:
  R.rcx=uint32_t(M.read8((R.r13+0x2ull))); goto L_1800088aa;
L_1800088aa:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800088ac;
L_1800088ac:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800088ae;
L_1800088ae:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800088af;
L_1800088af:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800088b1;
L_1800088b1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800088b3;
L_1800088b3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800088b5;
L_1800088b5:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_1800088b7;
L_1800088b7:
  R.rax=uint32_t(M.read8((R.r8))); goto L_1800088bb;
L_1800088bb:
  R.rcx=uint32_t(M.read8((R.r13))); goto L_1800088c0;
L_1800088c0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800088c2;
L_1800088c2:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800088c4;
L_1800088c4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800088c5;
L_1800088c5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800088c7;
L_1800088c7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800088c9;
L_1800088c9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800088cb;
L_1800088cb:
  if (!M.zf&&(M.sf==M.of)) goto L_1800088d4; goto L_1800088cd;
L_1800088cd:
  T=(uint32_t(R.rsi)) ^ (uint32_t(R.rsi)); M.logicflags(T,32);
  R.rsi=uint32_t(T);
  goto L_1800088cf;
L_1800088cf:
  goto L_180008a0f;
L_1800088d4:
  R.r8=uint64_t(M.read64((R.r14+(R.r12*8ull)))); goto L_1800088d8;
L_1800088d8:
  R.r11=uint64_t(R.rbx); goto L_1800088db;
L_1800088db:
  R.r9=uint64_t(R.r8); goto L_1800088de;
L_1800088de:
  R.r10=uint64_t(R.r8); goto L_1800088e1;
L_1800088e1:
  goto L_1800088f9;
L_1800088e3:
  R.r8=uint64_t(M.read64((R.r14+(R.r12*8ull)))); goto L_1800088e7;
L_1800088e7:
  R.r11=uint64_t(R.rbx); goto L_1800088ea;
L_1800088ea:
  R.r9=uint64_t(R.r8); goto L_1800088ed;
L_1800088ed:
  R.r10=uint64_t(R.r8); goto L_1800088f0;
L_1800088f0:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800088f3;
L_1800088f3:
  if (M.zf) goto L_1800091d2; goto L_1800088f9;
L_1800088f9:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_1800088fc;
L_1800088fc:
  if (M.zf) goto L_1800091d2; goto L_180008902;
L_180008902:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_180008907;
L_180008907:
  R.rcx=uint32_t(M.read8((R.r11+0x1ull))); goto L_18000890c;
L_18000890c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000890e;
L_18000890e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008910;
L_180008910:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008911;
L_180008911:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008913;
L_180008913:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008915;
L_180008915:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008917;
L_180008917:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091c9; goto L_18000891d;
L_18000891d:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_180008922;
L_180008922:
  R.rcx=uint32_t(M.read8((R.r11+0x3ull))); goto L_180008927;
L_180008927:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008929;
L_180008929:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000892b;
L_18000892b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000892c;
L_18000892c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000892e;
L_18000892e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008930;
L_180008930:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008932;
L_180008932:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091c9; goto L_180008938;
L_180008938:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_18000893d;
L_18000893d:
  R.rcx=uint32_t(M.read8((R.r11+0x2ull))); goto L_180008942;
L_180008942:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008944;
L_180008944:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008946;
L_180008946:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008947;
L_180008947:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008949;
L_180008949:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000894b;
L_18000894b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000894d;
L_18000894d:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091c9; goto L_180008953;
L_180008953:
  R.rax=uint32_t(M.read8((R.r10))); goto L_180008957;
L_180008957:
  R.rcx=uint32_t(M.read8((R.r11))); goto L_18000895b;
L_18000895b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000895d;
L_18000895d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000895f;
L_18000895f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008960;
L_180008960:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008962;
L_180008962:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008964;
L_180008964:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008966;
L_180008966:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091c9; goto L_18000896c;
L_18000896c:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008974;
L_180008974:
  R.rcx=uint64_t((0x18000897b-0x897bull)); goto L_18000897b;
L_18000897b:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_180008983;
L_180008983:
  R.r10=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008987;
L_180008987:
  T=(R.r13) & (R.r13); M.logicflags(T,64);
  goto L_18000898a;
L_18000898a:
  if (M.zf) goto L_1800091d2; goto L_180008990;
L_180008990:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180008993;
L_180008993:
  if (M.zf) goto L_1800091d2; goto L_180008999;
L_180008999:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_18000899e;
L_18000899e:
  R.rcx=uint32_t(M.read8((R.r13+0x1ull))); goto L_1800089a3;
L_1800089a3:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800089a5;
L_1800089a5:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800089a7;
L_1800089a7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800089a8;
L_1800089a8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800089aa;
L_1800089aa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800089ac;
L_1800089ac:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800089ae;
L_1800089ae:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091d2; goto L_1800089b4;
L_1800089b4:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_1800089b9;
L_1800089b9:
  R.rcx=uint32_t(M.read8((R.r13+0x3ull))); goto L_1800089be;
L_1800089be:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800089c0;
L_1800089c0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800089c2;
L_1800089c2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800089c3;
L_1800089c3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800089c5;
L_1800089c5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800089c7;
L_1800089c7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800089c9;
L_1800089c9:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091d2; goto L_1800089cf;
L_1800089cf:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_1800089d4;
L_1800089d4:
  R.rcx=uint32_t(M.read8((R.r13+0x2ull))); goto L_1800089d9;
L_1800089d9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800089db;
L_1800089db:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800089dd;
L_1800089dd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800089de;
L_1800089de:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800089e0;
L_1800089e0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800089e2;
L_1800089e2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800089e4;
L_1800089e4:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091d2; goto L_1800089ea;
L_1800089ea:
  R.rax=uint32_t(M.read8((R.r10))); goto L_1800089ee;
L_1800089ee:
  R.rcx=uint32_t(M.read8((R.r13))); goto L_1800089f3;
L_1800089f3:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800089f5;
L_1800089f5:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800089f7;
L_1800089f7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800089f8;
L_1800089f8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800089fa;
L_1800089fa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800089fc;
L_1800089fc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800089fe;
L_1800089fe:
  if (!M.zf&&(M.sf==M.of)) goto L_1800091d2; goto L_180008a04;
L_180008a04:
  T=(uint32_t(R.rsi)) ^ (uint32_t(R.rsi)); M.logicflags(T,32);
  R.rsi=uint32_t(T);
  goto L_180008a06;
L_180008a06:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180008a09;
L_180008a09:
  if (M.zf) goto L_180009455; goto L_180008a0f;
L_180008a0f:
  R.r8=uint64_t((0x180008a16-0x8a16ull)); goto L_180008a16;
L_180008a16:
  R.rbp=uint64_t(M.read64((R.r14+(R.r12*8ull)))); goto L_180008a1a;
L_180008a1a:
  T=(R.rbp) & (R.rbp); M.logicflags(T,64);
  goto L_180008a1d;
L_180008a1d:
  if (M.zf) goto L_180009455; goto L_180008a23;
L_180008a23:
  T=(R.r13) & (R.r13); M.logicflags(T,64);
  goto L_180008a26;
L_180008a26:
  if (M.zf) goto L_180009455; goto L_180008a2c;
L_180008a2c:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180008a2f;
L_180008a2f:
  if (M.zf) goto L_180008d71; goto L_180008a35;
L_180008a35:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180008a37;
L_180008a37:
  if (!M.zf) goto L_180008aac; goto L_180008a39;
L_180008a39:
  R.rdx=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180008a3d;
L_180008a3d:
  T=M.subflags(uint8_t(R.rdx),M.read8((R.r15+0x1ull)),8);
  goto L_180008a41;
L_180008a41:
  if (!M.zf) goto L_180008a9c; goto L_180008a43;
L_180008a43:
  R.r8=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180008a48;
L_180008a48:
  T=M.subflags(uint8_t(R.r8),M.read8((R.r15+0x3ull)),8);
  goto L_180008a4c;
L_180008a4c:
  if (!M.zf) goto L_180008a9c; goto L_180008a4e;
L_180008a4e:
  R.r9=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180008a53;
L_180008a53:
  T=M.subflags(uint8_t(R.r9),M.read8((R.r15+0x2ull)),8);
  goto L_180008a57;
L_180008a57:
  if (!M.zf) goto L_180008a9c; goto L_180008a59;
L_180008a59:
  R.r11=uint32_t(M.read8((R.rbx))); goto L_180008a5d;
L_180008a5d:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r15)),8);
  goto L_180008a60;
L_180008a60:
  if (!M.zf) goto L_180008a9c; goto L_180008a62;
L_180008a62:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008a6a;
L_180008a6a:
  R.rcx=uint64_t((0x180008a71-0x8a71ull)); goto L_180008a71;
L_180008a71:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_180008a79;
L_180008a79:
  R.rcx=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008a7d;
L_180008a7d:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180008a80;
L_180008a80:
  if (M.zf) goto L_180008a9c; goto L_180008a82;
L_180008a82:
  T=M.subflags(uint8_t(R.rdx),M.read8((R.rcx+0x1ull)),8);
  goto L_180008a85;
L_180008a85:
  if (!M.zf) goto L_180008a9c; goto L_180008a87;
L_180008a87:
  T=M.subflags(uint8_t(R.r8),M.read8((R.rcx+0x3ull)),8);
  goto L_180008a8b;
L_180008a8b:
  if (!M.zf) goto L_180008a9c; goto L_180008a8d;
L_180008a8d:
  T=M.subflags(uint8_t(R.r9),M.read8((R.rcx+0x2ull)),8);
  goto L_180008a91;
L_180008a91:
  if (!M.zf) goto L_180008a9c; goto L_180008a93;
L_180008a93:
  T=M.subflags(uint8_t(R.r11),M.read8((R.rcx)),8);
  goto L_180008a96;
L_180008a96:
  if (M.zf) goto L_180008ba2; goto L_180008a9c;
L_180008a9c:
  R.r13=uint32_t(M.read32((R.rsp+0x70ull))); goto L_180008aa1;
L_180008aa1:
  R.r9=uint64_t(R.rbp); goto L_180008aa4;
L_180008aa4:
  R.r8=uint64_t(R.rbx); goto L_180008aa7;
L_180008aa7:
  goto L_180008bce;
L_180008aac:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_180008ab1;
L_180008ab1:
  R.r9=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180008ab6;
L_180008ab6:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_180008ab9;
L_180008ab9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008abb;
L_180008abb:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008abd;
L_180008abd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008abe;
L_180008abe:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ac0;
L_180008ac0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ac2;
L_180008ac2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008ac4;
L_180008ac4:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008aca;
L_180008aca:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_180008acf;
L_180008acf:
  R.r11=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180008ad4;
L_180008ad4:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180008ad7;
L_180008ad7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ad9;
L_180008ad9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008adb;
L_180008adb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008adc;
L_180008adc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ade;
L_180008ade:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ae0;
L_180008ae0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008ae2;
L_180008ae2:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008ae8;
L_180008ae8:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_180008aed;
L_180008aed:
  R.r12=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180008af2;
L_180008af2:
  R.rcx=uint32_t(uint32_t(R.r12)); goto L_180008af5;
L_180008af5:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008af7;
L_180008af7:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008af9;
L_180008af9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008afa;
L_180008afa:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008afc;
L_180008afc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008afe;
L_180008afe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b00;
L_180008b00:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008b06;
L_180008b06:
  R.rax=uint32_t(M.read8((R.r15))); goto L_180008b0a;
L_180008b0a:
  R.r13=uint32_t(M.read8((R.rbx))); goto L_180008b0e;
L_180008b0e:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180008b11;
L_180008b11:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008b13;
L_180008b13:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008b15;
L_180008b15:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008b16;
L_180008b16:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008b18;
L_180008b18:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008b1a;
L_180008b1a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b1c;
L_180008b1c:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008b22;
L_180008b22:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008b2a;
L_180008b2a:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.r8+(R.rax*4ull)+0xf078ull))))); goto L_180008b32;
L_180008b32:
  R.r8=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008b36;
L_180008b36:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180008b39;
L_180008b39:
  if (M.zf) goto L_180008c4f; goto L_180008b3f;
L_180008b3f:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008b44;
L_180008b44:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_180008b47;
L_180008b47:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008b49;
L_180008b49:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008b4b;
L_180008b4b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008b4c;
L_180008b4c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008b4e;
L_180008b4e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008b50;
L_180008b50:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b52;
L_180008b52:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008b58;
L_180008b58:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_180008b5d;
L_180008b5d:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180008b60;
L_180008b60:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008b62;
L_180008b62:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008b64;
L_180008b64:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008b65;
L_180008b65:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008b67;
L_180008b67:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008b69;
L_180008b69:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b6b;
L_180008b6b:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008b71;
L_180008b71:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180008b76;
L_180008b76:
  R.rcx=uint32_t(uint32_t(R.r12)); goto L_180008b79;
L_180008b79:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008b7b;
L_180008b7b:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008b7d;
L_180008b7d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008b7e;
L_180008b7e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008b80;
L_180008b80:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008b82;
L_180008b82:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b84;
L_180008b84:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008b8a;
L_180008b8a:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180008b8e;
L_180008b8e:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180008b91;
L_180008b91:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008b93;
L_180008b93:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008b95;
L_180008b95:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008b96;
L_180008b96:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008b98;
L_180008b98:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008b9a;
L_180008b9a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008b9c;
L_180008b9c:
  if (!M.zf&&(M.sf==M.of)) goto L_180008c4f; goto L_180008ba2;
L_180008ba2:
  R.r13=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x70ull))))); goto L_180008ba7;
L_180008ba7:
  R.rdx=uint64_t(R.rbx); goto L_180008baa;
L_180008baa:
  R.rcx=uint64_t(M.read64((R.r14+(R.r13*8ull)))); goto L_180008bae;
L_180008bae:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180008bb3;
L_180008bb3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008bb5;
L_180008bb5:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d6c; goto L_180008bbb;
L_180008bbb:
  R.r9=uint64_t(R.rbp); goto L_180008bbe;
L_180008bbe:
  R.r8=uint64_t(R.rbx); goto L_180008bc1;
L_180008bc1:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180008bc3;
L_180008bc3:
  if (!M.zf) goto L_180008c44; goto L_180008bc5;
L_180008bc5:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180008bc8;
L_180008bc8:
  if (M.zf) goto L_180008d71; goto L_180008bce;
L_180008bce:
  R.r10=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008bd3;
L_180008bd3:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r9+0x1ull)),8);
  goto L_180008bd7;
L_180008bd7:
  if (!M.zf) goto L_180008d71; goto L_180008bdd;
L_180008bdd:
  R.r11=uint32_t(M.read8((R.r8+0x3ull))); goto L_180008be2;
L_180008be2:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r9+0x3ull)),8);
  goto L_180008be6;
L_180008be6:
  if (!M.zf) goto L_180008d71; goto L_180008bec;
L_180008bec:
  R.r12=uint32_t(M.read8((R.r8+0x2ull))); goto L_180008bf1;
L_180008bf1:
  T=M.subflags(uint8_t(R.r12),M.read8((R.r9+0x2ull)),8);
  goto L_180008bf5;
L_180008bf5:
  if (!M.zf) goto L_180008d71; goto L_180008bfb;
L_180008bfb:
  R.r8=uint32_t(M.read8((R.r8))); goto L_180008bff;
L_180008bff:
  T=M.subflags(uint8_t(R.r8),M.read8((R.r9)),8);
  goto L_180008c02;
L_180008c02:
  if (!M.zf) goto L_180008d71; goto L_180008c08;
L_180008c08:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.r13)))); goto L_180008c0b;
L_180008c0b:
  R.rcx=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008c0f;
L_180008c0f:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_180008c12;
L_180008c12:
  if (M.zf) goto L_180008d71; goto L_180008c18;
L_180008c18:
  T=M.subflags(uint8_t(R.r10),M.read8((R.rcx+0x1ull)),8);
  goto L_180008c1c;
L_180008c1c:
  if (!M.zf) goto L_180008d71; goto L_180008c22;
L_180008c22:
  T=M.subflags(uint8_t(R.r11),M.read8((R.rcx+0x3ull)),8);
  goto L_180008c26;
L_180008c26:
  if (!M.zf) goto L_180008d71; goto L_180008c2c;
L_180008c2c:
  T=M.subflags(uint8_t(R.r12),M.read8((R.rcx+0x2ull)),8);
  goto L_180008c30;
L_180008c30:
  if (!M.zf) goto L_180008d71; goto L_180008c36;
L_180008c36:
  T=M.subflags(uint8_t(R.r8),M.read8((R.rcx)),8);
  goto L_180008c39;
L_180008c39:
  if (M.zf) goto L_180008d45; goto L_180008c3f;
L_180008c3f:
  goto L_180008d71;
L_180008c44:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180008c47;
L_180008c47:
  if (M.zf) goto L_180008d71; goto L_180008c4d;
L_180008c4d:
  goto L_180008c55;
L_180008c4f:
  R.r9=uint64_t(R.rbp); goto L_180008c52;
L_180008c52:
  R.r8=uint64_t(R.rbx); goto L_180008c55;
L_180008c55:
  R.rax=uint32_t(M.read8((R.r9+0x1ull))); goto L_180008c5a;
L_180008c5a:
  R.r11=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008c5f;
L_180008c5f:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180008c62;
L_180008c62:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008c64;
L_180008c64:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008c66;
L_180008c66:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008c67;
L_180008c67:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008c69;
L_180008c69:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008c6b;
L_180008c6b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008c6d;
L_180008c6d:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008c73;
L_180008c73:
  R.rax=uint32_t(M.read8((R.r9+0x3ull))); goto L_180008c78;
L_180008c78:
  R.r12=uint32_t(M.read8((R.r8+0x3ull))); goto L_180008c7d;
L_180008c7d:
  R.rcx=uint32_t(uint32_t(R.r12)); goto L_180008c80;
L_180008c80:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008c82;
L_180008c82:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008c84;
L_180008c84:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008c85;
L_180008c85:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008c87;
L_180008c87:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008c89;
L_180008c89:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008c8b;
L_180008c8b:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008c91;
L_180008c91:
  R.rax=uint32_t(M.read8((R.r9+0x2ull))); goto L_180008c96;
L_180008c96:
  R.r13=uint32_t(M.read8((R.r8+0x2ull))); goto L_180008c9b;
L_180008c9b:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180008c9e;
L_180008c9e:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ca0;
L_180008ca0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008ca2;
L_180008ca2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008ca3;
L_180008ca3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ca5;
L_180008ca5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ca7;
L_180008ca7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008ca9;
L_180008ca9:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008caf;
L_180008caf:
  R.rcx=uint32_t(M.read8((R.r8))); goto L_180008cb3;
L_180008cb3:
  R.rax=uint32_t(M.read8((R.r9))); goto L_180008cb7;
L_180008cb7:
  M.write32((R.rsp+0x70ull), uint32_t(R.rcx)); goto L_180008cbb;
L_180008cbb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008cbd;
L_180008cbd:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008cbf;
L_180008cbf:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008cc0;
L_180008cc0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008cc2;
L_180008cc2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008cc4;
L_180008cc4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008cc6;
L_180008cc6:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008ccc;
L_180008ccc:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008cd4;
L_180008cd4:
  R.rcx=uint64_t((0x180008cdb-0x8cdbull)); goto L_180008cdb;
L_180008cdb:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf050ull))))); goto L_180008ce3;
L_180008ce3:
  R.r8=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008ce7;
L_180008ce7:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180008cea;
L_180008cea:
  if (M.zf) goto L_180008d71; goto L_180008cf0;
L_180008cf0:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008cf5;
L_180008cf5:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180008cf8;
L_180008cf8:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008cfa;
L_180008cfa:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008cfc;
L_180008cfc:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008cfd;
L_180008cfd:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008cff;
L_180008cff:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008d01;
L_180008d01:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008d03;
L_180008d03:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008d05;
L_180008d05:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_180008d0a;
L_180008d0a:
  R.rcx=uint32_t(uint32_t(R.r12)); goto L_180008d0d;
L_180008d0d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008d0f;
L_180008d0f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008d11;
L_180008d11:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008d12;
L_180008d12:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008d14;
L_180008d14:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008d16;
L_180008d16:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008d18;
L_180008d18:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008d1a;
L_180008d1a:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180008d1f;
L_180008d1f:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180008d22;
L_180008d22:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008d24;
L_180008d24:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008d26;
L_180008d26:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008d27;
L_180008d27:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008d29;
L_180008d29:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008d2b;
L_180008d2b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008d2d;
L_180008d2d:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008d2f;
L_180008d2f:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180008d33;
L_180008d33:
  R.rcx=uint32_t(M.read8((R.rsp+0x70ull))); goto L_180008d38;
L_180008d38:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008d3a;
L_180008d3a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008d3c;
L_180008d3c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008d3d;
L_180008d3d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008d3f;
L_180008d3f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008d41;
L_180008d41:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008d43;
L_180008d43:
  if (!M.zf&&(M.sf==M.of)) goto L_180008d71; goto L_180008d45;
L_180008d45:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008d4d;
L_180008d4d:
  R.rcx=uint64_t((0x180008d54-0x8d54ull)); goto L_180008d54;
L_180008d54:
  R.rdx=uint64_t(R.rbx); goto L_180008d57;
L_180008d57:
  R.rcx=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_180008d5f;
L_180008d5f:
  R.rcx=uint64_t(M.read64((R.r14+(R.rcx*8ull)))); goto L_180008d63;
L_180008d63:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180008d68;
L_180008d68:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008d6a;
L_180008d6a:
  if (M.zf||(M.sf!=M.of)) goto L_180008d71; goto L_180008d6c;
L_180008d6c:
  R.rsi=uint32_t(2ull); goto L_180008d71;
L_180008d71:
  R.r9=uint64_t(M.read64((R.rsp+0x28ull))); goto L_180008d76;
L_180008d76:
  R.r9=uint64_t(M.read64((R.r14+(R.r9*8ull)))); goto L_180008d7a;
L_180008d7a:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_180008d7d;
L_180008d7d:
  if (M.zf) goto L_180009455; goto L_180008d83;
L_180008d83:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180008d86;
L_180008d86:
  if (M.zf) goto L_180009455; goto L_180008d8c;
L_180008d8c:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180008d8e;
L_180008d8e:
  if (!M.zf) goto L_180008dcc; goto L_180008d90;
L_180008d90:
  R.r13=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180008d95;
L_180008d95:
  T=M.subflags(uint8_t(R.r13),M.read8((R.r15+0x1ull)),8);
  goto L_180008d99;
L_180008d99:
  if (!M.zf) goto L_180009455; goto L_180008d9f;
L_180008d9f:
  R.r11=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180008da4;
L_180008da4:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r15+0x3ull)),8);
  goto L_180008da8;
L_180008da8:
  if (!M.zf) goto L_180009455; goto L_180008dae;
L_180008dae:
  R.r12=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180008db3;
L_180008db3:
  T=M.subflags(uint8_t(R.r12),M.read8((R.r15+0x2ull)),8);
  goto L_180008db7;
L_180008db7:
  if (!M.zf) goto L_180009455; goto L_180008dbd;
L_180008dbd:
  R.r10=uint32_t(M.read8((R.rbx))); goto L_180008dc1;
L_180008dc1:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r15)),8);
  goto L_180008dc4;
L_180008dc4:
  if (!M.zf) goto L_180009455; goto L_180008dca;
L_180008dca:
  goto L_180008e42;
L_180008dcc:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_180008dd1;
L_180008dd1:
  R.r13=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180008dd6;
L_180008dd6:
  R.rcx=uint32_t(uint32_t(R.r13)); goto L_180008dd9;
L_180008dd9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ddb;
L_180008ddb:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008ddd;
L_180008ddd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008dde;
L_180008dde:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008de0;
L_180008de0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008de2;
L_180008de2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008de4;
L_180008de4:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008dea;
L_180008dea:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_180008def;
L_180008def:
  R.r11=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180008df4;
L_180008df4:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180008df7;
L_180008df7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008df9;
L_180008df9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008dfb;
L_180008dfb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008dfc;
L_180008dfc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008dfe;
L_180008dfe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008e00;
L_180008e00:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008e02;
L_180008e02:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008e08;
L_180008e08:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_180008e0d;
L_180008e0d:
  R.r12=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180008e12;
L_180008e12:
  R.rcx=uint32_t(uint32_t(R.r12)); goto L_180008e15;
L_180008e15:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008e17;
L_180008e17:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008e19;
L_180008e19:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008e1a;
L_180008e1a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008e1c;
L_180008e1c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008e1e;
L_180008e1e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008e20;
L_180008e20:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008e26;
L_180008e26:
  R.rax=uint32_t(M.read8((R.r15))); goto L_180008e2a;
L_180008e2a:
  R.r10=uint32_t(M.read8((R.rbx))); goto L_180008e2e;
L_180008e2e:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_180008e31;
L_180008e31:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008e33;
L_180008e33:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008e35;
L_180008e35:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008e36;
L_180008e36:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008e38;
L_180008e38:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008e3a;
L_180008e3a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008e3c;
L_180008e3c:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008e42;
L_180008e42:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x20ull))))); goto L_180008e47;
L_180008e47:
  R.r8=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180008e4b;
L_180008e4b:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180008e4e;
L_180008e4e:
  if (M.zf) goto L_180009455; goto L_180008e54;
L_180008e54:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180008e56;
L_180008e56:
  if (!M.zf) goto L_180008eb4; goto L_180008e58;
L_180008e58:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180008e5b;
L_180008e5b:
  if (M.zf) goto L_180009455; goto L_180008e61;
L_180008e61:
  T=M.subflags(uint8_t(R.r13),M.read8((R.r8+0x1ull)),8);
  goto L_180008e65;
L_180008e65:
  if (!M.zf) goto L_180009455; goto L_180008e6b;
L_180008e6b:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r8+0x3ull)),8);
  goto L_180008e6f;
L_180008e6f:
  if (!M.zf) goto L_180009455; goto L_180008e75;
L_180008e75:
  T=M.subflags(uint8_t(R.r12),M.read8((R.r8+0x2ull)),8);
  goto L_180008e79;
L_180008e79:
  if (!M.zf) goto L_180009455; goto L_180008e7f;
L_180008e7f:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r8)),8);
  goto L_180008e82;
L_180008e82:
  if (!M.zf) goto L_180009455; goto L_180008e88;
L_180008e88:
  T=M.subflags(uint8_t(R.r13),M.read8((R.r9+0x1ull)),8);
  goto L_180008e8c;
L_180008e8c:
  if (!M.zf) goto L_180009455; goto L_180008e92;
L_180008e92:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r9+0x3ull)),8);
  goto L_180008e96;
L_180008e96:
  if (!M.zf) goto L_180009455; goto L_180008e9c;
L_180008e9c:
  T=M.subflags(uint8_t(R.r12),M.read8((R.r9+0x2ull)),8);
  goto L_180008ea0;
L_180008ea0:
  if (!M.zf) goto L_180009455; goto L_180008ea6;
L_180008ea6:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r9)),8);
  goto L_180008ea9;
L_180008ea9:
  if (M.zf) goto L_180008f8b; goto L_180008eaf;
L_180008eaf:
  goto L_180009455;
L_180008eb4:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180008eb7;
L_180008eb7:
  if (M.zf) goto L_180009455; goto L_180008ebd;
L_180008ebd:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008ec2;
L_180008ec2:
  R.rcx=uint32_t(uint8_t(R.r13)); goto L_180008ec6;
L_180008ec6:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ec8;
L_180008ec8:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008eca;
L_180008eca:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008ecb;
L_180008ecb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ecd;
L_180008ecd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ecf;
L_180008ecf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008ed1;
L_180008ed1:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008ed7;
L_180008ed7:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_180008edc;
L_180008edc:
  R.rcx=uint32_t(uint8_t(R.r11)); goto L_180008ee0;
L_180008ee0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ee2;
L_180008ee2:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008ee4;
L_180008ee4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008ee5;
L_180008ee5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ee7;
L_180008ee7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ee9;
L_180008ee9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008eeb;
L_180008eeb:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008ef1;
L_180008ef1:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180008ef6;
L_180008ef6:
  R.rcx=uint32_t(uint8_t(R.r12)); goto L_180008efa;
L_180008efa:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008efc;
L_180008efc:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008efe;
L_180008efe:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008eff;
L_180008eff:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f01;
L_180008f01:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f03;
L_180008f03:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f05;
L_180008f05:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f0b;
L_180008f0b:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180008f0f;
L_180008f0f:
  R.rcx=uint32_t(uint8_t(R.r10)); goto L_180008f13;
L_180008f13:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008f15;
L_180008f15:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008f17;
L_180008f17:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008f18;
L_180008f18:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f1a;
L_180008f1a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f1c;
L_180008f1c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f1e;
L_180008f1e:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f24;
L_180008f24:
  R.rax=uint32_t(M.read8((R.r9+0x1ull))); goto L_180008f29;
L_180008f29:
  R.rcx=uint32_t(uint8_t(R.r13)); goto L_180008f2d;
L_180008f2d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008f2f;
L_180008f2f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008f31;
L_180008f31:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008f32;
L_180008f32:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f34;
L_180008f34:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f36;
L_180008f36:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f38;
L_180008f38:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f3e;
L_180008f3e:
  R.rax=uint32_t(M.read8((R.r9+0x3ull))); goto L_180008f43;
L_180008f43:
  R.rcx=uint32_t(uint8_t(R.r11)); goto L_180008f47;
L_180008f47:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008f49;
L_180008f49:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008f4b;
L_180008f4b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008f4c;
L_180008f4c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f4e;
L_180008f4e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f50;
L_180008f50:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f52;
L_180008f52:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f58;
L_180008f58:
  R.rax=uint32_t(M.read8((R.r9+0x2ull))); goto L_180008f5d;
L_180008f5d:
  R.rcx=uint32_t(uint8_t(R.r12)); goto L_180008f61;
L_180008f61:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008f63;
L_180008f63:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008f65;
L_180008f65:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008f66;
L_180008f66:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f68;
L_180008f68:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f6a;
L_180008f6a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f6c;
L_180008f6c:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f72;
L_180008f72:
  R.rax=uint32_t(M.read8((R.r9))); goto L_180008f76;
L_180008f76:
  R.rcx=uint32_t(uint8_t(R.r10)); goto L_180008f7a;
L_180008f7a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008f7c;
L_180008f7c:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008f7e;
L_180008f7e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008f7f;
L_180008f7f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008f81;
L_180008f81:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008f83;
L_180008f83:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f85;
L_180008f85:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180008f8b;
L_180008f8b:
  R.rdx=uint64_t(R.rbx); goto L_180008f8e;
L_180008f8e:
  R.rcx=uint64_t(R.rbp); goto L_180008f91;
L_180008f91:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180008f96;
L_180008f96:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008f98;
L_180008f98:
  if (M.zf||(M.sf!=M.of)) goto L_180009455; goto L_180008f9e;
L_180008f9e:
  R.r15=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180008fa6;
L_180008fa6:
  R.rbx=uint32_t(M.read8((R.rbp+0x1ull))); goto L_180008faa;
L_180008faa:
  R.r8=uint64_t(M.read64((R.r14+(R.r15*8ull)))); goto L_180008fae;
L_180008fae:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180008fb3;
L_180008fb3:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180008fb5;
L_180008fb5:
  if (!M.zf) goto L_180008fed; goto L_180008fb7;
L_180008fb7:
  T=M.subflags(uint8_t(R.rbx),uint8_t(R.rax),8);
  goto L_180008fb9;
L_180008fb9:
  if (!M.zf) goto L_180009455; goto L_180008fbf;
L_180008fbf:
  R.r11=uint32_t(M.read8((R.rbp+0x3ull))); goto L_180008fc4;
L_180008fc4:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r8+0x3ull)),8);
  goto L_180008fc8;
L_180008fc8:
  if (!M.zf) goto L_180009455; goto L_180008fce;
L_180008fce:
  R.r10=uint32_t(M.read8((R.rbp+0x2ull))); goto L_180008fd3;
L_180008fd3:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r8+0x2ull)),8);
  goto L_180008fd7;
L_180008fd7:
  if (!M.zf) goto L_180009455; goto L_180008fdd;
L_180008fdd:
  R.r9=uint32_t(M.read8((R.rbp))); goto L_180008fe2;
L_180008fe2:
  T=M.subflags(uint8_t(R.r9),M.read8((R.r8)),8);
  goto L_180008fe5;
L_180008fe5:
  if (!M.zf) goto L_180009455; goto L_180008feb;
L_180008feb:
  goto L_180009059;
L_180008fed:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_180008fef;
L_180008fef:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180008ff1;
L_180008ff1:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180008ff3;
L_180008ff3:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180008ff4;
L_180008ff4:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180008ff6;
L_180008ff6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180008ff8;
L_180008ff8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180008ffa;
L_180008ffa:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009000;
L_180009000:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_180009005;
L_180009005:
  R.r11=uint32_t(M.read8((R.rbp+0x3ull))); goto L_18000900a;
L_18000900a:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_18000900d;
L_18000900d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000900f;
L_18000900f:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009011;
L_180009011:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009012;
L_180009012:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009014;
L_180009014:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009016;
L_180009016:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009018;
L_180009018:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_18000901e;
L_18000901e:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180009023;
L_180009023:
  R.r10=uint32_t(M.read8((R.rbp+0x2ull))); goto L_180009028;
L_180009028:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_18000902b;
L_18000902b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000902d;
L_18000902d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000902f;
L_18000902f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009030;
L_180009030:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009032;
L_180009032:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009034;
L_180009034:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009036;
L_180009036:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_18000903c;
L_18000903c:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180009040;
L_180009040:
  R.r9=uint32_t(M.read8((R.rbp))); goto L_180009045;
L_180009045:
  R.rcx=uint32_t(uint32_t(R.r9)); goto L_180009048;
L_180009048:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000904a;
L_18000904a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000904c;
L_18000904c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000904d;
L_18000904d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000904f;
L_18000904f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009051;
L_180009051:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009053;
L_180009053:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009059;
L_180009059:
  R.rax=uint64_t((0x180009060-0x9060ull)); goto L_180009060;
L_180009060:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rax+(R.r15*4ull)+0xf050ull))))); goto L_180009068;
L_180009068:
  R.r8=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_18000906c;
L_18000906c:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000906f;
L_18000906f:
  if (M.zf) goto L_180009455; goto L_180009075;
L_180009075:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180009077;
L_180009077:
  if (!M.zf) goto L_1800090e0; goto L_180009079;
L_180009079:
  T=M.subflags(uint8_t(R.rbx),M.read8((R.r8+0x1ull)),8);
  goto L_18000907d;
L_18000907d:
  if (!M.zf) goto L_180009455; goto L_180009083;
L_180009083:
  T=M.subflags(uint8_t(R.r11),M.read8((R.r8+0x3ull)),8);
  goto L_180009087;
L_180009087:
  if (!M.zf) goto L_180009455; goto L_18000908d;
L_18000908d:
  T=M.subflags(uint8_t(R.r10),M.read8((R.r8+0x2ull)),8);
  goto L_180009091;
L_180009091:
  if (!M.zf) goto L_180009455; goto L_180009097;
L_180009097:
  T=M.subflags(uint8_t(R.r9),M.read8((R.r8)),8);
  goto L_18000909a;
L_18000909a:
  if (!M.zf) goto L_180009455; goto L_1800090a0;
L_1800090a0:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x88ull))))); goto L_1800090a8;
L_1800090a8:
  R.rcx=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_1800090ac;
L_1800090ac:
  T=(R.rcx) & (R.rcx); M.logicflags(T,64);
  goto L_1800090af;
L_1800090af:
  if (M.zf) goto L_180009455; goto L_1800090b5;
L_1800090b5:
  T=M.subflags(uint8_t(R.rbx),M.read8((R.rcx+0x1ull)),8);
  goto L_1800090b8;
L_1800090b8:
  if (!M.zf) goto L_180009455; goto L_1800090be;
L_1800090be:
  T=M.subflags(uint8_t(R.r11),M.read8((R.rcx+0x3ull)),8);
  goto L_1800090c2;
L_1800090c2:
  if (!M.zf) goto L_180009455; goto L_1800090c8;
L_1800090c8:
  T=M.subflags(uint8_t(R.r10),M.read8((R.rcx+0x2ull)),8);
  goto L_1800090cc;
L_1800090cc:
  if (!M.zf) goto L_180009455; goto L_1800090d2;
L_1800090d2:
  T=M.subflags(uint8_t(R.r9),M.read8((R.rcx)),8);
  goto L_1800090d5;
L_1800090d5:
  if (M.zf) goto L_1800091bf; goto L_1800090db;
L_1800090db:
  goto L_180009455;
L_1800090e0:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_1800090e5;
L_1800090e5:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_1800090e7;
L_1800090e7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800090e9;
L_1800090e9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800090eb;
L_1800090eb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800090ec;
L_1800090ec:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800090ee;
L_1800090ee:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800090f0;
L_1800090f0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800090f2;
L_1800090f2:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800090f8;
L_1800090f8:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_1800090fd;
L_1800090fd:
  R.rcx=uint32_t(uint8_t(R.r11)); goto L_180009101;
L_180009101:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009103;
L_180009103:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009105;
L_180009105:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009106;
L_180009106:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009108;
L_180009108:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000910a;
L_18000910a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000910c;
L_18000910c:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009112;
L_180009112:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180009117;
L_180009117:
  R.rcx=uint32_t(uint8_t(R.r10)); goto L_18000911b;
L_18000911b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000911d;
L_18000911d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000911f;
L_18000911f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009120;
L_180009120:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009122;
L_180009122:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009124;
L_180009124:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009126;
L_180009126:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_18000912c;
L_18000912c:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180009130;
L_180009130:
  R.rcx=uint32_t(uint8_t(R.r9)); goto L_180009134;
L_180009134:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009136;
L_180009136:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009138;
L_180009138:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009139;
L_180009139:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000913b;
L_18000913b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000913d;
L_18000913d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000913f;
L_18000913f:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009145;
L_180009145:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x88ull))))); goto L_18000914d;
L_18000914d:
  R.r8=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_180009151;
L_180009151:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_180009154;
L_180009154:
  if (M.zf) goto L_180009455; goto L_18000915a;
L_18000915a:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_18000915f;
L_18000915f:
  R.rcx=uint32_t(uint32_t(R.rbx)); goto L_180009161;
L_180009161:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009163;
L_180009163:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009165;
L_180009165:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009166;
L_180009166:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009168;
L_180009168:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000916a;
L_18000916a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000916c;
L_18000916c:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009172;
L_180009172:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_180009177;
L_180009177:
  R.rcx=uint32_t(uint8_t(R.r11)); goto L_18000917b;
L_18000917b:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000917d;
L_18000917d:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000917f;
L_18000917f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009180;
L_180009180:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009182;
L_180009182:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009184;
L_180009184:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009186;
L_180009186:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_18000918c;
L_18000918c:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180009191;
L_180009191:
  R.rcx=uint32_t(uint8_t(R.r10)); goto L_180009195;
L_180009195:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009197;
L_180009197:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009199;
L_180009199:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000919a;
L_18000919a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000919c;
L_18000919c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000919e;
L_18000919e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800091a0;
L_1800091a0:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800091a6;
L_1800091a6:
  R.rax=uint32_t(M.read8((R.r8))); goto L_1800091aa;
L_1800091aa:
  R.rcx=uint32_t(uint8_t(R.r9)); goto L_1800091ae;
L_1800091ae:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800091b0;
L_1800091b0:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800091b2;
L_1800091b2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800091b3;
L_1800091b3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800091b5;
L_1800091b5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800091b7;
L_1800091b7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800091b9;
L_1800091b9:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800091bf;
L_1800091bf:
  R.rsi=uint32_t(3ull); goto L_1800091c4;
L_1800091c4:
  goto L_180009455;
L_1800091c9:
  R.r10=uint64_t(M.read64((R.r14+(R.rsi*8ull)))); goto L_1800091cd;
L_1800091cd:
  R.r11=uint64_t(R.rbx); goto L_1800091d0;
L_1800091d0:
  goto L_1800091e2;
L_1800091d2:
  R.r10=uint64_t(M.read64((R.r14+(R.rsi*8ull)))); goto L_1800091d6;
L_1800091d6:
  R.r11=uint64_t(R.rbx); goto L_1800091d9;
L_1800091d9:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800091dc;
L_1800091dc:
  if (M.zf) goto L_18000926d; goto L_1800091e2;
L_1800091e2:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_1800091e5;
L_1800091e5:
  if (M.zf) goto L_18000926d; goto L_1800091eb;
L_1800091eb:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_1800091f0;
L_1800091f0:
  R.rcx=uint32_t(M.read8((R.r11+0x1ull))); goto L_1800091f5;
L_1800091f5:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800091f7;
L_1800091f7:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800091f9;
L_1800091f9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800091fa;
L_1800091fa:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800091fc;
L_1800091fc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800091fe;
L_1800091fe:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009200;
L_180009200:
  if (!M.zf&&(M.sf==M.of)) goto L_18000924a; goto L_180009202;
L_180009202:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_180009207;
L_180009207:
  R.rcx=uint32_t(M.read8((R.r11+0x3ull))); goto L_18000920c;
L_18000920c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000920e;
L_18000920e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009210;
L_180009210:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009211;
L_180009211:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009213;
L_180009213:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009215;
L_180009215:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009217;
L_180009217:
  if (!M.zf&&(M.sf==M.of)) goto L_18000924a; goto L_180009219;
L_180009219:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_18000921e;
L_18000921e:
  R.rcx=uint32_t(M.read8((R.r11+0x2ull))); goto L_180009223;
L_180009223:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009225;
L_180009225:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009227;
L_180009227:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009228;
L_180009228:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000922a;
L_18000922a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000922c;
L_18000922c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000922e;
L_18000922e:
  if (!M.zf&&(M.sf==M.of)) goto L_18000924a; goto L_180009230;
L_180009230:
  R.rax=uint32_t(M.read8((R.r10))); goto L_180009234;
L_180009234:
  R.rcx=uint32_t(M.read8((R.r11))); goto L_180009238;
L_180009238:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000923a;
L_18000923a:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000923c;
L_18000923c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000923d;
L_18000923d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000923f;
L_18000923f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009241;
L_180009241:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009243;
L_180009243:
  if (!M.zf&&(M.sf==M.of)) goto L_18000924a; goto L_180009245;
L_180009245:
  R.r11=(R.r11&~0xffull)|(uint8_t(1ull)); goto L_180009248;
L_180009248:
  goto L_18000924d;
L_18000924a:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_18000924d;
L_18000924d:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180009255;
L_180009255:
  R.rcx=uint64_t((0x18000925c-0x925cull)); goto L_18000925c;
L_18000925c:
  R.rsi=uint64_t(R.rbx); goto L_18000925f;
L_18000925f:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_180009267;
L_180009267:
  R.r10=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_18000926b;
L_18000926b:
  goto L_180009293;
L_18000926d:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rsp+0x90ull))))); goto L_180009275;
L_180009275:
  R.rcx=uint64_t((0x18000927c-0x927cull)); goto L_18000927c;
L_18000927c:
  T=(uint8_t(R.r11)) ^ (uint8_t(R.r11)); M.logicflags(T,8);
  R.r11=(R.r11&~0xffull)|(uint8_t(T));
  goto L_18000927f;
L_18000927f:
  R.rsi=uint64_t(R.rbx); goto L_180009282;
L_180009282:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rcx+(R.rax*4ull)+0xf078ull))))); goto L_18000928a;
L_18000928a:
  R.r10=uint64_t(M.read64((R.r14+(R.rax*8ull)))); goto L_18000928e;
L_18000928e:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180009291;
L_180009291:
  if (M.zf) goto L_1800092f2; goto L_180009293;
L_180009293:
  T=(R.r10) & (R.r10); M.logicflags(T,64);
  goto L_180009296;
L_180009296:
  if (M.zf) goto L_1800092f2; goto L_180009298;
L_180009298:
  R.rax=uint32_t(M.read8((R.r10+0x1ull))); goto L_18000929d;
L_18000929d:
  R.rcx=uint32_t(M.read8((R.rsi+0x1ull))); goto L_1800092a1;
L_1800092a1:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800092a3;
L_1800092a3:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800092a5;
L_1800092a5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800092a6;
L_1800092a6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800092a8;
L_1800092a8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800092aa;
L_1800092aa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800092ac;
L_1800092ac:
  if (!M.zf&&(M.sf==M.of)) goto L_1800092f2; goto L_1800092ae;
L_1800092ae:
  R.rax=uint32_t(M.read8((R.r10+0x3ull))); goto L_1800092b3;
L_1800092b3:
  R.rcx=uint32_t(M.read8((R.rsi+0x3ull))); goto L_1800092b7;
L_1800092b7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800092b9;
L_1800092b9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800092bb;
L_1800092bb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800092bc;
L_1800092bc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800092be;
L_1800092be:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800092c0;
L_1800092c0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800092c2;
L_1800092c2:
  if (!M.zf&&(M.sf==M.of)) goto L_1800092f2; goto L_1800092c4;
L_1800092c4:
  R.rax=uint32_t(M.read8((R.r10+0x2ull))); goto L_1800092c9;
L_1800092c9:
  R.rcx=uint32_t(M.read8((R.rsi+0x2ull))); goto L_1800092cd;
L_1800092cd:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800092cf;
L_1800092cf:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800092d1;
L_1800092d1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800092d2;
L_1800092d2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800092d4;
L_1800092d4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800092d6;
L_1800092d6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800092d8;
L_1800092d8:
  if (!M.zf&&(M.sf==M.of)) goto L_1800092f2; goto L_1800092da;
L_1800092da:
  R.rax=uint32_t(M.read8((R.r10))); goto L_1800092de;
L_1800092de:
  R.rcx=uint32_t(M.read8((R.rsi))); goto L_1800092e1;
L_1800092e1:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800092e3;
L_1800092e3:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800092e5;
L_1800092e5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800092e6;
L_1800092e6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800092e8;
L_1800092e8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800092ea;
L_1800092ea:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800092ec;
L_1800092ec:
  if (!M.zf&&(M.sf==M.of)) goto L_1800092f2; goto L_1800092ee;
L_1800092ee:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_1800092f0;
L_1800092f0:
  goto L_1800092f4;
L_1800092f2:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_1800092f4;
L_1800092f4:
  R.rsi=uint32_t(uint32_t(R.rbp)); goto L_1800092f6;
L_1800092f6:
  T=M.subflags(uint8_t(R.rax),uint8_t(R.r11),8);
  goto L_1800092f9;
L_1800092f9:
  if (M.zf) goto L_180009455; goto L_1800092ff;
L_1800092ff:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180009301;
L_180009301:
  if (!M.zf) goto L_180009388; goto L_180009307;
L_180009307:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000930a;
L_18000930a:
  if (M.zf) goto L_18000933b; goto L_18000930c;
L_18000930c:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_18000930f;
L_18000930f:
  if (M.zf) goto L_18000933b; goto L_180009311;
L_180009311:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_180009316;
L_180009316:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180009319;
L_180009319:
  if (!M.zf) goto L_18000933b; goto L_18000931b;
L_18000931b:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_180009320;
L_180009320:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180009323;
L_180009323:
  if (!M.zf) goto L_18000933b; goto L_180009325;
L_180009325:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_18000932a;
L_18000932a:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_18000932d;
L_18000932d:
  if (!M.zf) goto L_18000933b; goto L_18000932f;
L_18000932f:
  R.rax=uint32_t(M.read8((R.r15))); goto L_180009333;
L_180009333:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180009335;
L_180009335:
  if (!M.zf) goto L_18000933b; goto L_180009337;
L_180009337:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009339;
L_180009339:
  goto L_18000933d;
L_18000933b:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_18000933d;
L_18000933d:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_18000933f;
L_18000933f:
  if (M.zf) goto L_180009455; goto L_180009345;
L_180009345:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180009348;
L_180009348:
  if (M.zf) goto L_180009379; goto L_18000934a;
L_18000934a:
  T=(R.r8) & (R.r8); M.logicflags(T,64);
  goto L_18000934d;
L_18000934d:
  if (M.zf) goto L_180009379; goto L_18000934f;
L_18000934f:
  R.rax=uint32_t(M.read8((R.r8+0x1ull))); goto L_180009354;
L_180009354:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180009357;
L_180009357:
  if (!M.zf) goto L_180009379; goto L_180009359;
L_180009359:
  R.rax=uint32_t(M.read8((R.r8+0x3ull))); goto L_18000935e;
L_18000935e:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180009361;
L_180009361:
  if (!M.zf) goto L_180009379; goto L_180009363;
L_180009363:
  R.rax=uint32_t(M.read8((R.r8+0x2ull))); goto L_180009368;
L_180009368:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_18000936b;
L_18000936b:
  if (!M.zf) goto L_180009379; goto L_18000936d;
L_18000936d:
  R.rax=uint32_t(M.read8((R.r8))); goto L_180009371;
L_180009371:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180009373;
L_180009373:
  if (!M.zf) goto L_180009379; goto L_180009375;
L_180009375:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180009377;
L_180009377:
  goto L_18000937b;
L_180009379:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_18000937b;
L_18000937b:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_18000937d;
L_18000937d:
  if (M.zf) goto L_180009455; goto L_180009383;
L_180009383:
  goto L_180009453;
L_180009388:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000938b;
L_18000938b:
  if (M.zf) goto L_180009455; goto L_180009391;
L_180009391:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180009394;
L_180009394:
  if (M.zf) goto L_180009455; goto L_18000939a;
L_18000939a:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_18000939f;
L_18000939f:
  R.rcx=uint32_t(M.read8((R.rbx+0x1ull))); goto L_1800093a3;
L_1800093a3:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800093a5;
L_1800093a5:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800093a7;
L_1800093a7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800093a8;
L_1800093a8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800093aa;
L_1800093aa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800093ac;
L_1800093ac:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800093ae;
L_1800093ae:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800093b4;
L_1800093b4:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_1800093b9;
L_1800093b9:
  R.rcx=uint32_t(M.read8((R.rbx+0x3ull))); goto L_1800093bd;
L_1800093bd:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800093bf;
L_1800093bf:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800093c1;
L_1800093c1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800093c2;
L_1800093c2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800093c4;
L_1800093c4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800093c6;
L_1800093c6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800093c8;
L_1800093c8:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800093ce;
L_1800093ce:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_1800093d3;
L_1800093d3:
  R.rcx=uint32_t(M.read8((R.rbx+0x2ull))); goto L_1800093d7;
L_1800093d7:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800093d9;
L_1800093d9:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800093db;
L_1800093db:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800093dc;
L_1800093dc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800093de;
L_1800093de:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800093e0;
L_1800093e0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800093e2;
L_1800093e2:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800093e4;
L_1800093e4:
  R.rax=uint32_t(M.read8((R.r15))); goto L_1800093e8;
L_1800093e8:
  R.rcx=uint32_t(M.read8((R.rbx))); goto L_1800093eb;
L_1800093eb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_1800093ed;
L_1800093ed:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_1800093ef;
L_1800093ef:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800093f0;
L_1800093f0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800093f2;
L_1800093f2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800093f4;
L_1800093f4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800093f6;
L_1800093f6:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_1800093f8;
L_1800093f8:
  T=(R.r9) & (R.r9); M.logicflags(T,64);
  goto L_1800093fb;
L_1800093fb:
  if (M.zf) goto L_180009455; goto L_1800093fd;
L_1800093fd:
  R.rax=uint32_t(M.read8((R.r9+0x1ull))); goto L_180009402;
L_180009402:
  R.rcx=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180009406;
L_180009406:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009408;
L_180009408:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000940a;
L_18000940a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000940b;
L_18000940b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000940d;
L_18000940d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000940f;
L_18000940f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009411;
L_180009411:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009413;
L_180009413:
  R.rax=uint32_t(M.read8((R.r9+0x3ull))); goto L_180009418;
L_180009418:
  R.rcx=uint32_t(M.read8((R.rbx+0x3ull))); goto L_18000941c;
L_18000941c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_18000941e;
L_18000941e:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009420;
L_180009420:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009421;
L_180009421:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009423;
L_180009423:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180009425;
L_180009425:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009427;
L_180009427:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009429;
L_180009429:
  R.rax=uint32_t(M.read8((R.r9+0x2ull))); goto L_18000942e;
L_18000942e:
  R.rcx=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180009432;
L_180009432:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009434;
L_180009434:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_180009436;
L_180009436:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180009437;
L_180009437:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180009439;
L_180009439:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000943b;
L_18000943b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000943d;
L_18000943d:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_18000943f;
L_18000943f:
  R.rax=uint32_t(M.read8((R.r9))); goto L_180009443;
L_180009443:
  R.rcx=uint32_t(M.read8((R.rbx))); goto L_180009446;
L_180009446:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  R.rcx=uint32_t(T);
  goto L_180009448;
L_180009448:
  R.rax=uint32_t(uint32_t(R.rcx)); goto L_18000944a;
L_18000944a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000944b;
L_18000944b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000944d;
L_18000944d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000944f;
L_18000944f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180009451;
L_180009451:
  if (!M.zf&&(M.sf==M.of)) goto L_180009455; goto L_180009453;
L_180009453:
  T=(uint32_t(R.rsi)) ^ (uint32_t(R.rsi)); M.logicflags(T,32);
  R.rsi=uint32_t(T);
  goto L_180009455;
L_180009455:
  R.rbp=uint64_t(M.read64((R.rsp+0x78ull))); goto L_18000945a;
L_18000945a:
  R.r12=uint64_t(M.read64((R.rsp+0x30ull))); goto L_18000945f;
L_18000945f:
  R.rax=uint32_t(uint32_t(R.rsi)); goto L_180009461;
L_180009461:
  R.rsp=uint64_t((R.rsp)+(0x38ull)); goto L_180009465;
L_180009465:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009467;
L_180009467:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180009469;
L_180009469:
  R.r13=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000946b;
L_18000946b:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000946c;
L_18000946c:
  R.rsi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000946d;
L_18000946d:
  R.rbx=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_18000946e;
L_18000946e:
  return int32_t(uint32_t(R.rax));
