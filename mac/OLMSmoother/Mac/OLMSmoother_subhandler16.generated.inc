// Generated from olmsmoother_v1_subhandler16_cfg_20260806.json; do not hand edit.
L_180002740:
  M.write32((R.rsp+0x20ull), uint32_t(R.r9)); goto L_180002745;
L_180002745:
  M.write32((R.rsp+0x18ull), uint32_t(R.r8)); goto L_18000274a;
L_18000274a:
  M.write64((R.rsp+0x8ull), R.rcx); goto L_18000274f;
L_18000274f:
  R.rsp-=8; M.write64(R.rsp,R.rbp); goto L_180002750;
L_180002750:
  R.rsp-=8; M.write64(R.rsp,R.rbx); goto L_180002751;
L_180002751:
  R.rsp-=8; M.write64(R.rsp,R.rsi); goto L_180002752;
L_180002752:
  R.rsp-=8; M.write64(R.rsp,R.rdi); goto L_180002753;
L_180002753:
  R.rsp-=8; M.write64(R.rsp,R.r12); goto L_180002755;
L_180002755:
  R.rsp-=8; M.write64(R.rsp,R.r13); goto L_180002757;
L_180002757:
  R.rsp-=8; M.write64(R.rsp,R.r14); goto L_180002759;
L_180002759:
  R.rsp-=8; M.write64(R.rsp,R.r15); goto L_18000275b;
L_18000275b:
  R.rbp=uint64_t(R.rsp); goto L_18000275e;
L_18000275e:
  T=M.subflags(R.rsp,0x68ull,64);
  R.rsp=uint64_t(T);
  goto L_180002762;
L_180002762:
  R.rax=uint64_t(M.read64((R.rbp+0x88ull))); goto L_180002769;
L_180002769:
  R.rbx=uint64_t((0x180002770-0x2770ull)); goto L_180002770;
L_180002770:
  R.r10=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002777;
L_180002777:
  R.r11=uint32_t(uint32_t(R.r9)); goto L_18000277a;
L_18000277a:
  R.r13=uint64_t(M.read64((R.rbp+0xb0ull))); goto L_180002781;
L_180002781:
  R.r9=uint32_t(uint32_t(R.r8)); goto L_180002784;
L_180002784:
  M.write32((R.rax), uint32_t(R.r8)); goto L_180002787;
L_180002787:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_18000278e;
L_18000278e:
  M.write32((R.r10), uint32_t(R.r11)); goto L_180002791;
L_180002791:
  M.write32((R.rax), uint32_t(R.r8)); goto L_180002794;
L_180002794:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_18000279b;
L_18000279b:
  M.write32((R.rax), uint32_t(R.r11)); goto L_18000279e;
L_18000279e:
  R.rax=uint64_t(M.read64((R.rbp+0xa8ull))); goto L_1800027a5;
L_1800027a5:
  M.write32((R.rax), uint32_t(R.r8)); goto L_1800027a8;
L_1800027a8:
  R.rax=uint64_t(M.read64((R.rbp+0x78ull))); goto L_1800027ac;
L_1800027ac:
  M.write32((R.r13), uint32_t(R.r11)); goto L_1800027b0;
L_1800027b0:
  M.write8((R.rax), 0ull); goto L_1800027b3;
L_1800027b3:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_1800027ba;
L_1800027ba:
  M.write8((R.rax), 0ull); goto L_1800027bd;
L_1800027bd:
  R.rax=uint32_t(M.read32((R.rcx+0x10ull))); goto L_1800027c0;
L_1800027c0:
  R.r8=uint32_t(M.read32((R.rcx+0xcull))); goto L_1800027c4;
L_1800027c4:
  R.rdi=uint32_t(uint32_t(R.r8)); goto L_1800027c7;
L_1800027c7:
  R.rcx=uint64_t(int64_t(int32_t(M.read32((R.rbp+0x68ull))))); goto L_1800027cb;
L_1800027cb:
  M.write32((R.rbp-0x28ull), uint32_t(R.rax)); goto L_1800027ce;
L_1800027ce:
  M.write32((R.rbp+0xb0ull), uint32_t(R.r8)); goto L_1800027d5;
L_1800027d5:
  R.rdi=uint32_t((uint32_t(R.rdi))<<((7ull)&0x3f)); goto L_1800027d8;
L_1800027d8:
  R.rax=uint32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf0c8ull))); goto L_1800027df;
L_1800027df:
  R.r10=uint64_t(int64_t(int32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf000ull))))); goto L_1800027e7;
L_1800027e7:
  T=M.addflags(uint32_t(R.rax),uint32_t(R.r9),32); R.rax=uint32_t(T); goto L_1800027ea;
L_1800027ea:
  R.r9=uint64_t(int64_t(int32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf028ull))))); goto L_1800027f2;
L_1800027f2:
  M.write32((R.rbp-0x24ull), uint32_t(R.rax)); goto L_1800027f5;
L_1800027f5:
  R.rax=uint32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf0f0ull))); goto L_1800027fc;
L_1800027fc:
  R.rsi=uint64_t(M.read64((R.rdx+(R.r10*8ull)))); goto L_180002800;
L_180002800:
  T=M.addflags(uint32_t(R.rax),uint32_t(R.r11),32); R.rax=uint32_t(T); goto L_180002803;
L_180002803:
  R.r14=uint64_t(M.read64((R.rdx+(R.r9*8ull)))); goto L_180002807;
L_180002807:
  M.write32((R.rbp+0x50ull), uint32_t(R.rax)); goto L_18000280a;
L_18000280a:
  R.rax=uint32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf0a0ull))); goto L_180002811;
L_180002811:
  M.write32((R.rbp-0x20ull), uint32_t(R.rax)); goto L_180002814;
L_180002814:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf050ull))))); goto L_18000281c;
L_18000281c:
  M.write32((R.rbp-0x18ull), uint32_t(R.r10)); goto L_180002820;
L_180002820:
  M.write32((R.rbp-0x1cull), uint32_t(R.r9)); goto L_180002824;
L_180002824:
  R.r12=uint64_t(M.read64((R.rdx+(R.rax*8ull)))); goto L_180002828;
L_180002828:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rbx+(R.rcx*4ull)+0xf078ull))))); goto L_180002830;
L_180002830:
  R.rbx=uint64_t(M.read64((R.rdx+0x20ull))); goto L_180002834;
L_180002834:
  R.r15=uint64_t(M.read64((R.rdx+(R.rax*8ull)))); goto L_180002838;
L_180002838:
  R.rax=uint64_t(M.read64((R.rdx+(R.rcx*8ull)))); goto L_18000283c;
L_18000283c:
  R.rdx=uint64_t(R.rbx); goto L_18000283f;
L_18000283f:
  R.rcx=uint64_t(R.r12); goto L_180002842;
L_180002842:
  M.write64((R.rbp-0x10ull), R.rax); goto L_180002846;
L_180002846:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_18000284b;
L_18000284b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000284d;
L_18000284d:
  if (M.zf||(M.sf!=M.of)) goto L_180002a85; goto L_180002853;
L_180002853:
  R.rdx=uint64_t(R.rbx); goto L_180002856;
L_180002856:
  R.rcx=uint64_t(R.r15); goto L_180002859;
L_180002859:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_18000285e;
L_18000285e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002860;
L_180002860:
  if (M.zf||(M.sf!=M.of)) goto L_180002a85; goto L_180002866;
L_180002866:
  R.rdx=uint64_t(R.rbx); goto L_180002869;
L_180002869:
  R.rcx=uint64_t(R.rsi); goto L_18000286c;
L_18000286c:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180002871;
L_180002871:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002873;
L_180002873:
  if (M.zf||(M.sf!=M.of)) goto L_180002a85; goto L_180002879;
L_180002879:
  R.rdx=uint64_t(R.rbx); goto L_18000287c;
L_18000287c:
  R.rcx=uint64_t(R.r14); goto L_18000287f;
L_18000287f:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180002884;
L_180002884:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002886;
L_180002886:
  if (M.zf||(M.sf!=M.of)) goto L_180002a85; goto L_18000288c;
L_18000288c:
  R.r14=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180002890;
L_180002890:
  R.rdx=uint32_t(uint32_t(R.r14)); goto L_180002893;
L_180002893:
  R.r12=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180002897;
L_180002897:
  R.r8=uint32_t(uint32_t(R.r12)); goto L_18000289a;
L_18000289a:
  R.r15=uint64_t(M.read64((R.rbp+0x88ull))); goto L_1800028a1;
L_1800028a1:
  R.rax=uint64_t(M.read64((R.rbp+0x90ull))); goto L_1800028a8;
L_1800028a8:
  R.rsi=uint32_t(M.read32((R.rbp-0x28ull))); goto L_1800028ab;
L_1800028ab:
  R.r9=uint32_t(M.read32((R.rbp-0x18ull))); goto L_1800028af;
L_1800028af:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_1800028b3;
L_1800028b3:
  M.write32((R.rsp+0x38ull), uint32_t(R.rsi)); goto L_1800028b7;
L_1800028b7:
  M.write32((R.r15), uint32_t(R.r14)); goto L_1800028ba;
L_1800028ba:
  M.write32((R.rax), uint32_t(R.r12)); goto L_1800028bd;
L_1800028bd:
  R.rax=uint64_t((R.rbp+0x80ull)); goto L_1800028c4;
L_1800028c4:
  M.write64((R.rsp+0x30ull), R.rax); goto L_1800028c9;
L_1800028c9:
  R.rax=uint64_t((R.rbp+0x58ull)); goto L_1800028cd;
L_1800028cd:
  M.write64((R.rsp+0x28ull), R.rax); goto L_1800028d2;
L_1800028d2:
  R.rax=uint32_t(M.read32((R.rbp-0x20ull))); goto L_1800028d5;
L_1800028d5:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_1800028d9;
L_1800028d9:
  M.write32((R.rbp+0x58ull), uint32_t(R.r14)); goto L_1800028dd;
L_1800028dd:
  M.write32((R.rbp+0x80ull), uint32_t(R.r12)); goto L_1800028e4;
L_1800028e4:
  M.write32((R.rbp+0x68ull), uint32_t(R.r14)); goto L_1800028e8;
L_1800028e8:
  M.write32((R.rbp+0x88ull), uint32_t(R.r12)); goto L_1800028ef;
L_1800028ef:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_1800028f4;
L_1800028f4:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_1800028f8;
L_1800028f8:
  R.rbx=uint32_t(uint32_t(R.rax)); goto L_1800028fa;
L_1800028fa:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_1800028fe;
L_1800028fe:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_180002905;
L_180002905:
  M.write32((R.rsp+0x38ull), uint32_t(R.rsi)); goto L_180002909;
L_180002909:
  R.r8=uint32_t(uint32_t(R.r12)); goto L_18000290c;
L_18000290c:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180002911;
L_180002911:
  R.rdx=uint32_t(uint32_t(R.r14)); goto L_180002914;
L_180002914:
  R.rax=uint64_t((R.rbp+0x68ull)); goto L_180002918;
L_180002918:
  M.write64((R.rsp+0x28ull), R.rax); goto L_18000291d;
L_18000291d:
  R.rax=uint32_t(M.read32((R.rbp-0x20ull))); goto L_180002920;
L_180002920:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180002924;
L_180002924:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180002929;
L_180002929:
  R.r11=uint32_t(M.read32((R.rbp+0x68ull))); goto L_18000292d;
L_18000292d:
  R.rdi=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180002930;
L_180002930:
  R.rcx=uint32_t(uint32_t(R.rdi)); goto L_180002932;
L_180002932:
  R.r9=uint32_t(M.read32((R.rbp+0x88ull))); goto L_180002939;
L_180002939:
  R.r10=uint32_t(M.read32((R.rbp+0x80ull))); goto L_180002940;
L_180002940:
  R.r8=uint64_t(M.read64((R.rbp+0xa8ull))); goto L_180002947;
L_180002947:
  M.write32((R.rbp+0xb0ull), uint32_t(R.rax)); goto L_18000294d;
L_18000294d:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180002950;
L_180002950:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r14),32);
  R.rax=uint32_t(T);
  goto L_180002953;
L_180002953:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002954;
L_180002954:
  R.rsi=uint32_t(uint32_t(R.rax)); goto L_180002956;
L_180002956:
  M.write32((R.r8), uint32_t(R.r14)); goto L_180002959;
L_180002959:
  T=(uint32_t(R.rsi)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rsi=uint32_t(T);
  goto L_18000295b;
L_18000295b:
  M.write32((R.r13), uint32_t(R.r12)); goto L_18000295f;
L_18000295f:
  T=M.subflags(uint32_t(R.rsi),uint32_t(R.rdx),32);
  R.rsi=uint32_t(T);
  goto L_180002961;
L_180002961:
  R.rax=uint32_t(uint32_t(R.rdi)); goto L_180002963;
L_180002963:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r14),32);
  R.rax=uint32_t(T);
  goto L_180002966;
L_180002966:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002967;
L_180002967:
  R.r14=uint32_t(uint32_t(R.rax)); goto L_18000296a;
L_18000296a:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180002971;
L_180002971:
  T=(uint32_t(R.r14)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r14=uint32_t(T);
  goto L_180002974;
L_180002974:
  T=M.subflags(uint32_t(R.r14),uint32_t(R.rdx),32);
  R.r14=uint32_t(T);
  goto L_180002977;
L_180002977:
  T=M.subflags(uint32_t(R.rsi),uint32_t(R.r14),32);
  goto L_18000297a;
L_18000297a:
  if(M.sf!=M.of){R.rcx=uint32_t(uint32_t(R.r11));} goto L_18000297e;
L_18000297e:
  M.write32((R.rax), uint32_t(R.rcx)); goto L_180002980;
L_180002980:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180002983;
L_180002983:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r12),32);
  R.rax=uint32_t(T);
  goto L_180002986;
L_180002986:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_180002989;
L_180002989:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000298a;
L_18000298a:
  R.r12=uint32_t(uint32_t(R.rax)); goto L_18000298d;
L_18000298d:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180002990;
L_180002990:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rbp+0x60ull)),32);
  R.rax=uint32_t(T);
  goto L_180002993;
L_180002993:
  T=(uint32_t(R.r12)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r12=uint32_t(T);
  goto L_180002996;
L_180002996:
  T=M.subflags(uint32_t(R.r12),uint32_t(R.rdx),32);
  R.r12=uint32_t(T);
  goto L_180002999;
L_180002999:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000299a;
L_18000299a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000299c;
L_18000299c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000299e;
L_18000299e:
  R.rdx=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_1800029a5;
L_1800029a5:
  T=M.subflags(uint32_t(R.r12),uint32_t(R.rax),32);
  goto L_1800029a8;
L_1800029a8:
  M.write32((R.rbp+0x60ull), uint32_t(R.rax)); goto L_1800029ab;
L_1800029ab:
  if(M.sf!=M.of){R.rcx=uint32_t(uint32_t(R.r9));} goto L_1800029af;
L_1800029af:
  M.write32((R.rdx), uint32_t(R.rcx)); goto L_1800029b1;
L_1800029b1:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_1800029b3;
L_1800029b3:
  if (!M.zf) goto L_1800029c5; goto L_1800029b5;
L_1800029b5:
  T=M.subflags(M.read32((R.rbp+0xb0ull)),uint32_t(R.rbx),32);
  goto L_1800029bb;
L_1800029bb:
  if (!M.zf) goto L_1800029c5; goto L_1800029bd;
L_1800029bd:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_1800029c1;
L_1800029c1:
  M.write32((R.rax), uint32_t(R.rbx)); goto L_1800029c3;
L_1800029c3:
  goto L_180002a41;
L_1800029c5:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_1800029c9;
L_1800029c9:
  M.write32((R.rax), 1ull); goto L_1800029cf;
L_1800029cf:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_1800029d6;
L_1800029d6:
  T=M.subflags(uint32_t(R.rsi),uint32_t(R.r14),32);
  goto L_1800029d9;
L_1800029d9:
  if (M.zf||(M.sf!=M.of)) goto L_1800029e3; goto L_1800029db;
L_1800029db:
  M.write32((R.rax), uint32_t(R.r11)); goto L_1800029de;
L_1800029de:
  M.write32((R.r8), uint32_t(R.rdi)); goto L_1800029e1;
L_1800029e1:
  goto L_1800029e8;
L_1800029e3:
  M.write32((R.rax), uint32_t(R.rdi)); goto L_1800029e5;
L_1800029e5:
  M.write32((R.r8), uint32_t(R.r11)); goto L_1800029e8;
L_1800029e8:
  T=M.subflags(uint32_t(R.r12),M.read32((R.rbp+0x60ull)),32);
  goto L_1800029ec;
L_1800029ec:
  if (M.zf||(M.sf!=M.of)) goto L_1800029f7; goto L_1800029ee;
L_1800029ee:
  M.write32((R.rdx), uint32_t(R.r9)); goto L_1800029f1;
L_1800029f1:
  M.write32((R.r13), uint32_t(R.r10)); goto L_1800029f5;
L_1800029f5:
  goto L_1800029fe;
L_1800029f7:
  M.write32((R.rdx), uint32_t(R.r10)); goto L_1800029fa;
L_1800029fa:
  M.write32((R.r13), uint32_t(R.r9)); goto L_1800029fe;
L_1800029fe:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rbp-0x20ull))))); goto L_180002a02;
L_180002a02:
  R.r9=uint64_t((0x180002a09-0x2a09ull)); goto L_180002a09;
L_180002a09:
  R.rcx=uint32_t(M.read32((R.r9+(R.rax*4ull)+0xf0c8ull))); goto L_180002a11;
L_180002a11:
  T=M.addflags(uint32_t(R.rcx),M.read32((R.r8)),32); R.rcx=uint32_t(T); goto L_180002a14;
L_180002a14:
  T=(uint32_t(R.rcx)) & (uint32_t(R.rcx)); M.logicflags(T,32);
  goto L_180002a16;
L_180002a16:
  if (M.zf||(M.sf!=M.of)) goto L_180002a41; goto L_180002a18;
L_180002a18:
  R.r10=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180002a1c;
L_180002a1c:
  R.rdx=uint64_t(M.read64((R.r10+0x18ull))); goto L_180002a20;
L_180002a20:
  T=M.subflags(uint32_t(R.rcx),M.read32((R.rdx+0x24ull)),32);
  goto L_180002a23;
L_180002a23:
  if (M.sf==M.of) goto L_180002a41; goto L_180002a25;
L_180002a25:
  R.rax=uint32_t(M.read32((R.r9+(R.rax*4ull)+0xf0f0ull))); goto L_180002a2d;
L_180002a2d:
  T=M.addflags(uint32_t(R.rax),M.read32((R.r13)),32); R.rax=uint32_t(T); goto L_180002a31;
L_180002a31:
  T=(uint32_t(R.rax)) & (uint32_t(R.rax)); M.logicflags(T,32);
  goto L_180002a33;
L_180002a33:
  if (M.zf||(M.sf!=M.of)) goto L_180002a41; goto L_180002a35;
L_180002a35:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rdx+0x28ull)),32);
  goto L_180002a38;
L_180002a38:
  if (M.sf==M.of) goto L_180002a41; goto L_180002a3a;
L_180002a3a:
  M.write32((R.r8), uint32_t(R.rcx)); goto L_180002a3d;
L_180002a3d:
  M.write32((R.r13), uint32_t(R.rax)); goto L_180002a41;
L_180002a41:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180002a48;
L_180002a48:
  R.r10=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002a4f;
L_180002a4f:
  R.rax=uint32_t(M.read32((R.rax))); goto L_180002a51;
L_180002a51:
  T=M.subflags(uint32_t(R.rax),M.read32((R.r15)),32);
  R.rax=uint32_t(T);
  goto L_180002a54;
L_180002a54:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002a55;
L_180002a55:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180002a57;
L_180002a57:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180002a5e;
L_180002a5e:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180002a60;
L_180002a60:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180002a62;
L_180002a62:
  R.rax=uint32_t(M.read32((R.rax))); goto L_180002a64;
L_180002a64:
  T=M.subflags(uint32_t(R.rax),M.read32((R.r10)),32);
  R.rax=uint32_t(T);
  goto L_180002a67;
L_180002a67:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002a68;
L_180002a68:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002a6a;
L_180002a6a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002a6c;
L_180002a6c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180002a6e;
L_180002a6e:
  if(!M.zf&&(M.sf==M.of)){R.rax=uint32_t(uint32_t(R.rcx));} goto L_180002a71;
L_180002a71:
  T=(uint8_t(R.rax)) & (1ull); M.logicflags(T,8);
  goto L_180002a73;
L_180002a73:
  if (!M.zf) goto L_1800033b3; goto L_180002a79;
L_180002a79:
  R.rax=uint64_t(M.read64((R.rbp+0x78ull))); goto L_180002a7d;
L_180002a7d:
  M.write8((R.rax), 1ull); goto L_180002a80;
L_180002a80:
  goto L_1800033b3;
L_180002a85:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180002a89;
L_180002a89:
  R.r13=uint64_t(M.read64((R.rbp+0x88ull))); goto L_180002a90;
L_180002a90:
  R.r8=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180002a94;
L_180002a94:
  R.r9=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180002a98;
L_180002a98:
  M.write32((R.rax), 2ull); goto L_180002a9e;
L_180002a9e:
  R.rax=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002aa5;
L_180002aa5:
  M.write32((R.r13), uint32_t(R.r8)); goto L_180002aa9;
L_180002aa9:
  M.write32((R.rbp+0xa8ull), uint32_t(R.r8)); goto L_180002ab0;
L_180002ab0:
  M.write32((R.rbp+0x88ull), uint32_t(R.r9)); goto L_180002ab7;
L_180002ab7:
  M.write32((R.rax), uint32_t(R.r9)); goto L_180002aba;
L_180002aba:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180002abd;
L_180002abd:
  if (M.zf) goto L_180002b5c; goto L_180002ac3;
L_180002ac3:
  T=M.subflags(M.read32((R.rbp+0xb0ull)),0ull,32);
  goto L_180002aca;
L_180002aca:
  if (!M.zf) goto L_180002b05; goto L_180002acc;
L_180002acc:
  T=(R.r12) & (R.r12); M.logicflags(T,64);
  goto L_180002acf;
L_180002acf:
  if (M.zf) goto L_180002b5c; goto L_180002ad5;
L_180002ad5:
  R.rax=uint32_t(M.read16((R.r12+0x2ull))); goto L_180002adb;
L_180002adb:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180002adf;
L_180002adf:
  if (!M.zf) goto L_180002b5c; goto L_180002ae1;
L_180002ae1:
  R.rax=uint32_t(M.read16((R.r12+0x6ull))); goto L_180002ae7;
L_180002ae7:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180002aeb;
L_180002aeb:
  if (!M.zf) goto L_180002b5c; goto L_180002aed;
L_180002aed:
  R.rax=uint32_t(M.read16((R.r12+0x4ull))); goto L_180002af3;
L_180002af3:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180002af7;
L_180002af7:
  if (!M.zf) goto L_180002b5c; goto L_180002af9;
L_180002af9:
  R.rax=uint32_t(M.read16((R.r12))); goto L_180002afe;
L_180002afe:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180002b01;
L_180002b01:
  if (!M.zf) goto L_180002b5c; goto L_180002b03;
L_180002b03:
  goto L_180002b6f;
L_180002b05:
  T=(R.r12) & (R.r12); M.logicflags(T,64);
  goto L_180002b08;
L_180002b08:
  if (M.zf) goto L_180002b5c; goto L_180002b0a;
L_180002b0a:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002b0e;
L_180002b0e:
  R.rcx=uint32_t(M.read16((R.r12+0x2ull))); goto L_180002b14;
L_180002b14:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002b16;
L_180002b16:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002b17;
L_180002b17:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002b19;
L_180002b19:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002b1b;
L_180002b1b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002b1d;
L_180002b1d:
  if (!M.zf&&(M.sf==M.of)) goto L_180002b5c; goto L_180002b1f;
L_180002b1f:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002b23;
L_180002b23:
  R.rcx=uint32_t(M.read16((R.r12+0x6ull))); goto L_180002b29;
L_180002b29:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002b2b;
L_180002b2b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002b2c;
L_180002b2c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002b2e;
L_180002b2e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002b30;
L_180002b30:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002b32;
L_180002b32:
  if (!M.zf&&(M.sf==M.of)) goto L_180002b5c; goto L_180002b34;
L_180002b34:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002b38;
L_180002b38:
  R.rcx=uint32_t(M.read16((R.r12+0x4ull))); goto L_180002b3e;
L_180002b3e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002b40;
L_180002b40:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002b41;
L_180002b41:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002b43;
L_180002b43:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002b45;
L_180002b45:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002b47;
L_180002b47:
  if (!M.zf&&(M.sf==M.of)) goto L_180002b5c; goto L_180002b49;
L_180002b49:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_180002b4c;
L_180002b4c:
  R.rcx=uint32_t(M.read16((R.r12))); goto L_180002b51;
L_180002b51:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002b53;
L_180002b53:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002b54;
L_180002b54:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002b56;
L_180002b56:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002b58;
L_180002b58:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002b5a;
L_180002b5a:
  if (M.zf||(M.sf!=M.of)) goto L_180002b6f; goto L_180002b5c;
L_180002b5c:
  R.rdx=uint64_t(R.r12); goto L_180002b5f;
L_180002b5f:
  R.rcx=uint64_t(R.rbx); goto L_180002b62;
L_180002b62:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180002b67;
L_180002b67:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002b69;
L_180002b69:
  if (M.zf||(M.sf!=M.of)) goto L_180002d0a; goto L_180002b6f;
L_180002b6f:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180002b72;
L_180002b72:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002b79;
L_180002b79:
  R.r9=uint32_t(M.read32((R.rbp-0x18ull))); goto L_180002b7d;
L_180002b7d:
  R.r8=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180002b81;
L_180002b81:
  R.rdx=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180002b84;
L_180002b84:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180002b88;
L_180002b88:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180002b8c;
L_180002b8c:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180002b8f;
L_180002b8f:
  M.write64((R.rsp+0x30ull), R.r12); goto L_180002b94;
L_180002b94:
  M.write64((R.rsp+0x28ull), R.r13); goto L_180002b99;
L_180002b99:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180002b9d;
L_180002b9d:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180002ba2;
L_180002ba2:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180002ba5;
L_180002ba5:
  if (M.zf) goto L_180002c38; goto L_180002bab;
L_180002bab:
  T=M.subflags(M.read32((R.rbp+0xb0ull)),0ull,32);
  goto L_180002bb2;
L_180002bb2:
  if (!M.zf) goto L_180002be5; goto L_180002bb4;
L_180002bb4:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180002bb7;
L_180002bb7:
  if (M.zf) goto L_180002c38; goto L_180002bb9;
L_180002bb9:
  R.rax=uint32_t(M.read16((R.r15+0x2ull))); goto L_180002bbe;
L_180002bbe:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180002bc2;
L_180002bc2:
  if (!M.zf) goto L_180002c38; goto L_180002bc4;
L_180002bc4:
  R.rax=uint32_t(M.read16((R.r15+0x6ull))); goto L_180002bc9;
L_180002bc9:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180002bcd;
L_180002bcd:
  if (!M.zf) goto L_180002c38; goto L_180002bcf;
L_180002bcf:
  R.rax=uint32_t(M.read16((R.r15+0x4ull))); goto L_180002bd4;
L_180002bd4:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180002bd8;
L_180002bd8:
  if (!M.zf) goto L_180002c38; goto L_180002bda;
L_180002bda:
  R.rax=uint32_t(M.read16((R.r15))); goto L_180002bde;
L_180002bde:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180002be1;
L_180002be1:
  if (!M.zf) goto L_180002c38; goto L_180002be3;
L_180002be3:
  goto L_180002c47;
L_180002be5:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180002be8;
L_180002be8:
  if (M.zf) goto L_180002c38; goto L_180002bea;
L_180002bea:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002bee;
L_180002bee:
  R.rcx=uint32_t(M.read16((R.r15+0x2ull))); goto L_180002bf3;
L_180002bf3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002bf5;
L_180002bf5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002bf6;
L_180002bf6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002bf8;
L_180002bf8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002bfa;
L_180002bfa:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002bfc;
L_180002bfc:
  if (!M.zf&&(M.sf==M.of)) goto L_180002c38; goto L_180002bfe;
L_180002bfe:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002c02;
L_180002c02:
  R.rcx=uint32_t(M.read16((R.r15+0x6ull))); goto L_180002c07;
L_180002c07:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002c09;
L_180002c09:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002c0a;
L_180002c0a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002c0c;
L_180002c0c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002c0e;
L_180002c0e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002c10;
L_180002c10:
  if (!M.zf&&(M.sf==M.of)) goto L_180002c38; goto L_180002c12;
L_180002c12:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002c16;
L_180002c16:
  R.rcx=uint32_t(M.read16((R.r15+0x4ull))); goto L_180002c1b;
L_180002c1b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002c1d;
L_180002c1d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002c1e;
L_180002c1e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002c20;
L_180002c20:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002c22;
L_180002c22:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002c24;
L_180002c24:
  if (!M.zf&&(M.sf==M.of)) goto L_180002c38; goto L_180002c26;
L_180002c26:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_180002c29;
L_180002c29:
  R.rcx=uint32_t(M.read16((R.r15))); goto L_180002c2d;
L_180002c2d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002c2f;
L_180002c2f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002c30;
L_180002c30:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002c32;
L_180002c32:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002c34;
L_180002c34:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002c36;
L_180002c36:
  if (M.zf||(M.sf!=M.of)) goto L_180002c47; goto L_180002c38;
L_180002c38:
  R.rdx=uint64_t(R.r15); goto L_180002c3b;
L_180002c3b:
  R.rcx=uint64_t(R.rbx); goto L_180002c3e;
L_180002c3e:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180002c43;
L_180002c43:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002c45;
L_180002c45:
  if (M.zf||(M.sf!=M.of)) goto L_180002c81; goto L_180002c47;
L_180002c47:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180002c4a;
L_180002c4a:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180002c4e;
L_180002c4e:
  R.r8=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180002c52;
L_180002c52:
  R.rdx=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180002c55;
L_180002c55:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180002c59;
L_180002c59:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180002c5d;
L_180002c5d:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_180002c64;
L_180002c64:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180002c69;
L_180002c69:
  R.rax=uint64_t((R.rbp+0xa8ull)); goto L_180002c70;
L_180002c70:
  M.write64((R.rsp+0x28ull), R.rax); goto L_180002c75;
L_180002c75:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180002c78;
L_180002c78:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180002c7c;
L_180002c7c:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180002c81;
L_180002c81:
  R.r8=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180002c85;
L_180002c85:
  R.r10=uint32_t(uint32_t(R.r8)); goto L_180002c88;
L_180002c88:
  T=M.subflags(uint32_t(R.r10),M.read32((R.r13)),32);
  R.r10=uint32_t(T);
  goto L_180002c8c;
L_180002c8c:
  R.r15=uint32_t(M.read32((R.rbp+0xa8ull))); goto L_180002c93;
L_180002c93:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.r15),32);
  R.r8=uint32_t(T);
  goto L_180002c96;
L_180002c96:
  R.r9=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180002c9a;
L_180002c9a:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180002c9d;
L_180002c9d:
  T=M.subflags(uint32_t(R.r9),M.read32((R.rbp+0x88ull)),32);
  R.r9=uint32_t(T);
  goto L_180002ca4;
L_180002ca4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002ca5;
L_180002ca5:
  R.r11=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180002ca9;
L_180002ca9:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180002cab;
L_180002cab:
  T=M.subflags(uint32_t(R.r11),M.read32((R.r12)),32);
  R.r11=uint32_t(T);
  goto L_180002caf;
L_180002caf:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180002cb1;
L_180002cb1:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180002cb3;
L_180002cb3:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180002cb6;
L_180002cb6:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002cb7;
L_180002cb7:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002cb9;
L_180002cb9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002cbb;
L_180002cbb:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180002cbd;
L_180002cbd:
  if(M.zf||(M.sf!=M.of)){R.r8=uint32_t(uint32_t(R.r9));} goto L_180002cc1;
L_180002cc1:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180002cc4;
L_180002cc4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002cc5;
L_180002cc5:
  R.r8=uint32_t(uint32_t(R.rax)); goto L_180002cc8;
L_180002cc8:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180002ccb;
L_180002ccb:
  T=(uint32_t(R.r8)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r8=uint32_t(T);
  goto L_180002cce;
L_180002cce:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rdx),32);
  R.r8=uint32_t(T);
  goto L_180002cd1;
L_180002cd1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002cd2;
L_180002cd2:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180002cd4;
L_180002cd4:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180002cd7;
L_180002cd7:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180002cd9;
L_180002cd9:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180002cdb;
L_180002cdb:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002cdc;
L_180002cdc:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002cde;
L_180002cde:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002ce0;
L_180002ce0:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180002ce2;
L_180002ce2:
  if(M.zf||(M.sf!=M.of)){R.r10=uint32_t(uint32_t(R.r11));} goto L_180002ce6;
L_180002ce6:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180002ce9;
L_180002ce9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002cea;
L_180002cea:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002cec;
L_180002cec:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002cee;
L_180002cee:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180002cf1;
L_180002cf1:
  if (M.sf==M.of) goto L_180002dee; goto L_180002cf7;
L_180002cf7:
  R.rax=uint32_t(M.read32((R.rbp+0x88ull))); goto L_180002cfd;
L_180002cfd:
  M.write32((R.r13), uint32_t(R.r15)); goto L_180002d01;
L_180002d01:
  M.write32((R.r12), uint32_t(R.rax)); goto L_180002d05;
L_180002d05:
  goto L_180002dee;
L_180002d0a:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180002d0d;
L_180002d0d:
  if (M.zf) goto L_180002da0; goto L_180002d13;
L_180002d13:
  T=M.subflags(M.read32((R.rbp+0xb0ull)),0ull,32);
  goto L_180002d1a;
L_180002d1a:
  if (!M.zf) goto L_180002d4d; goto L_180002d1c;
L_180002d1c:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180002d1f;
L_180002d1f:
  if (M.zf) goto L_180002da0; goto L_180002d21;
L_180002d21:
  R.rax=uint32_t(M.read16((R.r15+0x2ull))); goto L_180002d26;
L_180002d26:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180002d2a;
L_180002d2a:
  if (!M.zf) goto L_180002da0; goto L_180002d2c;
L_180002d2c:
  R.rax=uint32_t(M.read16((R.r15+0x6ull))); goto L_180002d31;
L_180002d31:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180002d35;
L_180002d35:
  if (!M.zf) goto L_180002da0; goto L_180002d37;
L_180002d37:
  R.rax=uint32_t(M.read16((R.r15+0x4ull))); goto L_180002d3c;
L_180002d3c:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180002d40;
L_180002d40:
  if (!M.zf) goto L_180002da0; goto L_180002d42;
L_180002d42:
  R.rax=uint32_t(M.read16((R.r15))); goto L_180002d46;
L_180002d46:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180002d49;
L_180002d49:
  if (!M.zf) goto L_180002da0; goto L_180002d4b;
L_180002d4b:
  goto L_180002daf;
L_180002d4d:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180002d50;
L_180002d50:
  if (M.zf) goto L_180002da0; goto L_180002d52;
L_180002d52:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002d56;
L_180002d56:
  R.rcx=uint32_t(M.read16((R.r15+0x2ull))); goto L_180002d5b;
L_180002d5b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002d5d;
L_180002d5d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002d5e;
L_180002d5e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002d60;
L_180002d60:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002d62;
L_180002d62:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002d64;
L_180002d64:
  if (!M.zf&&(M.sf==M.of)) goto L_180002da0; goto L_180002d66;
L_180002d66:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002d6a;
L_180002d6a:
  R.rcx=uint32_t(M.read16((R.r15+0x6ull))); goto L_180002d6f;
L_180002d6f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002d71;
L_180002d71:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002d72;
L_180002d72:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002d74;
L_180002d74:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002d76;
L_180002d76:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002d78;
L_180002d78:
  if (!M.zf&&(M.sf==M.of)) goto L_180002da0; goto L_180002d7a;
L_180002d7a:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002d7e;
L_180002d7e:
  R.rcx=uint32_t(M.read16((R.r15+0x4ull))); goto L_180002d83;
L_180002d83:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002d85;
L_180002d85:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002d86;
L_180002d86:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002d88;
L_180002d88:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002d8a;
L_180002d8a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002d8c;
L_180002d8c:
  if (!M.zf&&(M.sf==M.of)) goto L_180002da0; goto L_180002d8e;
L_180002d8e:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_180002d91;
L_180002d91:
  R.rcx=uint32_t(M.read16((R.r15))); goto L_180002d95;
L_180002d95:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002d97;
L_180002d97:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002d98;
L_180002d98:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002d9a;
L_180002d9a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002d9c;
L_180002d9c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002d9e;
L_180002d9e:
  if (M.zf||(M.sf!=M.of)) goto L_180002daf; goto L_180002da0;
L_180002da0:
  R.rdx=uint64_t(R.r15); goto L_180002da3;
L_180002da3:
  R.rcx=uint64_t(R.rbx); goto L_180002da6;
L_180002da6:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180002dab;
L_180002dab:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002dad;
L_180002dad:
  if (M.zf||(M.sf!=M.of)) goto L_180002de7; goto L_180002daf;
L_180002daf:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180002db2;
L_180002db2:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002db9;
L_180002db9:
  R.r15=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180002dbd;
L_180002dbd:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180002dc0;
L_180002dc0:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180002dc4;
L_180002dc4:
  R.rdx=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180002dc7;
L_180002dc7:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180002dcb;
L_180002dcb:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180002dcf;
L_180002dcf:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180002dd2;
L_180002dd2:
  M.write64((R.rsp+0x30ull), R.r12); goto L_180002dd7;
L_180002dd7:
  M.write64((R.rsp+0x28ull), R.r13); goto L_180002ddc;
L_180002ddc:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180002de0;
L_180002de0:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180002de5;
L_180002de5:
  goto L_180002df2;
L_180002de7:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180002dee;
L_180002dee:
  R.r15=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180002df2;
L_180002df2:
  R.rax=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180002df5;
L_180002df5:
  T=M.subflags(M.read32((R.r13)),uint32_t(R.rax),32);
  goto L_180002df9;
L_180002df9:
  if (!M.zf) goto L_180002f81; goto L_180002dff;
L_180002dff:
  T=M.subflags(M.read32((R.r12)),uint32_t(R.r15),32);
  goto L_180002e03;
L_180002e03:
  if (!M.zf) goto L_180002f81; goto L_180002e09;
L_180002e09:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180002e0c;
L_180002e0c:
  if (M.zf) goto L_180003012; goto L_180002e12;
L_180002e12:
  R.r15=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180002e19;
L_180002e19:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180002e1c;
L_180002e1c:
  if (!M.zf) goto L_180002ea6; goto L_180002e22;
L_180002e22:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180002e25;
L_180002e25:
  if (M.zf) goto L_180003012; goto L_180002e2b;
L_180002e2b:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002e2f;
L_180002e2f:
  T=M.subflags(uint16_t(R.rax),M.read16((R.rsi+0x2ull)),16);
  goto L_180002e33;
L_180002e33:
  if (!M.zf) goto L_180002f9b; goto L_180002e39;
L_180002e39:
  R.rcx=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002e3d;
L_180002e3d:
  T=M.subflags(uint16_t(R.rcx),M.read16((R.rsi+0x6ull)),16);
  goto L_180002e41;
L_180002e41:
  if (!M.zf) goto L_180002f9b; goto L_180002e47;
L_180002e47:
  R.rdx=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002e4b;
L_180002e4b:
  T=M.subflags(uint16_t(R.rdx),M.read16((R.rsi+0x4ull)),16);
  goto L_180002e4f;
L_180002e4f:
  if (!M.zf) goto L_180002f9b; goto L_180002e55;
L_180002e55:
  R.r8=uint32_t(M.read16((R.rbx))); goto L_180002e59;
L_180002e59:
  T=M.subflags(uint16_t(R.r8),M.read16((R.rsi)),16);
  goto L_180002e5d;
L_180002e5d:
  if (!M.zf) goto L_180002f9b; goto L_180002e63;
L_180002e63:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180002e66;
L_180002e66:
  if (M.zf) goto L_180002f9b; goto L_180002e6c;
L_180002e6c:
  T=M.subflags(uint16_t(R.rax),M.read16((R.r14+0x2ull)),16);
  goto L_180002e71;
L_180002e71:
  if (!M.zf) goto L_180002f9b; goto L_180002e77;
L_180002e77:
  T=M.subflags(uint16_t(R.rcx),M.read16((R.r14+0x6ull)),16);
  goto L_180002e7c;
L_180002e7c:
  if (!M.zf) goto L_180002f9b; goto L_180002e82;
L_180002e82:
  T=M.subflags(uint16_t(R.rdx),M.read16((R.r14+0x4ull)),16);
  goto L_180002e87;
L_180002e87:
  if (!M.zf) goto L_180002f9b; goto L_180002e8d;
L_180002e8d:
  T=M.subflags(uint16_t(R.r8),M.read16((R.r14)),16);
  goto L_180002e91;
L_180002e91:
  if (!M.zf) goto L_180002f9b; goto L_180002e97;
L_180002e97:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180002e9b;
L_180002e9b:
  M.write32((R.rax), 3ull); goto L_180002ea1;
L_180002ea1:
  goto L_180002f88;
L_180002ea6:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180002ea9;
L_180002ea9:
  if (M.zf) goto L_180003012; goto L_180002eaf;
L_180002eaf:
  R.r11=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002eb4;
L_180002eb4:
  R.rcx=uint32_t(M.read16((R.rsi+0x2ull))); goto L_180002eb8;
L_180002eb8:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180002ebb;
L_180002ebb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002ebd;
L_180002ebd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002ebe;
L_180002ebe:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002ec0;
L_180002ec0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002ec2;
L_180002ec2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002ec4;
L_180002ec4:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002eca;
L_180002eca:
  R.r10=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002ecf;
L_180002ecf:
  R.rcx=uint32_t(M.read16((R.rsi+0x6ull))); goto L_180002ed3;
L_180002ed3:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180002ed6;
L_180002ed6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002ed8;
L_180002ed8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002ed9;
L_180002ed9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002edb;
L_180002edb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002edd;
L_180002edd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002edf;
L_180002edf:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002ee5;
L_180002ee5:
  R.r9=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002eea;
L_180002eea:
  R.rcx=uint32_t(M.read16((R.rsi+0x4ull))); goto L_180002eee;
L_180002eee:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180002ef1;
L_180002ef1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002ef3;
L_180002ef3:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002ef4;
L_180002ef4:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002ef6;
L_180002ef6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002ef8;
L_180002ef8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002efa;
L_180002efa:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f00;
L_180002f00:
  R.r8=uint32_t(M.read16((R.rbx))); goto L_180002f04;
L_180002f04:
  R.rcx=uint32_t(M.read16((R.rsi))); goto L_180002f07;
L_180002f07:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180002f0a;
L_180002f0a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002f0c;
L_180002f0c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002f0d;
L_180002f0d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002f0f;
L_180002f0f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002f11;
L_180002f11:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002f13;
L_180002f13:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f19;
L_180002f19:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180002f1c;
L_180002f1c:
  if (M.zf) goto L_180002fc8; goto L_180002f22;
L_180002f22:
  R.rcx=uint32_t(M.read16((R.r14+0x2ull))); goto L_180002f27;
L_180002f27:
  T=M.subflags(uint32_t(R.r11),uint32_t(R.rcx),32);
  R.r11=uint32_t(T);
  goto L_180002f2a;
L_180002f2a:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180002f2d;
L_180002f2d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002f2e;
L_180002f2e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002f30;
L_180002f30:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002f32;
L_180002f32:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002f34;
L_180002f34:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f3a;
L_180002f3a:
  R.rcx=uint32_t(M.read16((R.r14+0x6ull))); goto L_180002f3f;
L_180002f3f:
  T=M.subflags(uint32_t(R.r10),uint32_t(R.rcx),32);
  R.r10=uint32_t(T);
  goto L_180002f42;
L_180002f42:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180002f45;
L_180002f45:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002f46;
L_180002f46:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002f48;
L_180002f48:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002f4a;
L_180002f4a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002f4c;
L_180002f4c:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f4e;
L_180002f4e:
  R.rcx=uint32_t(M.read16((R.r14+0x4ull))); goto L_180002f53;
L_180002f53:
  T=M.subflags(uint32_t(R.r9),uint32_t(R.rcx),32);
  R.r9=uint32_t(T);
  goto L_180002f56;
L_180002f56:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180002f59;
L_180002f59:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002f5a;
L_180002f5a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002f5c;
L_180002f5c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002f5e;
L_180002f5e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002f60;
L_180002f60:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f62;
L_180002f62:
  R.rcx=uint32_t(M.read16((R.r14))); goto L_180002f66;
L_180002f66:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rcx),32);
  R.r8=uint32_t(T);
  goto L_180002f69;
L_180002f69:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180002f6c;
L_180002f6c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002f6d;
L_180002f6d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002f6f;
L_180002f6f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002f71;
L_180002f71:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002f73;
L_180002f73:
  if (!M.zf&&(M.sf==M.of)) goto L_180002fc8; goto L_180002f75;
L_180002f75:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180002f79;
L_180002f79:
  M.write32((R.rax), 3ull); goto L_180002f7f;
L_180002f7f:
  goto L_180002f88;
L_180002f81:
  R.r15=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180002f88;
L_180002f88:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180002f8b;
L_180002f8b:
  if (M.zf) goto L_180003012; goto L_180002f91;
L_180002f91:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180002f94;
L_180002f94:
  if (!M.zf) goto L_180002fc3; goto L_180002f96;
L_180002f96:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180002f99;
L_180002f99:
  if (M.zf) goto L_180003012; goto L_180002f9b;
L_180002f9b:
  R.rax=uint32_t(M.read16((R.rsi+0x2ull))); goto L_180002f9f;
L_180002f9f:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_180002fa3;
L_180002fa3:
  if (!M.zf) goto L_180003012; goto L_180002fa5;
L_180002fa5:
  R.rax=uint32_t(M.read16((R.rsi+0x6ull))); goto L_180002fa9;
L_180002fa9:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180002fad;
L_180002fad:
  if (!M.zf) goto L_180003012; goto L_180002faf;
L_180002faf:
  R.rax=uint32_t(M.read16((R.rsi+0x4ull))); goto L_180002fb3;
L_180002fb3:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180002fb7;
L_180002fb7:
  if (!M.zf) goto L_180003012; goto L_180002fb9;
L_180002fb9:
  R.rax=uint32_t(M.read16((R.rsi))); goto L_180002fbc;
L_180002fbc:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_180002fbf;
L_180002fbf:
  if (!M.zf) goto L_180003012; goto L_180002fc1;
L_180002fc1:
  goto L_18000302c;
L_180002fc3:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180002fc6;
L_180002fc6:
  if (M.zf) goto L_180003012; goto L_180002fc8;
L_180002fc8:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180002fcc;
L_180002fcc:
  R.rcx=uint32_t(M.read16((R.rsi+0x2ull))); goto L_180002fd0;
L_180002fd0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002fd2;
L_180002fd2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002fd3;
L_180002fd3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002fd5;
L_180002fd5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002fd7;
L_180002fd7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002fd9;
L_180002fd9:
  if (!M.zf&&(M.sf==M.of)) goto L_180003012; goto L_180002fdb;
L_180002fdb:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_180002fdf;
L_180002fdf:
  R.rcx=uint32_t(M.read16((R.rsi+0x6ull))); goto L_180002fe3;
L_180002fe3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002fe5;
L_180002fe5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002fe6;
L_180002fe6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002fe8;
L_180002fe8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002fea;
L_180002fea:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002fec;
L_180002fec:
  if (!M.zf&&(M.sf==M.of)) goto L_180003012; goto L_180002fee;
L_180002fee:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180002ff2;
L_180002ff2:
  R.rcx=uint32_t(M.read16((R.rsi+0x4ull))); goto L_180002ff6;
L_180002ff6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180002ff8;
L_180002ff8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180002ff9;
L_180002ff9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180002ffb;
L_180002ffb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180002ffd;
L_180002ffd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180002fff;
L_180002fff:
  if (!M.zf&&(M.sf==M.of)) goto L_180003012; goto L_180003001;
L_180003001:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_180003004;
L_180003004:
  R.rcx=uint32_t(M.read16((R.rsi))); goto L_180003007;
L_180003007:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003009;
L_180003009:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000300a;
L_18000300a:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000300c;
L_18000300c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000300e;
L_18000300e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003010;
L_180003010:
  if (M.zf||(M.sf!=M.of)) goto L_180003080; goto L_180003012;
L_180003012:
  R.rdx=uint64_t(R.rsi); goto L_180003015;
L_180003015:
  R.rcx=uint64_t(R.rbx); goto L_180003018;
L_180003018:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_18000301d;
L_18000301d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000301f;
L_18000301f:
  if (M.zf||(M.sf!=M.of)) goto L_1800030e2; goto L_180003025;
L_180003025:
  R.r15=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_18000302c;
L_18000302c:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000302f;
L_18000302f:
  if (M.zf) goto L_1800030d3; goto L_180003035;
L_180003035:
  T=(uint32_t(R.r15)) & (uint32_t(R.r15)); M.logicflags(T,32);
  goto L_180003038;
L_180003038:
  if (!M.zf) goto L_180003080; goto L_18000303a;
L_18000303a:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_18000303d;
L_18000303d:
  if (M.zf) goto L_1800030d3; goto L_180003043;
L_180003043:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_180003048;
L_180003048:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_18000304c;
L_18000304c:
  if (!M.zf) goto L_1800030d3; goto L_180003052;
L_180003052:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_180003057;
L_180003057:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_18000305b;
L_18000305b:
  if (!M.zf) goto L_1800030d3; goto L_18000305d;
L_18000305d:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_180003062;
L_180003062:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180003066;
L_180003066:
  if (!M.zf) goto L_1800030d3; goto L_180003068;
L_180003068:
  R.rax=uint32_t(M.read16((R.r14))); goto L_18000306c;
L_18000306c:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_18000306f;
L_18000306f:
  if (!M.zf) goto L_1800030d3; goto L_180003071;
L_180003071:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_180003078;
L_180003078:
  M.write8((R.rax), 1ull); goto L_18000307b;
L_18000307b:
  goto L_1800033b3;
L_180003080:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003083;
L_180003083:
  if (M.zf) goto L_1800030d3; goto L_180003085;
L_180003085:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180003089;
L_180003089:
  R.rcx=uint32_t(M.read16((R.r14+0x2ull))); goto L_18000308e;
L_18000308e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003090;
L_180003090:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003091;
L_180003091:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003093;
L_180003093:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003095;
L_180003095:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003097;
L_180003097:
  if (!M.zf&&(M.sf==M.of)) goto L_1800030d3; goto L_180003099;
L_180003099:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_18000309d;
L_18000309d:
  R.rcx=uint32_t(M.read16((R.r14+0x6ull))); goto L_1800030a2;
L_1800030a2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800030a4;
L_1800030a4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800030a5;
L_1800030a5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800030a7;
L_1800030a7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800030a9;
L_1800030a9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800030ab;
L_1800030ab:
  if (!M.zf&&(M.sf==M.of)) goto L_1800030d3; goto L_1800030ad;
L_1800030ad:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_1800030b1;
L_1800030b1:
  R.rcx=uint32_t(M.read16((R.r14+0x4ull))); goto L_1800030b6;
L_1800030b6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800030b8;
L_1800030b8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800030b9;
L_1800030b9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800030bb;
L_1800030bb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800030bd;
L_1800030bd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800030bf;
L_1800030bf:
  if (!M.zf&&(M.sf==M.of)) goto L_1800030d3; goto L_1800030c1;
L_1800030c1:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_1800030c4;
L_1800030c4:
  R.rcx=uint32_t(M.read16((R.r14))); goto L_1800030c8;
L_1800030c8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800030ca;
L_1800030ca:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800030cb;
L_1800030cb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800030cd;
L_1800030cd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800030cf;
L_1800030cf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800030d1;
L_1800030d1:
  if (M.zf||(M.sf!=M.of)) goto L_180003117; goto L_1800030d3;
L_1800030d3:
  R.rdx=uint64_t(R.r14); goto L_1800030d6;
L_1800030d6:
  R.rcx=uint64_t(R.rbx); goto L_1800030d9;
L_1800030d9:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_1800030de;
L_1800030de:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800030e0;
L_1800030e0:
  if (!M.zf&&(M.sf==M.of)) goto L_180003117; goto L_1800030e2;
L_1800030e2:
  R.r12=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_1800030e9;
L_1800030e9:
  R.rcx=uint64_t(R.rsi); goto L_1800030ec;
L_1800030ec:
  R.r13=uint64_t(M.read64((R.rbp-0x10ull))); goto L_1800030f0;
L_1800030f0:
  R.r15=uint32_t(uint32_t(R.r12)); goto L_1800030f3;
L_1800030f3:
  T=M.subflags(0,uint32_t(R.r15),32); R.r15=uint32_t(T); goto L_1800030f6;
L_1800030f6:
  R.rdx=uint64_t(R.r13); goto L_1800030f9;
L_1800030f9:
  R.r15=uint32_t((uint32_t(R.r15))<<((7ull)&0x3f)); goto L_1800030fd;
L_1800030fd:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180003102;
L_180003102:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180003105;
L_180003105:
  if (M.sf==M.of) goto L_180003126; goto L_180003107;
L_180003107:
  R.rdx=uint64_t(R.r13); goto L_18000310a;
L_18000310a:
  R.rcx=uint64_t(R.r14); goto L_18000310d;
L_18000310d:
  R.rax=uint32_t(ColorCompare16((const uint16_t*)R.rcx,(const uint16_t*)R.rdx)); goto L_180003112;
L_180003112:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180003115;
L_180003115:
  if (M.sf==M.of) goto L_180003126; goto L_180003117;
L_180003117:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_18000311e;
L_18000311e:
  M.write8((R.rax), 1ull); goto L_180003121;
L_180003121:
  goto L_1800033b3;
L_180003126:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180003129;
L_180003129:
  R.r15=uint32_t(M.read32((R.rbp+0x58ull))); goto L_18000312d;
L_18000312d:
  R.rdx=uint32_t(uint32_t(R.r15)); goto L_180003130;
L_180003130:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180003134;
L_180003134:
  R.r8=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003138;
L_180003138:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_18000313c;
L_18000313c:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003140;
L_180003140:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_180003147;
L_180003147:
  M.write64((R.rsp+0x30ull), R.rax); goto L_18000314c;
L_18000314c:
  R.rax=uint64_t((R.rbp+0x90ull)); goto L_180003153;
L_180003153:
  M.write64((R.rsp+0x28ull), R.rax); goto L_180003158;
L_180003158:
  R.rax=uint32_t(M.read32((R.rbp-0x20ull))); goto L_18000315b;
L_18000315b:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_18000315f;
L_18000315f:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003164;
L_180003164:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180003167;
L_180003167:
  R.rdx=uint32_t(uint32_t(R.r15)); goto L_18000316a;
L_18000316a:
  R.r9=uint32_t(M.read32((R.rbp-0x18ull))); goto L_18000316e;
L_18000316e:
  R.r8=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003172;
L_180003172:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003176;
L_180003176:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_18000317a;
L_18000317a:
  R.rax=uint64_t((R.rbp+0x58ull)); goto L_18000317e;
L_18000317e:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180003183;
L_180003183:
  R.rax=uint64_t((R.rbp+0x68ull)); goto L_180003187;
L_180003187:
  M.write64((R.rsp+0x28ull), R.rax); goto L_18000318c;
L_18000318c:
  R.rax=uint32_t(M.read32((R.rbp-0x20ull))); goto L_18000318f;
L_18000318f:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003193;
L_180003193:
  R.rax=(uintptr_t)EdgeWalker16Exact((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003198;
L_180003198:
  T=(uint32_t(R.r12)) & (uint32_t(R.r12)); M.logicflags(T,32);
  goto L_18000319b;
L_18000319b:
  if (!M.zf) goto L_18000322c; goto L_1800031a1;
L_1800031a1:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800031a4;
L_1800031a4:
  if (M.zf) goto L_1800031d6; goto L_1800031a6;
L_1800031a6:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_1800031a9;
L_1800031a9:
  if (M.zf) goto L_1800031d6; goto L_1800031ab;
L_1800031ab:
  R.rax=uint32_t(M.read16((R.rsi+0x2ull))); goto L_1800031af;
L_1800031af:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_1800031b3;
L_1800031b3:
  if (!M.zf) goto L_1800031d6; goto L_1800031b5;
L_1800031b5:
  R.rax=uint32_t(M.read16((R.rsi+0x6ull))); goto L_1800031b9;
L_1800031b9:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_1800031bd;
L_1800031bd:
  if (!M.zf) goto L_1800031d6; goto L_1800031bf;
L_1800031bf:
  R.rax=uint32_t(M.read16((R.rsi+0x4ull))); goto L_1800031c3;
L_1800031c3:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_1800031c7;
L_1800031c7:
  if (!M.zf) goto L_1800031d6; goto L_1800031c9;
L_1800031c9:
  R.rax=uint32_t(M.read16((R.rsi))); goto L_1800031cc;
L_1800031cc:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_1800031cf;
L_1800031cf:
  if (!M.zf) goto L_1800031d6; goto L_1800031d1;
L_1800031d1:
  R.r8=(R.r8&~0xffull)|(uint8_t(1ull)); goto L_1800031d4;
L_1800031d4:
  goto L_1800031d9;
L_1800031d6:
  T=(uint8_t(R.r8)) ^ (uint8_t(R.r8)); M.logicflags(T,8);
  R.r8=(R.r8&~0xffull)|(uint8_t(T));
  goto L_1800031d9;
L_1800031d9:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_1800031dc;
L_1800031dc:
  if (M.zf) goto L_1800032e4; goto L_1800031e2;
L_1800031e2:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_1800031e5;
L_1800031e5:
  if (M.zf) goto L_1800032e4; goto L_1800031eb;
L_1800031eb:
  R.rax=uint32_t(M.read16((R.r14+0x2ull))); goto L_1800031f0;
L_1800031f0:
  T=M.subflags(M.read16((R.rbx+0x2ull)),uint16_t(R.rax),16);
  goto L_1800031f4;
L_1800031f4:
  if (!M.zf) goto L_1800032e4; goto L_1800031fa;
L_1800031fa:
  R.rax=uint32_t(M.read16((R.r14+0x6ull))); goto L_1800031ff;
L_1800031ff:
  T=M.subflags(M.read16((R.rbx+0x6ull)),uint16_t(R.rax),16);
  goto L_180003203;
L_180003203:
  if (!M.zf) goto L_1800032e4; goto L_180003209;
L_180003209:
  R.rax=uint32_t(M.read16((R.r14+0x4ull))); goto L_18000320e;
L_18000320e:
  T=M.subflags(M.read16((R.rbx+0x4ull)),uint16_t(R.rax),16);
  goto L_180003212;
L_180003212:
  if (!M.zf) goto L_1800032e4; goto L_180003218;
L_180003218:
  R.rax=uint32_t(M.read16((R.r14))); goto L_18000321c;
L_18000321c:
  T=M.subflags(M.read16((R.rbx)),uint16_t(R.rax),16);
  goto L_18000321f;
L_18000321f:
  if (!M.zf) goto L_1800032e4; goto L_180003225;
L_180003225:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180003227;
L_180003227:
  goto L_1800032e6;
L_18000322c:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000322f;
L_18000322f:
  if (M.zf) goto L_180003285; goto L_180003231;
L_180003231:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003234;
L_180003234:
  if (M.zf) goto L_180003285; goto L_180003236;
L_180003236:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_18000323a;
L_18000323a:
  R.rcx=uint32_t(M.read16((R.rsi+0x2ull))); goto L_18000323e;
L_18000323e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003240;
L_180003240:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003241;
L_180003241:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003243;
L_180003243:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003245;
L_180003245:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003247;
L_180003247:
  if (!M.zf&&(M.sf==M.of)) goto L_180003285; goto L_180003249;
L_180003249:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_18000324d;
L_18000324d:
  R.rcx=uint32_t(M.read16((R.rsi+0x6ull))); goto L_180003251;
L_180003251:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003253;
L_180003253:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003254;
L_180003254:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003256;
L_180003256:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003258;
L_180003258:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000325a;
L_18000325a:
  if (!M.zf&&(M.sf==M.of)) goto L_180003285; goto L_18000325c;
L_18000325c:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_180003260;
L_180003260:
  R.rcx=uint32_t(M.read16((R.rsi+0x4ull))); goto L_180003264;
L_180003264:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003266;
L_180003266:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003267;
L_180003267:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003269;
L_180003269:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000326b;
L_18000326b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000326d;
L_18000326d:
  if (!M.zf&&(M.sf==M.of)) goto L_180003285; goto L_18000326f;
L_18000326f:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_180003272;
L_180003272:
  R.rcx=uint32_t(M.read16((R.rsi))); goto L_180003275;
L_180003275:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003277;
L_180003277:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003278;
L_180003278:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000327a;
L_18000327a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000327c;
L_18000327c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000327e;
L_18000327e:
  if (!M.zf&&(M.sf==M.of)) goto L_180003285; goto L_180003280;
L_180003280:
  R.r8=(R.r8&~0xffull)|(uint8_t(1ull)); goto L_180003283;
L_180003283:
  goto L_180003288;
L_180003285:
  T=(uint8_t(R.r8)) ^ (uint8_t(R.r8)); M.logicflags(T,8);
  R.r8=(R.r8&~0xffull)|(uint8_t(T));
  goto L_180003288;
L_180003288:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000328b;
L_18000328b:
  if (M.zf) goto L_1800032e4; goto L_18000328d;
L_18000328d:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003290;
L_180003290:
  if (M.zf) goto L_1800032e4; goto L_180003292;
L_180003292:
  R.rax=uint32_t(M.read16((R.rbx+0x2ull))); goto L_180003296;
L_180003296:
  R.rcx=uint32_t(M.read16((R.r14+0x2ull))); goto L_18000329b;
L_18000329b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_18000329d;
L_18000329d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000329e;
L_18000329e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800032a0;
L_1800032a0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800032a2;
L_1800032a2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800032a4;
L_1800032a4:
  if (!M.zf&&(M.sf==M.of)) goto L_1800032e4; goto L_1800032a6;
L_1800032a6:
  R.rax=uint32_t(M.read16((R.rbx+0x6ull))); goto L_1800032aa;
L_1800032aa:
  R.rcx=uint32_t(M.read16((R.r14+0x6ull))); goto L_1800032af;
L_1800032af:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800032b1;
L_1800032b1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800032b2;
L_1800032b2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800032b4;
L_1800032b4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800032b6;
L_1800032b6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800032b8;
L_1800032b8:
  if (!M.zf&&(M.sf==M.of)) goto L_1800032e4; goto L_1800032ba;
L_1800032ba:
  R.rax=uint32_t(M.read16((R.rbx+0x4ull))); goto L_1800032be;
L_1800032be:
  R.rcx=uint32_t(M.read16((R.r14+0x4ull))); goto L_1800032c3;
L_1800032c3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800032c5;
L_1800032c5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800032c6;
L_1800032c6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800032c8;
L_1800032c8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800032ca;
L_1800032ca:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800032cc;
L_1800032cc:
  if (!M.zf&&(M.sf==M.of)) goto L_1800032e4; goto L_1800032ce;
L_1800032ce:
  R.rax=uint32_t(M.read16((R.rbx))); goto L_1800032d1;
L_1800032d1:
  R.rcx=uint32_t(M.read16((R.r14))); goto L_1800032d5;
L_1800032d5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800032d7;
L_1800032d7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800032d8;
L_1800032d8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800032da;
L_1800032da:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800032dc;
L_1800032dc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800032de;
L_1800032de:
  if (!M.zf&&(M.sf==M.of)) goto L_1800032e4; goto L_1800032e0;
L_1800032e0:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_1800032e2;
L_1800032e2:
  goto L_1800032e6;
L_1800032e4:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_1800032e6;
L_1800032e6:
  T=(uint8_t(R.r8)) & (uint8_t(R.r8)); M.logicflags(T,8);
  goto L_1800032e9;
L_1800032e9:
  if (!M.zf) goto L_180003391; goto L_1800032ef;
L_1800032ef:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_1800032f1;
L_1800032f1:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_1800032f4;
L_1800032f4:
  if (!M.zf) goto L_180003383; goto L_1800032fa;
L_1800032fa:
  R.rcx=uint32_t(M.read32((R.rbp+0x58ull))); goto L_1800032fd;
L_1800032fd:
  R.r9=uint32_t(uint32_t(R.r15)); goto L_180003300;
L_180003300:
  R.r8=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003304;
L_180003304:
  T=M.subflags(uint32_t(R.r9),uint32_t(R.rax),32);
  R.r9=uint32_t(T);
  goto L_180003307;
L_180003307:
  R.rsi=uint64_t(M.read64((R.rbp+0x98ull))); goto L_18000330e;
L_18000330e:
  R.r10=uint32_t(uint32_t(R.r8)); goto L_180003311;
L_180003311:
  R.rbx=uint32_t(M.read32((R.rbp+0x90ull))); goto L_180003317;
L_180003317:
  T=M.subflags(uint32_t(R.r10),uint32_t(R.rcx),32);
  R.r10=uint32_t(T);
  goto L_18000331a;
L_18000331a:
  R.rdi=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180003321;
L_180003321:
  T=M.subflags(uint32_t(R.r15),uint32_t(R.rbx),32);
  R.r15=uint32_t(T);
  goto L_180003324;
L_180003324:
  R.r11=uint32_t(M.read32((R.rbp+0x88ull))); goto L_18000332b;
L_18000332b:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.r11),32);
  R.r8=uint32_t(T);
  goto L_18000332e;
L_18000332e:
  M.write32((R.rsi), uint32_t(R.rax)); goto L_180003330;
L_180003330:
  R.rax=uint32_t(uint32_t(R.r15)); goto L_180003333;
L_180003333:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003334;
L_180003334:
  M.write32((R.rdi), uint32_t(R.rcx)); goto L_180003336;
L_180003336:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180003338;
L_180003338:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_18000333a;
L_18000333a:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_18000333d;
L_18000333d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_18000333f;
L_18000333f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003340;
L_180003340:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003342;
L_180003342:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003344;
L_180003344:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180003346;
L_180003346:
  if(M.zf||(M.sf!=M.of)){R.r15=uint32_t(uint32_t(R.r8));} goto L_18000334a;
L_18000334a:
  R.rax=uint32_t(uint32_t(R.r15)); goto L_18000334d;
L_18000334d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000334e;
L_18000334e:
  R.r8=uint32_t(uint32_t(R.rax)); goto L_180003351;
L_180003351:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003354;
L_180003354:
  T=(uint32_t(R.r8)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r8=uint32_t(T);
  goto L_180003357;
L_180003357:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rdx),32);
  R.r8=uint32_t(T);
  goto L_18000335a;
L_18000335a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000335b;
L_18000335b:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_18000335d;
L_18000335d:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180003360;
L_180003360:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180003362;
L_180003362:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180003364;
L_180003364:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003365;
L_180003365:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003367;
L_180003367:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003369;
L_180003369:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_18000336b;
L_18000336b:
  if(M.zf||(M.sf!=M.of)){R.r9=uint32_t(uint32_t(R.r10));} goto L_18000336f;
L_18000336f:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003372;
L_180003372:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003373;
L_180003373:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003375;
L_180003375:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003377;
L_180003377:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_18000337a;
L_18000337a:
  if (M.zf||(M.sf!=M.of)) goto L_1800033b3; goto L_18000337c;
L_18000337c:
  M.write32((R.rsi), uint32_t(R.rbx)); goto L_18000337e;
L_18000337e:
  M.write32((R.rdi), uint32_t(R.r11)); goto L_180003381;
L_180003381:
  goto L_1800033b3;
L_180003383:
  R.rcx=uint64_t(M.read64((R.rbp+0x98ull))); goto L_18000338a;
L_18000338a:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_18000338c;
L_18000338c:
  R.rax=uint32_t(M.read32((R.rbp+0x58ull))); goto L_18000338f;
L_18000338f:
  goto L_1800033aa;
L_180003391:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180003393;
L_180003393:
  if (!M.zf) goto L_1800033b3; goto L_180003395;
L_180003395:
  R.rax=uint32_t(M.read32((R.rbp+0x90ull))); goto L_18000339b;
L_18000339b:
  R.rcx=uint64_t(M.read64((R.rbp+0x98ull))); goto L_1800033a2;
L_1800033a2:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_1800033a4;
L_1800033a4:
  R.rax=uint32_t(M.read32((R.rbp+0x88ull))); goto L_1800033aa;
L_1800033aa:
  R.rcx=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_1800033b1;
L_1800033b1:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_1800033b3;
L_1800033b3:
  T=M.addflags(R.rsp,0x68ull,64); R.rsp=uint64_t(T); goto L_1800033b7;
L_1800033b7:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033b9;
L_1800033b9:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033bb;
L_1800033bb:
  R.r13=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033bd;
L_1800033bd:
  R.r12=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033bf;
L_1800033bf:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033c0;
L_1800033c0:
  R.rsi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033c1;
L_1800033c1:
  R.rbx=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033c2;
L_1800033c2:
  R.rbp=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_1800033c3;
L_1800033c3:
  return;
