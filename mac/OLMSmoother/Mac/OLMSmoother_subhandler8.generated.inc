// Generated from olmsmoother_v1_subhandler8_cfg_20260805.json; do not hand edit.
L_1800033d0:
  M.write32((R.rsp+0x20ull), uint32_t(R.r9)); goto L_1800033d5;
L_1800033d5:
  M.write32((R.rsp+0x18ull), uint32_t(R.r8)); goto L_1800033da;
L_1800033da:
  M.write64((R.rsp+0x8ull), R.rcx); goto L_1800033df;
L_1800033df:
  R.rsp-=8; M.write64(R.rsp,R.rbp); goto L_1800033e0;
L_1800033e0:
  R.rsp-=8; M.write64(R.rsp,R.rbx); goto L_1800033e1;
L_1800033e1:
  R.rsp-=8; M.write64(R.rsp,R.rsi); goto L_1800033e2;
L_1800033e2:
  R.rsp-=8; M.write64(R.rsp,R.rdi); goto L_1800033e3;
L_1800033e3:
  R.rsp-=8; M.write64(R.rsp,R.r12); goto L_1800033e5;
L_1800033e5:
  R.rsp-=8; M.write64(R.rsp,R.r13); goto L_1800033e7;
L_1800033e7:
  R.rsp-=8; M.write64(R.rsp,R.r14); goto L_1800033e9;
L_1800033e9:
  R.rsp-=8; M.write64(R.rsp,R.r15); goto L_1800033eb;
L_1800033eb:
  R.rbp=uint64_t(R.rsp); goto L_1800033ee;
L_1800033ee:
  T=M.subflags(R.rsp,0x68ull,64);
  R.rsp=uint64_t(T);
  goto L_1800033f2;
L_1800033f2:
  R.rax=uint64_t(M.read64((R.rbp+0x88ull))); goto L_1800033f9;
L_1800033f9:
  R.r10=uint64_t((0x180003400-0x3400ull)); goto L_180003400;
L_180003400:
  R.r13=uint64_t(M.read64((R.rbp+0xb0ull))); goto L_180003407;
L_180003407:
  M.write32((R.rax), uint32_t(R.r8)); goto L_18000340a;
L_18000340a:
  R.rax=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180003411;
L_180003411:
  M.write32((R.rax), uint32_t(R.r9)); goto L_180003414;
L_180003414:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_18000341b;
L_18000341b:
  M.write32((R.rax), uint32_t(R.r8)); goto L_18000341e;
L_18000341e:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180003425;
L_180003425:
  M.write32((R.rax), uint32_t(R.r9)); goto L_180003428;
L_180003428:
  R.rax=uint64_t(M.read64((R.rbp+0xa8ull))); goto L_18000342f;
L_18000342f:
  M.write32((R.rax), uint32_t(R.r8)); goto L_180003432;
L_180003432:
  R.rax=uint64_t(M.read64((R.rbp+0x78ull))); goto L_180003436;
L_180003436:
  M.write32((R.r13), uint32_t(R.r9)); goto L_18000343a;
L_18000343a:
  M.write8((R.rax), 0ull); goto L_18000343d;
L_18000343d:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_180003444;
L_180003444:
  M.write8((R.rax), 0ull); goto L_180003447;
L_180003447:
  R.rax=uint32_t(M.read32((R.rcx+0xcull))); goto L_18000344a;
L_18000344a:
  R.rdi=uint32_t(M.read32((R.rcx+0x8ull))); goto L_18000344d;
L_18000344d:
  R.rcx=uint64_t(int64_t(int32_t(M.read32((R.rbp+0x68ull))))); goto L_180003451;
L_180003451:
  R.rbx=uint64_t(M.read64((R.rdx+0x20ull))); goto L_180003455;
L_180003455:
  M.write32((R.rbp+0x50ull), uint32_t(R.rax)); goto L_180003458;
L_180003458:
  R.rax=uint32_t(M.read32((R.r10+(R.rcx*4ull)+0xf0c8ull))); goto L_180003460;
L_180003460:
  T=M.addflags(uint32_t(R.rax),uint32_t(R.r8),32); R.rax=uint32_t(T); goto L_180003463;
L_180003463:
  R.r8=uint64_t(int64_t(int32_t(M.read32((R.r10+(R.rcx*4ull)+0xf028ull))))); goto L_18000346b;
L_18000346b:
  M.write32((R.rbp-0x28ull), uint32_t(R.rax)); goto L_18000346e;
L_18000346e:
  R.rax=uint32_t(M.read32((R.r10+(R.rcx*4ull)+0xf0f0ull))); goto L_180003476;
L_180003476:
  T=M.addflags(uint32_t(R.rax),uint32_t(R.r9),32); R.rax=uint32_t(T); goto L_180003479;
L_180003479:
  M.write32((R.rbp-0x20ull), uint32_t(R.r8)); goto L_18000347d;
L_18000347d:
  R.r9=uint64_t(int64_t(int32_t(M.read32((R.r10+(R.rcx*4ull)+0xf000ull))))); goto L_180003485;
L_180003485:
  R.r14=uint64_t(M.read64((R.rdx+(R.r8*8ull)))); goto L_180003489;
L_180003489:
  M.write32((R.rbp+0xb0ull), uint32_t(R.rax)); goto L_18000348f;
L_18000348f:
  R.rax=uint32_t(M.read32((R.r10+(R.rcx*4ull)+0xf0a0ull))); goto L_180003497;
L_180003497:
  R.rsi=uint64_t(M.read64((R.rdx+(R.r9*8ull)))); goto L_18000349b;
L_18000349b:
  M.write32((R.rbp-0x24ull), uint32_t(R.rax)); goto L_18000349e;
L_18000349e:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.r10+(R.rcx*4ull)+0xf050ull))))); goto L_1800034a6;
L_1800034a6:
  M.write32((R.rbp-0x1cull), uint32_t(R.r9)); goto L_1800034aa;
L_1800034aa:
  R.r12=uint64_t(M.read64((R.rdx+(R.rax*8ull)))); goto L_1800034ae;
L_1800034ae:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.r10+(R.rcx*4ull)+0xf078ull))))); goto L_1800034b6;
L_1800034b6:
  R.r15=uint64_t(M.read64((R.rdx+(R.rax*8ull)))); goto L_1800034ba;
L_1800034ba:
  R.rax=uint64_t(M.read64((R.rdx+(R.rcx*8ull)))); goto L_1800034be;
L_1800034be:
  R.rdx=uint64_t(R.rbx); goto L_1800034c1;
L_1800034c1:
  R.rcx=uint64_t(R.r12); goto L_1800034c4;
L_1800034c4:
  M.write64((R.rbp-0x18ull), R.rax); goto L_1800034c8;
L_1800034c8:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_1800034cd;
L_1800034cd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800034cf;
L_1800034cf:
  if (M.zf||(M.sf!=M.of)) goto L_18000370f; goto L_1800034d5;
L_1800034d5:
  R.rdx=uint64_t(R.rbx); goto L_1800034d8;
L_1800034d8:
  R.rcx=uint64_t(R.r15); goto L_1800034db;
L_1800034db:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_1800034e0;
L_1800034e0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800034e2;
L_1800034e2:
  if (M.zf||(M.sf!=M.of)) goto L_18000370f; goto L_1800034e8;
L_1800034e8:
  R.rdx=uint64_t(R.rbx); goto L_1800034eb;
L_1800034eb:
  R.rcx=uint64_t(R.rsi); goto L_1800034ee;
L_1800034ee:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_1800034f3;
L_1800034f3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800034f5;
L_1800034f5:
  if (M.zf||(M.sf!=M.of)) goto L_18000370f; goto L_1800034fb;
L_1800034fb:
  R.rdx=uint64_t(R.rbx); goto L_1800034fe;
L_1800034fe:
  R.rcx=uint64_t(R.r14); goto L_180003501;
L_180003501:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003506;
L_180003506:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003508;
L_180003508:
  if (M.zf||(M.sf!=M.of)) goto L_18000370f; goto L_18000350e;
L_18000350e:
  R.r12=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180003512;
L_180003512:
  R.rdx=uint32_t(uint32_t(R.r12)); goto L_180003515;
L_180003515:
  R.r15=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003519;
L_180003519:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_18000351c;
L_18000351c:
  R.rsi=uint64_t(M.read64((R.rbp+0x88ull))); goto L_180003523;
L_180003523:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180003526;
L_180003526:
  R.r14=uint64_t(M.read64((R.rbp+0x90ull))); goto L_18000352d;
L_18000352d:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180003531;
L_180003531:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003535;
L_180003535:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003539;
L_180003539:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_180003540;
L_180003540:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180003545;
L_180003545:
  R.rax=uint64_t((R.rbp+0x58ull)); goto L_180003549;
L_180003549:
  M.write64((R.rsp+0x28ull), R.rax); goto L_18000354e;
L_18000354e:
  R.rax=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180003551;
L_180003551:
  M.write32((R.rsi), uint32_t(R.r12)); goto L_180003554;
L_180003554:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003558;
L_180003558:
  M.write32((R.r14), uint32_t(R.r15)); goto L_18000355b;
L_18000355b:
  M.write32((R.rbp+0x58ull), uint32_t(R.r12)); goto L_18000355f;
L_18000355f:
  M.write32((R.rbp+0x88ull), uint32_t(R.r15)); goto L_180003566;
L_180003566:
  M.write32((R.rbp+0x68ull), uint32_t(R.r12)); goto L_18000356a;
L_18000356a:
  M.write32((R.rbp+0x90ull), uint32_t(R.r15)); goto L_180003571;
L_180003571:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003576;
L_180003576:
  R.r9=uint32_t(M.read32((R.rbp-0x20ull))); goto L_18000357a;
L_18000357a:
  R.rbx=uint32_t(uint32_t(R.rax)); goto L_18000357c;
L_18000357c:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_18000357f;
L_18000357f:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180003582;
L_180003582:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003586;
L_180003586:
  R.rdx=uint32_t(uint32_t(R.r12)); goto L_180003589;
L_180003589:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_18000358d;
L_18000358d:
  R.rax=uint64_t((R.rbp+0x90ull)); goto L_180003594;
L_180003594:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180003599;
L_180003599:
  R.rax=uint64_t((R.rbp+0x68ull)); goto L_18000359d;
L_18000359d:
  M.write64((R.rsp+0x28ull), R.rax); goto L_1800035a2;
L_1800035a2:
  R.rax=uint32_t(M.read32((R.rbp-0x24ull))); goto L_1800035a5;
L_1800035a5:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_1800035a9;
L_1800035a9:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_1800035ae;
L_1800035ae:
  R.r11=uint32_t(M.read32((R.rbp+0x68ull))); goto L_1800035b2;
L_1800035b2:
  R.rdi=uint32_t(M.read32((R.rbp+0x58ull))); goto L_1800035b5;
L_1800035b5:
  R.rcx=uint32_t(uint32_t(R.rdi)); goto L_1800035b7;
L_1800035b7:
  R.r9=uint32_t(M.read32((R.rbp+0x90ull))); goto L_1800035be;
L_1800035be:
  R.r8=uint64_t(M.read64((R.rbp+0xa8ull))); goto L_1800035c5;
L_1800035c5:
  R.r10=uint32_t(M.read32((R.rbp+0x88ull))); goto L_1800035cc;
L_1800035cc:
  M.write32((R.rbp+0x80ull), uint32_t(R.rax)); goto L_1800035d2;
L_1800035d2:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_1800035d5;
L_1800035d5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r12),32);
  R.rax=uint32_t(T);
  goto L_1800035d8;
L_1800035d8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800035d9;
L_1800035d9:
  M.write32((R.r8), uint32_t(R.r12)); goto L_1800035dc;
L_1800035dc:
  M.write32((R.r13), uint32_t(R.r15)); goto L_1800035e0;
L_1800035e0:
  R.r15=uint32_t(uint32_t(R.rax)); goto L_1800035e3;
L_1800035e3:
  T=(uint32_t(R.r15)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r15=uint32_t(T);
  goto L_1800035e6;
L_1800035e6:
  R.rax=uint32_t(uint32_t(R.rdi)); goto L_1800035e8;
L_1800035e8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r12),32);
  R.rax=uint32_t(T);
  goto L_1800035eb;
L_1800035eb:
  T=M.subflags(uint32_t(R.r15),uint32_t(R.rdx),32);
  R.r15=uint32_t(T);
  goto L_1800035ee;
L_1800035ee:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800035ef;
L_1800035ef:
  R.r12=uint32_t(uint32_t(R.rax)); goto L_1800035f2;
L_1800035f2:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_1800035f9;
L_1800035f9:
  T=(uint32_t(R.r12)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r12=uint32_t(T);
  goto L_1800035fc;
L_1800035fc:
  T=M.subflags(uint32_t(R.r12),uint32_t(R.rdx),32);
  R.r12=uint32_t(T);
  goto L_1800035ff;
L_1800035ff:
  T=M.subflags(uint32_t(R.r15),uint32_t(R.r12),32);
  goto L_180003602;
L_180003602:
  if(M.sf!=M.of){R.rcx=uint32_t(uint32_t(R.r11));} goto L_180003606;
L_180003606:
  M.write32((R.rax), uint32_t(R.rcx)); goto L_180003608;
L_180003608:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_18000360b;
L_18000360b:
  R.rcx=uint32_t(M.read32((R.rbp+0x60ull))); goto L_18000360e;
L_18000360e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003610;
L_180003610:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003611;
L_180003611:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003613;
L_180003613:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003615;
L_180003615:
  M.write32((R.rbp+0x60ull), uint32_t(R.rax)); goto L_180003618;
L_180003618:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_18000361b;
L_18000361b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_18000361d;
L_18000361d:
  R.rcx=uint32_t(uint32_t(R.r10)); goto L_180003620;
L_180003620:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003621;
L_180003621:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003623;
L_180003623:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003625;
L_180003625:
  R.rdx=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003628;
L_180003628:
  T=M.subflags(uint32_t(R.rdx),uint32_t(R.rax),32);
  goto L_18000362a;
L_18000362a:
  M.write32((R.rbp+0x68ull), uint32_t(R.rax)); goto L_18000362d;
L_18000362d:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180003634;
L_180003634:
  if(M.sf!=M.of){R.rcx=uint32_t(uint32_t(R.r9));} goto L_180003638;
L_180003638:
  M.write32((R.rax), uint32_t(R.rcx)); goto L_18000363a;
L_18000363a:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_18000363c;
L_18000363c:
  if (!M.zf) goto L_180003651; goto L_18000363e;
L_18000363e:
  T=M.subflags(M.read32((R.rbp+0x80ull)),uint32_t(R.rbx),32);
  goto L_180003644;
L_180003644:
  if (!M.zf) goto L_180003651; goto L_180003646;
L_180003646:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_18000364a;
L_18000364a:
  M.write32((R.rax), uint32_t(R.rbx)); goto L_18000364c;
L_18000364c:
  goto L_1800036d3;
L_180003651:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180003655;
L_180003655:
  M.write32((R.rax), 1ull); goto L_18000365b;
L_18000365b:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180003662;
L_180003662:
  T=M.subflags(uint32_t(R.r15),uint32_t(R.r12),32);
  goto L_180003665;
L_180003665:
  if (M.zf||(M.sf!=M.of)) goto L_18000366f; goto L_180003667;
L_180003667:
  M.write32((R.rax), uint32_t(R.r11)); goto L_18000366a;
L_18000366a:
  M.write32((R.r8), uint32_t(R.rdi)); goto L_18000366d;
L_18000366d:
  goto L_180003674;
L_18000366f:
  M.write32((R.rax), uint32_t(R.rdi)); goto L_180003671;
L_180003671:
  M.write32((R.r8), uint32_t(R.r11)); goto L_180003674;
L_180003674:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_18000367b;
L_18000367b:
  T=M.subflags(uint32_t(R.rdx),M.read32((R.rbp+0x68ull)),32);
  goto L_18000367e;
L_18000367e:
  if (M.zf||(M.sf!=M.of)) goto L_180003689; goto L_180003680;
L_180003680:
  M.write32((R.rax), uint32_t(R.r9)); goto L_180003683;
L_180003683:
  M.write32((R.r13), uint32_t(R.r10)); goto L_180003687;
L_180003687:
  goto L_180003690;
L_180003689:
  M.write32((R.rax), uint32_t(R.r10)); goto L_18000368c;
L_18000368c:
  M.write32((R.r13), uint32_t(R.r9)); goto L_180003690;
L_180003690:
  R.rax=uint64_t(int64_t(int32_t(M.read32((R.rbp-0x24ull))))); goto L_180003694;
L_180003694:
  R.r9=uint64_t((0x18000369b-0x369bull)); goto L_18000369b;
L_18000369b:
  R.rcx=uint32_t(M.read32((R.r9+(R.rax*4ull)+0xf0c8ull))); goto L_1800036a3;
L_1800036a3:
  T=M.addflags(uint32_t(R.rcx),M.read32((R.r8)),32); R.rcx=uint32_t(T); goto L_1800036a6;
L_1800036a6:
  T=(uint32_t(R.rcx)) & (uint32_t(R.rcx)); M.logicflags(T,32);
  goto L_1800036a8;
L_1800036a8:
  if (M.zf||(M.sf!=M.of)) goto L_1800036d3; goto L_1800036aa;
L_1800036aa:
  R.r10=uint64_t(M.read64((R.rbp+0x48ull))); goto L_1800036ae;
L_1800036ae:
  R.rdx=uint64_t(M.read64((R.r10+0x10ull))); goto L_1800036b2;
L_1800036b2:
  T=M.subflags(uint32_t(R.rcx),M.read32((R.rdx+0x24ull)),32);
  goto L_1800036b5;
L_1800036b5:
  if (M.sf==M.of) goto L_1800036d3; goto L_1800036b7;
L_1800036b7:
  R.rax=uint32_t(M.read32((R.r9+(R.rax*4ull)+0xf0f0ull))); goto L_1800036bf;
L_1800036bf:
  T=M.addflags(uint32_t(R.rax),M.read32((R.r13)),32); R.rax=uint32_t(T); goto L_1800036c3;
L_1800036c3:
  T=(uint32_t(R.rax)) & (uint32_t(R.rax)); M.logicflags(T,32);
  goto L_1800036c5;
L_1800036c5:
  if (M.zf||(M.sf!=M.of)) goto L_1800036d3; goto L_1800036c7;
L_1800036c7:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rdx+0x28ull)),32);
  goto L_1800036ca;
L_1800036ca:
  if (M.sf==M.of) goto L_1800036d3; goto L_1800036cc;
L_1800036cc:
  M.write32((R.r8), uint32_t(R.rcx)); goto L_1800036cf;
L_1800036cf:
  M.write32((R.r13), uint32_t(R.rax)); goto L_1800036d3;
L_1800036d3:
  R.rax=uint64_t(M.read64((R.rbp+0x98ull))); goto L_1800036da;
L_1800036da:
  R.rax=uint32_t(M.read32((R.rax))); goto L_1800036dc;
L_1800036dc:
  T=M.subflags(uint32_t(R.rax),M.read32((R.rsi)),32);
  R.rax=uint32_t(T);
  goto L_1800036de;
L_1800036de:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800036df;
L_1800036df:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_1800036e1;
L_1800036e1:
  R.rax=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_1800036e8;
L_1800036e8:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_1800036ea;
L_1800036ea:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_1800036ec;
L_1800036ec:
  R.rax=uint32_t(M.read32((R.rax))); goto L_1800036ee;
L_1800036ee:
  T=M.subflags(uint32_t(R.rax),M.read32((R.r14)),32);
  R.rax=uint32_t(T);
  goto L_1800036f1;
L_1800036f1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800036f2;
L_1800036f2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800036f4;
L_1800036f4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800036f6;
L_1800036f6:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_1800036f8;
L_1800036f8:
  if(!M.zf&&(M.sf==M.of)){R.rax=uint32_t(uint32_t(R.rcx));} goto L_1800036fb;
L_1800036fb:
  T=(uint8_t(R.rax)) & (1ull); M.logicflags(T,8);
  goto L_1800036fd;
L_1800036fd:
  if (!M.zf) goto L_180003fd7; goto L_180003703;
L_180003703:
  R.rax=uint64_t(M.read64((R.rbp+0x78ull))); goto L_180003707;
L_180003707:
  M.write8((R.rax), 1ull); goto L_18000370a;
L_18000370a:
  goto L_180003fd7;
L_18000370f:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180003713;
L_180003713:
  R.r13=uint64_t(M.read64((R.rbp+0x88ull))); goto L_18000371a;
L_18000371a:
  R.r8=uint32_t(M.read32((R.rbp-0x28ull))); goto L_18000371e;
L_18000371e:
  R.r9=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180003725;
L_180003725:
  M.write32((R.rax), 2ull); goto L_18000372b;
L_18000372b:
  R.rax=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180003732;
L_180003732:
  M.write32((R.r13), uint32_t(R.r8)); goto L_180003736;
L_180003736:
  M.write32((R.rbp+0xa8ull), uint32_t(R.r8)); goto L_18000373d;
L_18000373d:
  M.write32((R.rbp+0x88ull), uint32_t(R.r9)); goto L_180003744;
L_180003744:
  M.write32((R.rax), uint32_t(R.r9)); goto L_180003747;
L_180003747:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000374a;
L_18000374a:
  if (M.zf) goto L_1800037e0; goto L_180003750;
L_180003750:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003752;
L_180003752:
  if (!M.zf) goto L_180003789; goto L_180003754;
L_180003754:
  T=(R.r12) & (R.r12); M.logicflags(T,64);
  goto L_180003757;
L_180003757:
  if (M.zf) goto L_1800037e0; goto L_18000375d;
L_18000375d:
  R.rax=uint32_t(M.read8((R.r12+0x1ull))); goto L_180003763;
L_180003763:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003766;
L_180003766:
  if (!M.zf) goto L_1800037e0; goto L_180003768;
L_180003768:
  R.rax=uint32_t(M.read8((R.r12+0x3ull))); goto L_18000376e;
L_18000376e:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180003771;
L_180003771:
  if (!M.zf) goto L_1800037e0; goto L_180003773;
L_180003773:
  R.rax=uint32_t(M.read8((R.r12+0x2ull))); goto L_180003779;
L_180003779:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_18000377c;
L_18000377c:
  if (!M.zf) goto L_1800037e0; goto L_18000377e;
L_18000377e:
  R.rax=uint32_t(M.read8((R.r12))); goto L_180003783;
L_180003783:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180003785;
L_180003785:
  if (!M.zf) goto L_1800037e0; goto L_180003787;
L_180003787:
  goto L_1800037f3;
L_180003789:
  T=(R.r12) & (R.r12); M.logicflags(T,64);
  goto L_18000378c;
L_18000378c:
  if (M.zf) goto L_1800037e0; goto L_18000378e;
L_18000378e:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003792;
L_180003792:
  R.rcx=uint32_t(M.read8((R.r12+0x1ull))); goto L_180003798;
L_180003798:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_18000379a;
L_18000379a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000379b;
L_18000379b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000379d;
L_18000379d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000379f;
L_18000379f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800037a1;
L_1800037a1:
  if (!M.zf&&(M.sf==M.of)) goto L_1800037e0; goto L_1800037a3;
L_1800037a3:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_1800037a7;
L_1800037a7:
  R.rcx=uint32_t(M.read8((R.r12+0x3ull))); goto L_1800037ad;
L_1800037ad:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800037af;
L_1800037af:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800037b0;
L_1800037b0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800037b2;
L_1800037b2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800037b4;
L_1800037b4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800037b6;
L_1800037b6:
  if (!M.zf&&(M.sf==M.of)) goto L_1800037e0; goto L_1800037b8;
L_1800037b8:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_1800037bc;
L_1800037bc:
  R.rcx=uint32_t(M.read8((R.r12+0x2ull))); goto L_1800037c2;
L_1800037c2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800037c4;
L_1800037c4:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800037c5;
L_1800037c5:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800037c7;
L_1800037c7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800037c9;
L_1800037c9:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800037cb;
L_1800037cb:
  if (!M.zf&&(M.sf==M.of)) goto L_1800037e0; goto L_1800037cd;
L_1800037cd:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_1800037d0;
L_1800037d0:
  R.rcx=uint32_t(M.read8((R.r12))); goto L_1800037d5;
L_1800037d5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800037d7;
L_1800037d7:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800037d8;
L_1800037d8:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800037da;
L_1800037da:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800037dc;
L_1800037dc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800037de;
L_1800037de:
  if (M.zf||(M.sf!=M.of)) goto L_1800037f3; goto L_1800037e0;
L_1800037e0:
  R.rdx=uint64_t(R.r12); goto L_1800037e3;
L_1800037e3:
  R.rcx=uint64_t(R.rbx); goto L_1800037e6;
L_1800037e6:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_1800037eb;
L_1800037eb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800037ed;
L_1800037ed:
  if (M.zf||(M.sf!=M.of)) goto L_18000398b; goto L_1800037f3;
L_1800037f3:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_1800037f6;
L_1800037f6:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_1800037fd;
L_1800037fd:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180003801;
L_180003801:
  R.r8=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180003808;
L_180003808:
  R.rdx=uint32_t(M.read32((R.rbp-0x28ull))); goto L_18000380b;
L_18000380b:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_18000380f;
L_18000380f:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003813;
L_180003813:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180003816;
L_180003816:
  M.write64((R.rsp+0x30ull), R.r12); goto L_18000381b;
L_18000381b:
  M.write64((R.rsp+0x28ull), R.r13); goto L_180003820;
L_180003820:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003824;
L_180003824:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003829;
L_180003829:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000382c;
L_18000382c:
  if (M.zf) goto L_1800038b6; goto L_180003832;
L_180003832:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003834;
L_180003834:
  if (!M.zf) goto L_180003863; goto L_180003836;
L_180003836:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180003839;
L_180003839:
  if (M.zf) goto L_1800038b6; goto L_18000383b;
L_18000383b:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_180003840;
L_180003840:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003843;
L_180003843:
  if (!M.zf) goto L_1800038b6; goto L_180003845;
L_180003845:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_18000384a;
L_18000384a:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_18000384d;
L_18000384d:
  if (!M.zf) goto L_1800038b6; goto L_18000384f;
L_18000384f:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_180003854;
L_180003854:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_180003857;
L_180003857:
  if (!M.zf) goto L_1800038b6; goto L_180003859;
L_180003859:
  R.rax=uint32_t(M.read8((R.r15))); goto L_18000385d;
L_18000385d:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_18000385f;
L_18000385f:
  if (!M.zf) goto L_1800038b6; goto L_180003861;
L_180003861:
  goto L_1800038c5;
L_180003863:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_180003866;
L_180003866:
  if (M.zf) goto L_1800038b6; goto L_180003868;
L_180003868:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_18000386c;
L_18000386c:
  R.rcx=uint32_t(M.read8((R.r15+0x1ull))); goto L_180003871;
L_180003871:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003873;
L_180003873:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003874;
L_180003874:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003876;
L_180003876:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003878;
L_180003878:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000387a;
L_18000387a:
  if (!M.zf&&(M.sf==M.of)) goto L_1800038b6; goto L_18000387c;
L_18000387c:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003880;
L_180003880:
  R.rcx=uint32_t(M.read8((R.r15+0x3ull))); goto L_180003885;
L_180003885:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003887;
L_180003887:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003888;
L_180003888:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000388a;
L_18000388a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000388c;
L_18000388c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_18000388e;
L_18000388e:
  if (!M.zf&&(M.sf==M.of)) goto L_1800038b6; goto L_180003890;
L_180003890:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003894;
L_180003894:
  R.rcx=uint32_t(M.read8((R.r15+0x2ull))); goto L_180003899;
L_180003899:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_18000389b;
L_18000389b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000389c;
L_18000389c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000389e;
L_18000389e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800038a0;
L_1800038a0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800038a2;
L_1800038a2:
  if (!M.zf&&(M.sf==M.of)) goto L_1800038b6; goto L_1800038a4;
L_1800038a4:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_1800038a7;
L_1800038a7:
  R.rcx=uint32_t(M.read8((R.r15))); goto L_1800038ab;
L_1800038ab:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800038ad;
L_1800038ad:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800038ae;
L_1800038ae:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800038b0;
L_1800038b0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800038b2;
L_1800038b2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800038b4;
L_1800038b4:
  if (M.zf||(M.sf!=M.of)) goto L_1800038c5; goto L_1800038b6;
L_1800038b6:
  R.rdx=uint64_t(R.r15); goto L_1800038b9;
L_1800038b9:
  R.rcx=uint64_t(R.rbx); goto L_1800038bc;
L_1800038bc:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_1800038c1;
L_1800038c1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800038c3;
L_1800038c3:
  if (M.zf||(M.sf!=M.of)) goto L_180003902; goto L_1800038c5;
L_1800038c5:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_1800038c8;
L_1800038c8:
  R.r9=uint32_t(M.read32((R.rbp-0x20ull))); goto L_1800038cc;
L_1800038cc:
  R.r8=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_1800038d3;
L_1800038d3:
  R.rdx=uint32_t(M.read32((R.rbp-0x28ull))); goto L_1800038d6;
L_1800038d6:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_1800038da;
L_1800038da:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_1800038de;
L_1800038de:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_1800038e5;
L_1800038e5:
  M.write64((R.rsp+0x30ull), R.rax); goto L_1800038ea;
L_1800038ea:
  R.rax=uint64_t((R.rbp+0xa8ull)); goto L_1800038f1;
L_1800038f1:
  M.write64((R.rsp+0x28ull), R.rax); goto L_1800038f6;
L_1800038f6:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_1800038f9;
L_1800038f9:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_1800038fd;
L_1800038fd:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003902;
L_180003902:
  R.r8=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180003906;
L_180003906:
  R.r10=uint32_t(uint32_t(R.r8)); goto L_180003909;
L_180003909:
  T=M.subflags(uint32_t(R.r10),M.read32((R.r13)),32);
  R.r10=uint32_t(T);
  goto L_18000390d;
L_18000390d:
  R.r15=uint32_t(M.read32((R.rbp+0xa8ull))); goto L_180003914;
L_180003914:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.r15),32);
  R.r8=uint32_t(T);
  goto L_180003917;
L_180003917:
  R.r9=uint32_t(M.read32((R.rbp+0x60ull))); goto L_18000391b;
L_18000391b:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_18000391e;
L_18000391e:
  T=M.subflags(uint32_t(R.r9),M.read32((R.rbp+0x88ull)),32);
  R.r9=uint32_t(T);
  goto L_180003925;
L_180003925:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003926;
L_180003926:
  R.r11=uint32_t(M.read32((R.rbp+0x60ull))); goto L_18000392a;
L_18000392a:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_18000392c;
L_18000392c:
  T=M.subflags(uint32_t(R.r11),M.read32((R.r12)),32);
  R.r11=uint32_t(T);
  goto L_180003930;
L_180003930:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180003932;
L_180003932:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180003934;
L_180003934:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003937;
L_180003937:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003938;
L_180003938:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000393a;
L_18000393a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000393c;
L_18000393c:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_18000393e;
L_18000393e:
  if(M.zf||(M.sf!=M.of)){R.r8=uint32_t(uint32_t(R.r9));} goto L_180003942;
L_180003942:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180003945;
L_180003945:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003946;
L_180003946:
  R.r8=uint32_t(uint32_t(R.rax)); goto L_180003949;
L_180003949:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_18000394c;
L_18000394c:
  T=(uint32_t(R.r8)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r8=uint32_t(T);
  goto L_18000394f;
L_18000394f:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rdx),32);
  R.r8=uint32_t(T);
  goto L_180003952;
L_180003952:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003953;
L_180003953:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180003955;
L_180003955:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180003958;
L_180003958:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_18000395a;
L_18000395a:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_18000395c;
L_18000395c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000395d;
L_18000395d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000395f;
L_18000395f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003961;
L_180003961:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180003963;
L_180003963:
  if(M.zf||(M.sf!=M.of)){R.r10=uint32_t(uint32_t(R.r11));} goto L_180003967;
L_180003967:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_18000396a;
L_18000396a:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_18000396b;
L_18000396b:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_18000396d;
L_18000396d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_18000396f;
L_18000396f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180003972;
L_180003972:
  if (M.sf==M.of) goto L_180003a69; goto L_180003978;
L_180003978:
  R.rax=uint32_t(M.read32((R.rbp+0x88ull))); goto L_18000397e;
L_18000397e:
  M.write32((R.r13), uint32_t(R.r15)); goto L_180003982;
L_180003982:
  M.write32((R.r12), uint32_t(R.rax)); goto L_180003986;
L_180003986:
  goto L_180003a69;
L_18000398b:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_18000398e;
L_18000398e:
  if (M.zf) goto L_180003a18; goto L_180003994;
L_180003994:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003996;
L_180003996:
  if (!M.zf) goto L_1800039c5; goto L_180003998;
L_180003998:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_18000399b;
L_18000399b:
  if (M.zf) goto L_180003a18; goto L_18000399d;
L_18000399d:
  R.rax=uint32_t(M.read8((R.r15+0x1ull))); goto L_1800039a2;
L_1800039a2:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_1800039a5;
L_1800039a5:
  if (!M.zf) goto L_180003a18; goto L_1800039a7;
L_1800039a7:
  R.rax=uint32_t(M.read8((R.r15+0x3ull))); goto L_1800039ac;
L_1800039ac:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_1800039af;
L_1800039af:
  if (!M.zf) goto L_180003a18; goto L_1800039b1;
L_1800039b1:
  R.rax=uint32_t(M.read8((R.r15+0x2ull))); goto L_1800039b6;
L_1800039b6:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_1800039b9;
L_1800039b9:
  if (!M.zf) goto L_180003a18; goto L_1800039bb;
L_1800039bb:
  R.rax=uint32_t(M.read8((R.r15))); goto L_1800039bf;
L_1800039bf:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_1800039c1;
L_1800039c1:
  if (!M.zf) goto L_180003a18; goto L_1800039c3;
L_1800039c3:
  goto L_180003a27;
L_1800039c5:
  T=(R.r15) & (R.r15); M.logicflags(T,64);
  goto L_1800039c8;
L_1800039c8:
  if (M.zf) goto L_180003a18; goto L_1800039ca;
L_1800039ca:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_1800039ce;
L_1800039ce:
  R.rcx=uint32_t(M.read8((R.r15+0x1ull))); goto L_1800039d3;
L_1800039d3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800039d5;
L_1800039d5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800039d6;
L_1800039d6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800039d8;
L_1800039d8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800039da;
L_1800039da:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800039dc;
L_1800039dc:
  if (!M.zf&&(M.sf==M.of)) goto L_180003a18; goto L_1800039de;
L_1800039de:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_1800039e2;
L_1800039e2:
  R.rcx=uint32_t(M.read8((R.r15+0x3ull))); goto L_1800039e7;
L_1800039e7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800039e9;
L_1800039e9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800039ea;
L_1800039ea:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_1800039ec;
L_1800039ec:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_1800039ee;
L_1800039ee:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_1800039f0;
L_1800039f0:
  if (!M.zf&&(M.sf==M.of)) goto L_180003a18; goto L_1800039f2;
L_1800039f2:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_1800039f6;
L_1800039f6:
  R.rcx=uint32_t(M.read8((R.r15+0x2ull))); goto L_1800039fb;
L_1800039fb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_1800039fd;
L_1800039fd:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_1800039fe;
L_1800039fe:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003a00;
L_180003a00:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003a02;
L_180003a02:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003a04;
L_180003a04:
  if (!M.zf&&(M.sf==M.of)) goto L_180003a18; goto L_180003a06;
L_180003a06:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_180003a09;
L_180003a09:
  R.rcx=uint32_t(M.read8((R.r15))); goto L_180003a0d;
L_180003a0d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003a0f;
L_180003a0f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003a10;
L_180003a10:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003a12;
L_180003a12:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003a14;
L_180003a14:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003a16;
L_180003a16:
  if (M.zf||(M.sf!=M.of)) goto L_180003a27; goto L_180003a18;
L_180003a18:
  R.rdx=uint64_t(R.r15); goto L_180003a1b;
L_180003a1b:
  R.rcx=uint64_t(R.rbx); goto L_180003a1e;
L_180003a1e:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003a23;
L_180003a23:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003a25;
L_180003a25:
  if (M.zf||(M.sf!=M.of)) goto L_180003a62; goto L_180003a27;
L_180003a27:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180003a2a;
L_180003a2a:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180003a31;
L_180003a31:
  R.r15=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180003a38;
L_180003a38:
  R.r8=uint32_t(uint32_t(R.r15)); goto L_180003a3b;
L_180003a3b:
  R.r9=uint32_t(M.read32((R.rbp-0x20ull))); goto L_180003a3f;
L_180003a3f:
  R.rdx=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180003a42;
L_180003a42:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003a46;
L_180003a46:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003a4a;
L_180003a4a:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180003a4d;
L_180003a4d:
  M.write64((R.rsp+0x30ull), R.r12); goto L_180003a52;
L_180003a52:
  M.write64((R.rsp+0x28ull), R.r13); goto L_180003a57;
L_180003a57:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003a5b;
L_180003a5b:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003a60;
L_180003a60:
  goto L_180003a70;
L_180003a62:
  R.r12=uint64_t(M.read64((R.rbp+0x90ull))); goto L_180003a69;
L_180003a69:
  R.r15=uint32_t(M.read32((R.rbp+0xb0ull))); goto L_180003a70;
L_180003a70:
  R.rax=uint32_t(M.read32((R.rbp-0x28ull))); goto L_180003a73;
L_180003a73:
  T=M.subflags(M.read32((R.r13)),uint32_t(R.rax),32);
  goto L_180003a77;
L_180003a77:
  if (!M.zf) goto L_180003bdb; goto L_180003a7d;
L_180003a7d:
  T=M.subflags(M.read32((R.r12)),uint32_t(R.r15),32);
  goto L_180003a81;
L_180003a81:
  if (!M.zf) goto L_180003bdb; goto L_180003a87;
L_180003a87:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003a8a;
L_180003a8a:
  if (M.zf) goto L_180003c5c; goto L_180003a90;
L_180003a90:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003a92;
L_180003a92:
  if (!M.zf) goto L_180003b06; goto L_180003a94;
L_180003a94:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003a97;
L_180003a97:
  if (M.zf) goto L_180003c5c; goto L_180003a9d;
L_180003a9d:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003aa1;
L_180003aa1:
  T=M.subflags(uint8_t(R.rax),M.read8((R.rsi+0x1ull)),8);
  goto L_180003aa4;
L_180003aa4:
  if (!M.zf) goto L_180003be9; goto L_180003aaa;
L_180003aaa:
  R.rcx=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003aae;
L_180003aae:
  T=M.subflags(uint8_t(R.rcx),M.read8((R.rsi+0x3ull)),8);
  goto L_180003ab1;
L_180003ab1:
  if (!M.zf) goto L_180003be9; goto L_180003ab7;
L_180003ab7:
  R.rdx=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003abb;
L_180003abb:
  T=M.subflags(uint8_t(R.rdx),M.read8((R.rsi+0x2ull)),8);
  goto L_180003abe;
L_180003abe:
  if (!M.zf) goto L_180003be9; goto L_180003ac4;
L_180003ac4:
  R.r8=uint32_t(M.read8((R.rbx))); goto L_180003ac8;
L_180003ac8:
  T=M.subflags(uint8_t(R.r8),M.read8((R.rsi)),8);
  goto L_180003acb;
L_180003acb:
  if (!M.zf) goto L_180003be9; goto L_180003ad1;
L_180003ad1:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003ad4;
L_180003ad4:
  if (M.zf) goto L_180003be9; goto L_180003ada;
L_180003ada:
  T=M.subflags(uint8_t(R.rax),M.read8((R.r14+0x1ull)),8);
  goto L_180003ade;
L_180003ade:
  if (!M.zf) goto L_180003be9; goto L_180003ae4;
L_180003ae4:
  T=M.subflags(uint8_t(R.rcx),M.read8((R.r14+0x3ull)),8);
  goto L_180003ae8;
L_180003ae8:
  if (!M.zf) goto L_180003be9; goto L_180003aee;
L_180003aee:
  T=M.subflags(uint8_t(R.rdx),M.read8((R.r14+0x2ull)),8);
  goto L_180003af2;
L_180003af2:
  if (!M.zf) goto L_180003be9; goto L_180003af8;
L_180003af8:
  T=M.subflags(uint8_t(R.r8),M.read8((R.r14)),8);
  goto L_180003afb;
L_180003afb:
  if (!M.zf) goto L_180003be9; goto L_180003b01;
L_180003b01:
  goto L_180003bd1;
L_180003b06:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003b09;
L_180003b09:
  if (M.zf) goto L_180003c5c; goto L_180003b0f;
L_180003b0f:
  R.r11=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003b14;
L_180003b14:
  R.rcx=uint32_t(M.read8((R.rsi+0x1ull))); goto L_180003b18;
L_180003b18:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180003b1b;
L_180003b1b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003b1d;
L_180003b1d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003b1e;
L_180003b1e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003b20;
L_180003b20:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003b22;
L_180003b22:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003b24;
L_180003b24:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003b2a;
L_180003b2a:
  R.r10=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003b2f;
L_180003b2f:
  R.rcx=uint32_t(M.read8((R.rsi+0x3ull))); goto L_180003b33;
L_180003b33:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180003b36;
L_180003b36:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003b38;
L_180003b38:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003b39;
L_180003b39:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003b3b;
L_180003b3b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003b3d;
L_180003b3d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003b3f;
L_180003b3f:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003b45;
L_180003b45:
  R.r9=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003b4a;
L_180003b4a:
  R.rcx=uint32_t(M.read8((R.rsi+0x2ull))); goto L_180003b4e;
L_180003b4e:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003b51;
L_180003b51:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003b53;
L_180003b53:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003b54;
L_180003b54:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003b56;
L_180003b56:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003b58;
L_180003b58:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003b5a;
L_180003b5a:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003b60;
L_180003b60:
  R.r8=uint32_t(M.read8((R.rbx))); goto L_180003b64;
L_180003b64:
  R.rcx=uint32_t(M.read8((R.rsi))); goto L_180003b67;
L_180003b67:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180003b6a;
L_180003b6a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003b6c;
L_180003b6c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003b6d;
L_180003b6d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003b6f;
L_180003b6f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003b71;
L_180003b71:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003b73;
L_180003b73:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003b79;
L_180003b79:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003b7c;
L_180003b7c:
  if (M.zf) goto L_180003c12; goto L_180003b82;
L_180003b82:
  R.rcx=uint32_t(M.read8((R.r14+0x1ull))); goto L_180003b87;
L_180003b87:
  T=M.subflags(uint32_t(R.r11),uint32_t(R.rcx),32);
  R.r11=uint32_t(T);
  goto L_180003b8a;
L_180003b8a:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180003b8d;
L_180003b8d:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003b8e;
L_180003b8e:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003b90;
L_180003b90:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003b92;
L_180003b92:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003b94;
L_180003b94:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003b96;
L_180003b96:
  R.rcx=uint32_t(M.read8((R.r14+0x3ull))); goto L_180003b9b;
L_180003b9b:
  T=M.subflags(uint32_t(R.r10),uint32_t(R.rcx),32);
  R.r10=uint32_t(T);
  goto L_180003b9e;
L_180003b9e:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180003ba1;
L_180003ba1:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003ba2;
L_180003ba2:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ba4;
L_180003ba4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ba6;
L_180003ba6:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ba8;
L_180003ba8:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003baa;
L_180003baa:
  R.rcx=uint32_t(M.read8((R.r14+0x2ull))); goto L_180003baf;
L_180003baf:
  T=M.subflags(uint32_t(R.r9),uint32_t(R.rcx),32);
  R.r9=uint32_t(T);
  goto L_180003bb2;
L_180003bb2:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003bb5;
L_180003bb5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003bb6;
L_180003bb6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003bb8;
L_180003bb8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003bba;
L_180003bba:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003bbc;
L_180003bbc:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003bbe;
L_180003bbe:
  R.rcx=uint32_t(M.read8((R.r14))); goto L_180003bc2;
L_180003bc2:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rcx),32);
  R.r8=uint32_t(T);
  goto L_180003bc5;
L_180003bc5:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180003bc8;
L_180003bc8:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003bc9;
L_180003bc9:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003bcb;
L_180003bcb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003bcd;
L_180003bcd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003bcf;
L_180003bcf:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c12; goto L_180003bd1;
L_180003bd1:
  R.rax=uint64_t(M.read64((R.rbp+0x70ull))); goto L_180003bd5;
L_180003bd5:
  M.write32((R.rax), 3ull); goto L_180003bdb;
L_180003bdb:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003bde;
L_180003bde:
  if (M.zf) goto L_180003c5c; goto L_180003be0;
L_180003be0:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003be2;
L_180003be2:
  if (!M.zf) goto L_180003c0d; goto L_180003be4;
L_180003be4:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003be7;
L_180003be7:
  if (M.zf) goto L_180003c5c; goto L_180003be9;
L_180003be9:
  R.rax=uint32_t(M.read8((R.rsi+0x1ull))); goto L_180003bed;
L_180003bed:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003bf0;
L_180003bf0:
  if (!M.zf) goto L_180003c5c; goto L_180003bf2;
L_180003bf2:
  R.rax=uint32_t(M.read8((R.rsi+0x3ull))); goto L_180003bf6;
L_180003bf6:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180003bf9;
L_180003bf9:
  if (!M.zf) goto L_180003c5c; goto L_180003bfb;
L_180003bfb:
  R.rax=uint32_t(M.read8((R.rsi+0x2ull))); goto L_180003bff;
L_180003bff:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_180003c02;
L_180003c02:
  if (!M.zf) goto L_180003c5c; goto L_180003c04;
L_180003c04:
  R.rax=uint32_t(M.read8((R.rsi))); goto L_180003c07;
L_180003c07:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180003c09;
L_180003c09:
  if (!M.zf) goto L_180003c5c; goto L_180003c0b;
L_180003c0b:
  goto L_180003c6f;
L_180003c0d:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003c10;
L_180003c10:
  if (M.zf) goto L_180003c5c; goto L_180003c12;
L_180003c12:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003c16;
L_180003c16:
  R.rcx=uint32_t(M.read8((R.rsi+0x1ull))); goto L_180003c1a;
L_180003c1a:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003c1c;
L_180003c1c:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003c1d;
L_180003c1d:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003c1f;
L_180003c1f:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003c21;
L_180003c21:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003c23;
L_180003c23:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c5c; goto L_180003c25;
L_180003c25:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003c29;
L_180003c29:
  R.rcx=uint32_t(M.read8((R.rsi+0x3ull))); goto L_180003c2d;
L_180003c2d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003c2f;
L_180003c2f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003c30;
L_180003c30:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003c32;
L_180003c32:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003c34;
L_180003c34:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003c36;
L_180003c36:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c5c; goto L_180003c38;
L_180003c38:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003c3c;
L_180003c3c:
  R.rcx=uint32_t(M.read8((R.rsi+0x2ull))); goto L_180003c40;
L_180003c40:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003c42;
L_180003c42:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003c43;
L_180003c43:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003c45;
L_180003c45:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003c47;
L_180003c47:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003c49;
L_180003c49:
  if (!M.zf&&(M.sf==M.of)) goto L_180003c5c; goto L_180003c4b;
L_180003c4b:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_180003c4e;
L_180003c4e:
  R.rcx=uint32_t(M.read8((R.rsi))); goto L_180003c51;
L_180003c51:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003c53;
L_180003c53:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003c54;
L_180003c54:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003c56;
L_180003c56:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003c58;
L_180003c58:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003c5a;
L_180003c5a:
  if (M.zf||(M.sf!=M.of)) goto L_180003cba; goto L_180003c5c;
L_180003c5c:
  R.rdx=uint64_t(R.rsi); goto L_180003c5f;
L_180003c5f:
  R.rcx=uint64_t(R.rbx); goto L_180003c62;
L_180003c62:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003c67;
L_180003c67:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003c69;
L_180003c69:
  if (M.zf||(M.sf!=M.of)) goto L_180003d1c; goto L_180003c6f;
L_180003c6f:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003c72;
L_180003c72:
  if (M.zf) goto L_180003d0d; goto L_180003c78;
L_180003c78:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003c7a;
L_180003c7a:
  if (!M.zf) goto L_180003cba; goto L_180003c7c;
L_180003c7c:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003c7f;
L_180003c7f:
  if (M.zf) goto L_180003d0d; goto L_180003c85;
L_180003c85:
  R.rax=uint32_t(M.read8((R.r14+0x1ull))); goto L_180003c8a;
L_180003c8a:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003c8d;
L_180003c8d:
  if (!M.zf) goto L_180003d0d; goto L_180003c8f;
L_180003c8f:
  R.rax=uint32_t(M.read8((R.r14+0x3ull))); goto L_180003c94;
L_180003c94:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180003c97;
L_180003c97:
  if (!M.zf) goto L_180003d0d; goto L_180003c99;
L_180003c99:
  R.rax=uint32_t(M.read8((R.r14+0x2ull))); goto L_180003c9e;
L_180003c9e:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_180003ca1;
L_180003ca1:
  if (!M.zf) goto L_180003d0d; goto L_180003ca3;
L_180003ca3:
  R.rax=uint32_t(M.read8((R.r14))); goto L_180003ca7;
L_180003ca7:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180003ca9;
L_180003ca9:
  if (!M.zf) goto L_180003d0d; goto L_180003cab;
L_180003cab:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_180003cb2;
L_180003cb2:
  M.write8((R.rax), 1ull); goto L_180003cb5;
L_180003cb5:
  goto L_180003fd7;
L_180003cba:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003cbd;
L_180003cbd:
  if (M.zf) goto L_180003d0d; goto L_180003cbf;
L_180003cbf:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003cc3;
L_180003cc3:
  R.rcx=uint32_t(M.read8((R.r14+0x1ull))); goto L_180003cc8;
L_180003cc8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003cca;
L_180003cca:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003ccb;
L_180003ccb:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ccd;
L_180003ccd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ccf;
L_180003ccf:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003cd1;
L_180003cd1:
  if (!M.zf&&(M.sf==M.of)) goto L_180003d0d; goto L_180003cd3;
L_180003cd3:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003cd7;
L_180003cd7:
  R.rcx=uint32_t(M.read8((R.r14+0x3ull))); goto L_180003cdc;
L_180003cdc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003cde;
L_180003cde:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003cdf;
L_180003cdf:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ce1;
L_180003ce1:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ce3;
L_180003ce3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ce5;
L_180003ce5:
  if (!M.zf&&(M.sf==M.of)) goto L_180003d0d; goto L_180003ce7;
L_180003ce7:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003ceb;
L_180003ceb:
  R.rcx=uint32_t(M.read8((R.r14+0x2ull))); goto L_180003cf0;
L_180003cf0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003cf2;
L_180003cf2:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003cf3;
L_180003cf3:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003cf5;
L_180003cf5:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003cf7;
L_180003cf7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003cf9;
L_180003cf9:
  if (!M.zf&&(M.sf==M.of)) goto L_180003d0d; goto L_180003cfb;
L_180003cfb:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_180003cfe;
L_180003cfe:
  R.rcx=uint32_t(M.read8((R.r14))); goto L_180003d02;
L_180003d02:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003d04;
L_180003d04:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003d05;
L_180003d05:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003d07;
L_180003d07:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003d09;
L_180003d09:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003d0b;
L_180003d0b:
  if (M.zf||(M.sf!=M.of)) goto L_180003d46; goto L_180003d0d;
L_180003d0d:
  R.rdx=uint64_t(R.r14); goto L_180003d10;
L_180003d10:
  R.rcx=uint64_t(R.rbx); goto L_180003d13;
L_180003d13:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003d18;
L_180003d18:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003d1a;
L_180003d1a:
  if (!M.zf&&(M.sf==M.of)) goto L_180003d46; goto L_180003d1c;
L_180003d1c:
  R.r12=uint64_t(M.read64((R.rbp-0x18ull))); goto L_180003d20;
L_180003d20:
  R.r15=uint32_t(uint32_t(R.rdi)); goto L_180003d23;
L_180003d23:
  R.rdx=uint64_t(R.r12); goto L_180003d26;
L_180003d26:
  R.rcx=uint64_t(R.rsi); goto L_180003d29;
L_180003d29:
  T=M.subflags(0,uint32_t(R.r15),32); R.r15=uint32_t(T); goto L_180003d2c;
L_180003d2c:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003d31;
L_180003d31:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180003d34;
L_180003d34:
  if (M.sf==M.of) goto L_180003d55; goto L_180003d36;
L_180003d36:
  R.rdx=uint64_t(R.r12); goto L_180003d39;
L_180003d39:
  R.rcx=uint64_t(R.r14); goto L_180003d3c;
L_180003d3c:
  R.rax=uint32_t(ColorCompare8((const uint8_t*)R.rcx,(const uint8_t*)R.rdx)); goto L_180003d41;
L_180003d41:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r15),32);
  goto L_180003d44;
L_180003d44:
  if (M.sf==M.of) goto L_180003d55; goto L_180003d46;
L_180003d46:
  R.rax=uint64_t(M.read64((R.rbp+0x80ull))); goto L_180003d4d;
L_180003d4d:
  M.write8((R.rax), 1ull); goto L_180003d50;
L_180003d50:
  goto L_180003fd7;
L_180003d55:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180003d58;
L_180003d58:
  R.r13=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003d5c;
L_180003d5c:
  R.r8=uint32_t(uint32_t(R.r13)); goto L_180003d5f;
L_180003d5f:
  R.r12=uint32_t(M.read32((R.rbp+0x58ull))); goto L_180003d63;
L_180003d63:
  R.rdx=uint32_t(uint32_t(R.r12)); goto L_180003d66;
L_180003d66:
  R.r9=uint32_t(M.read32((R.rbp-0x20ull))); goto L_180003d6a;
L_180003d6a:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003d6e;
L_180003d6e:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003d72;
L_180003d72:
  R.rax=uint64_t((R.rbp+0x88ull)); goto L_180003d79;
L_180003d79:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180003d7e;
L_180003d7e:
  R.rax=uint64_t((R.rbp+0x90ull)); goto L_180003d85;
L_180003d85:
  M.write64((R.rsp+0x28ull), R.rax); goto L_180003d8a;
L_180003d8a:
  R.rax=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180003d8d;
L_180003d8d:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003d91;
L_180003d91:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003d96;
L_180003d96:
  R.rax=uint32_t(M.read32((R.rbp+0x50ull))); goto L_180003d99;
L_180003d99:
  R.r8=uint32_t(uint32_t(R.r13)); goto L_180003d9c;
L_180003d9c:
  R.r9=uint32_t(M.read32((R.rbp-0x1cull))); goto L_180003da0;
L_180003da0:
  R.rdx=uint32_t(uint32_t(R.r12)); goto L_180003da3;
L_180003da3:
  R.rcx=uint64_t(M.read64((R.rbp+0x48ull))); goto L_180003da7;
L_180003da7:
  M.write32((R.rsp+0x38ull), uint32_t(R.rax)); goto L_180003dab;
L_180003dab:
  R.rax=uint64_t((R.rbp+0x68ull)); goto L_180003daf;
L_180003daf:
  M.write64((R.rsp+0x30ull), R.rax); goto L_180003db4;
L_180003db4:
  R.rax=uint64_t((R.rbp+0x60ull)); goto L_180003db8;
L_180003db8:
  M.write64((R.rsp+0x28ull), R.rax); goto L_180003dbd;
L_180003dbd:
  R.rax=uint32_t(M.read32((R.rbp-0x24ull))); goto L_180003dc0;
L_180003dc0:
  M.write32((R.rsp+0x20ull), uint32_t(R.rax)); goto L_180003dc4;
L_180003dc4:
  R.rax=(uintptr_t)EdgeWalker8((RenderState*)R.rcx,(int)R.rdx,(int)R.r8,(int)R.r9,(uint32_t)M.read64(R.rsp+0x20),(int*)M.ptr(M.read64(R.rsp+0x28)),(int*)M.ptr(M.read64(R.rsp+0x30)),(int)M.read64(R.rsp+0x38)); goto L_180003dc9;
L_180003dc9:
  T=(uint32_t(R.rdi)) & (uint32_t(R.rdi)); M.logicflags(T,32);
  goto L_180003dcb;
L_180003dcb:
  if (!M.zf) goto L_180003e54; goto L_180003dd1;
L_180003dd1:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003dd4;
L_180003dd4:
  if (M.zf) goto L_180003e02; goto L_180003dd6;
L_180003dd6:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003dd9;
L_180003dd9:
  if (M.zf) goto L_180003e02; goto L_180003ddb;
L_180003ddb:
  R.rax=uint32_t(M.read8((R.rsi+0x1ull))); goto L_180003ddf;
L_180003ddf:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003de2;
L_180003de2:
  if (!M.zf) goto L_180003e02; goto L_180003de4;
L_180003de4:
  R.rax=uint32_t(M.read8((R.rsi+0x3ull))); goto L_180003de8;
L_180003de8:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180003deb;
L_180003deb:
  if (!M.zf) goto L_180003e02; goto L_180003ded;
L_180003ded:
  R.rax=uint32_t(M.read8((R.rsi+0x2ull))); goto L_180003df1;
L_180003df1:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_180003df4;
L_180003df4:
  if (!M.zf) goto L_180003e02; goto L_180003df6;
L_180003df6:
  R.rax=uint32_t(M.read8((R.rsi))); goto L_180003df9;
L_180003df9:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180003dfb;
L_180003dfb:
  if (!M.zf) goto L_180003e02; goto L_180003dfd;
L_180003dfd:
  R.r8=(R.r8&~0xffull)|(uint8_t(1ull)); goto L_180003e00;
L_180003e00:
  goto L_180003e05;
L_180003e02:
  T=(uint8_t(R.r8)) ^ (uint8_t(R.r8)); M.logicflags(T,8);
  R.r8=(R.r8&~0xffull)|(uint8_t(T));
  goto L_180003e05;
L_180003e05:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003e08;
L_180003e08:
  if (M.zf) goto L_180003f0c; goto L_180003e0e;
L_180003e0e:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003e11;
L_180003e11:
  if (M.zf) goto L_180003f0c; goto L_180003e17;
L_180003e17:
  R.rax=uint32_t(M.read8((R.r14+0x1ull))); goto L_180003e1c;
L_180003e1c:
  T=M.subflags(M.read8((R.rbx+0x1ull)),uint8_t(R.rax),8);
  goto L_180003e1f;
L_180003e1f:
  if (!M.zf) goto L_180003f0c; goto L_180003e25;
L_180003e25:
  R.rax=uint32_t(M.read8((R.r14+0x3ull))); goto L_180003e2a;
L_180003e2a:
  T=M.subflags(M.read8((R.rbx+0x3ull)),uint8_t(R.rax),8);
  goto L_180003e2d;
L_180003e2d:
  if (!M.zf) goto L_180003f0c; goto L_180003e33;
L_180003e33:
  R.rax=uint32_t(M.read8((R.r14+0x2ull))); goto L_180003e38;
L_180003e38:
  T=M.subflags(M.read8((R.rbx+0x2ull)),uint8_t(R.rax),8);
  goto L_180003e3b;
L_180003e3b:
  if (!M.zf) goto L_180003f0c; goto L_180003e41;
L_180003e41:
  R.rax=uint32_t(M.read8((R.r14))); goto L_180003e45;
L_180003e45:
  T=M.subflags(M.read8((R.rbx)),uint8_t(R.rax),8);
  goto L_180003e47;
L_180003e47:
  if (!M.zf) goto L_180003f0c; goto L_180003e4d;
L_180003e4d:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180003e4f;
L_180003e4f:
  goto L_180003f0e;
L_180003e54:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003e57;
L_180003e57:
  if (M.zf) goto L_180003ead; goto L_180003e59;
L_180003e59:
  T=(R.rsi) & (R.rsi); M.logicflags(T,64);
  goto L_180003e5c;
L_180003e5c:
  if (M.zf) goto L_180003ead; goto L_180003e5e;
L_180003e5e:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003e62;
L_180003e62:
  R.rcx=uint32_t(M.read8((R.rsi+0x1ull))); goto L_180003e66;
L_180003e66:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003e68;
L_180003e68:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003e69;
L_180003e69:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003e6b;
L_180003e6b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003e6d;
L_180003e6d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003e6f;
L_180003e6f:
  if (!M.zf&&(M.sf==M.of)) goto L_180003ead; goto L_180003e71;
L_180003e71:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003e75;
L_180003e75:
  R.rcx=uint32_t(M.read8((R.rsi+0x3ull))); goto L_180003e79;
L_180003e79:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003e7b;
L_180003e7b:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003e7c;
L_180003e7c:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003e7e;
L_180003e7e:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003e80;
L_180003e80:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003e82;
L_180003e82:
  if (!M.zf&&(M.sf==M.of)) goto L_180003ead; goto L_180003e84;
L_180003e84:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003e88;
L_180003e88:
  R.rcx=uint32_t(M.read8((R.rsi+0x2ull))); goto L_180003e8c;
L_180003e8c:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003e8e;
L_180003e8e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003e8f;
L_180003e8f:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003e91;
L_180003e91:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003e93;
L_180003e93:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003e95;
L_180003e95:
  if (!M.zf&&(M.sf==M.of)) goto L_180003ead; goto L_180003e97;
L_180003e97:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_180003e9a;
L_180003e9a:
  R.rcx=uint32_t(M.read8((R.rsi))); goto L_180003e9d;
L_180003e9d:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003e9f;
L_180003e9f:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003ea0;
L_180003ea0:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ea2;
L_180003ea2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ea4;
L_180003ea4:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ea6;
L_180003ea6:
  if (!M.zf&&(M.sf==M.of)) goto L_180003ead; goto L_180003ea8;
L_180003ea8:
  R.r8=(R.r8&~0xffull)|(uint8_t(1ull)); goto L_180003eab;
L_180003eab:
  goto L_180003eb0;
L_180003ead:
  T=(uint8_t(R.r8)) ^ (uint8_t(R.r8)); M.logicflags(T,8);
  R.r8=(R.r8&~0xffull)|(uint8_t(T));
  goto L_180003eb0;
L_180003eb0:
  T=(R.rbx) & (R.rbx); M.logicflags(T,64);
  goto L_180003eb3;
L_180003eb3:
  if (M.zf) goto L_180003f0c; goto L_180003eb5;
L_180003eb5:
  T=(R.r14) & (R.r14); M.logicflags(T,64);
  goto L_180003eb8;
L_180003eb8:
  if (M.zf) goto L_180003f0c; goto L_180003eba;
L_180003eba:
  R.rax=uint32_t(M.read8((R.rbx+0x1ull))); goto L_180003ebe;
L_180003ebe:
  R.rcx=uint32_t(M.read8((R.r14+0x1ull))); goto L_180003ec3;
L_180003ec3:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003ec5;
L_180003ec5:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003ec6;
L_180003ec6:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ec8;
L_180003ec8:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003eca;
L_180003eca:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ecc;
L_180003ecc:
  if (!M.zf&&(M.sf==M.of)) goto L_180003f0c; goto L_180003ece;
L_180003ece:
  R.rax=uint32_t(M.read8((R.rbx+0x3ull))); goto L_180003ed2;
L_180003ed2:
  R.rcx=uint32_t(M.read8((R.r14+0x3ull))); goto L_180003ed7;
L_180003ed7:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003ed9;
L_180003ed9:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003eda;
L_180003eda:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003edc;
L_180003edc:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ede;
L_180003ede:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ee0;
L_180003ee0:
  if (!M.zf&&(M.sf==M.of)) goto L_180003f0c; goto L_180003ee2;
L_180003ee2:
  R.rax=uint32_t(M.read8((R.rbx+0x2ull))); goto L_180003ee6;
L_180003ee6:
  R.rcx=uint32_t(M.read8((R.r14+0x2ull))); goto L_180003eeb;
L_180003eeb:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003eed;
L_180003eed:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003eee;
L_180003eee:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003ef0;
L_180003ef0:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003ef2;
L_180003ef2:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003ef4;
L_180003ef4:
  if (!M.zf&&(M.sf==M.of)) goto L_180003f0c; goto L_180003ef6;
L_180003ef6:
  R.rax=uint32_t(M.read8((R.rbx))); goto L_180003ef9;
L_180003ef9:
  R.rcx=uint32_t(M.read8((R.r14))); goto L_180003efd;
L_180003efd:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rcx),32);
  R.rax=uint32_t(T);
  goto L_180003eff;
L_180003eff:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f00;
L_180003f00:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003f02;
L_180003f02:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003f04;
L_180003f04:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdi),32);
  goto L_180003f06;
L_180003f06:
  if (!M.zf&&(M.sf==M.of)) goto L_180003f0c; goto L_180003f08;
L_180003f08:
  R.rax=(R.rax&~0xffull)|(uint8_t(1ull)); goto L_180003f0a;
L_180003f0a:
  goto L_180003f0e;
L_180003f0c:
  T=(uint8_t(R.rax)) ^ (uint8_t(R.rax)); M.logicflags(T,8);
  R.rax=(R.rax&~0xffull)|(uint8_t(T));
  goto L_180003f0e;
L_180003f0e:
  T=(uint8_t(R.r8)) & (uint8_t(R.r8)); M.logicflags(T,8);
  goto L_180003f11;
L_180003f11:
  if (!M.zf) goto L_180003fb5; goto L_180003f17;
L_180003f17:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180003f19;
L_180003f19:
  R.rax=uint32_t(M.read32((R.rbp+0x60ull))); goto L_180003f1c;
L_180003f1c:
  if (!M.zf) goto L_180003fa7; goto L_180003f22;
L_180003f22:
  R.rcx=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180003f25;
L_180003f25:
  R.r9=uint32_t(uint32_t(R.r12)); goto L_180003f28;
L_180003f28:
  R.rsi=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180003f2f;
L_180003f2f:
  T=M.subflags(uint32_t(R.r9),uint32_t(R.rax),32);
  R.r9=uint32_t(T);
  goto L_180003f32;
L_180003f32:
  R.rbx=uint32_t(M.read32((R.rbp+0x90ull))); goto L_180003f38;
L_180003f38:
  R.r10=uint32_t(uint32_t(R.r13)); goto L_180003f3b;
L_180003f3b:
  R.rdi=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180003f42;
L_180003f42:
  T=M.subflags(uint32_t(R.r10),uint32_t(R.rcx),32);
  R.r10=uint32_t(T);
  goto L_180003f45;
L_180003f45:
  R.r11=uint32_t(M.read32((R.rbp+0x88ull))); goto L_180003f4c;
L_180003f4c:
  T=M.subflags(uint32_t(R.r12),uint32_t(R.rbx),32);
  R.r12=uint32_t(T);
  goto L_180003f4f;
L_180003f4f:
  M.write32((R.rsi), uint32_t(R.rax)); goto L_180003f51;
L_180003f51:
  T=M.subflags(uint32_t(R.r13),uint32_t(R.r11),32);
  R.r13=uint32_t(T);
  goto L_180003f54;
L_180003f54:
  R.rax=uint32_t(uint32_t(R.r12)); goto L_180003f57;
L_180003f57:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f58;
L_180003f58:
  M.write32((R.rdi), uint32_t(R.rcx)); goto L_180003f5a;
L_180003f5a:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180003f5c;
L_180003f5c:
  R.rax=uint32_t(uint32_t(R.r13)); goto L_180003f5f;
L_180003f5f:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180003f61;
L_180003f61:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180003f63;
L_180003f63:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f64;
L_180003f64:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003f66;
L_180003f66:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003f68;
L_180003f68:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180003f6a;
L_180003f6a:
  if(M.zf||(M.sf!=M.of)){R.r12=uint32_t(uint32_t(R.r13));} goto L_180003f6e;
L_180003f6e:
  R.rax=uint32_t(uint32_t(R.r12)); goto L_180003f71;
L_180003f71:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f72;
L_180003f72:
  R.r8=uint32_t(uint32_t(R.rax)); goto L_180003f75;
L_180003f75:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003f78;
L_180003f78:
  T=(uint32_t(R.r8)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.r8=uint32_t(T);
  goto L_180003f7b;
L_180003f7b:
  T=M.subflags(uint32_t(R.r8),uint32_t(R.rdx),32);
  R.r8=uint32_t(T);
  goto L_180003f7e;
L_180003f7e:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f7f;
L_180003f7f:
  R.rcx=uint32_t(uint32_t(R.rax)); goto L_180003f81;
L_180003f81:
  R.rax=uint32_t(uint32_t(R.r10)); goto L_180003f84;
L_180003f84:
  T=(uint32_t(R.rcx)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rcx=uint32_t(T);
  goto L_180003f86;
L_180003f86:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rdx),32);
  R.rcx=uint32_t(T);
  goto L_180003f88;
L_180003f88:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f89;
L_180003f89:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003f8b;
L_180003f8b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003f8d;
L_180003f8d:
  T=M.subflags(uint32_t(R.rcx),uint32_t(R.rax),32);
  goto L_180003f8f;
L_180003f8f:
  if(M.zf||(M.sf!=M.of)){R.r9=uint32_t(uint32_t(R.r10));} goto L_180003f93;
L_180003f93:
  R.rax=uint32_t(uint32_t(R.r9)); goto L_180003f96;
L_180003f96:
  R.rdx=(uint32_t(R.rax)&0x80000000u)?0xffffffffu:0u; goto L_180003f97;
L_180003f97:
  T=(uint32_t(R.rax)) ^ (uint32_t(R.rdx)); M.logicflags(T,32);
  R.rax=uint32_t(T);
  goto L_180003f99;
L_180003f99:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.rdx),32);
  R.rax=uint32_t(T);
  goto L_180003f9b;
L_180003f9b:
  T=M.subflags(uint32_t(R.rax),uint32_t(R.r8),32);
  goto L_180003f9e;
L_180003f9e:
  if (M.zf||(M.sf!=M.of)) goto L_180003fd7; goto L_180003fa0;
L_180003fa0:
  M.write32((R.rsi), uint32_t(R.rbx)); goto L_180003fa2;
L_180003fa2:
  M.write32((R.rdi), uint32_t(R.r11)); goto L_180003fa5;
L_180003fa5:
  goto L_180003fd7;
L_180003fa7:
  R.rcx=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180003fae;
L_180003fae:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_180003fb0;
L_180003fb0:
  R.rax=uint32_t(M.read32((R.rbp+0x68ull))); goto L_180003fb3;
L_180003fb3:
  goto L_180003fce;
L_180003fb5:
  T=(uint8_t(R.rax)) & (uint8_t(R.rax)); M.logicflags(T,8);
  goto L_180003fb7;
L_180003fb7:
  if (!M.zf) goto L_180003fd7; goto L_180003fb9;
L_180003fb9:
  R.rax=uint32_t(M.read32((R.rbp+0x90ull))); goto L_180003fbf;
L_180003fbf:
  R.rcx=uint64_t(M.read64((R.rbp+0x98ull))); goto L_180003fc6;
L_180003fc6:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_180003fc8;
L_180003fc8:
  R.rax=uint32_t(M.read32((R.rbp+0x88ull))); goto L_180003fce;
L_180003fce:
  R.rcx=uint64_t(M.read64((R.rbp+0xa0ull))); goto L_180003fd5;
L_180003fd5:
  M.write32((R.rcx), uint32_t(R.rax)); goto L_180003fd7;
L_180003fd7:
  T=M.addflags(R.rsp,0x68ull,64); R.rsp=uint64_t(T); goto L_180003fdb;
L_180003fdb:
  R.r15=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fdd;
L_180003fdd:
  R.r14=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fdf;
L_180003fdf:
  R.r13=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe1;
L_180003fe1:
  R.r12=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe3;
L_180003fe3:
  R.rdi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe4;
L_180003fe4:
  R.rsi=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe5;
L_180003fe5:
  R.rbx=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe6;
L_180003fe6:
  R.rbp=uint64_t(M.read64(R.rsp)); R.rsp+=8; goto L_180003fe7;
L_180003fe7:
  return;
L_18000401b:
  R.rbx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_18000401f;
L_18000401f:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.rbx+0x24ull)),32);
  goto L_180004022;
L_180004022:
  if (M.sf==M.of) goto L_18000404c; goto L_180004024;
L_180004024:
  T=(uint32_t(R.r11)) & (uint32_t(R.r11)); M.logicflags(T,32);
  goto L_180004027;
L_180004027:
  if (M.sf) goto L_18000404c; goto L_180004029;
L_180004029:
  T=M.subflags(uint32_t(R.r11),M.read32((R.rbx+0x28ull)),32);
  goto L_18000402d;
L_18000402d:
  if (M.sf==M.of) goto L_18000404c; goto L_18000402f;
L_18000402f:
  R.rax=uint32_t(uint32_t(R.r11)); goto L_180004032;
L_180004032:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rbx+0x20ull))))); goto L_180004036;
L_180004036:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180004039;
L_180004039:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rsi)))); goto L_18000403c;
L_18000403c:
  R.rdx=uint64_t((R.rcx+(R.rax*8ull))); goto L_180004040;
L_180004040:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180004043;
L_180004043:
  T=M.addflags(R.rdx,M.read64((R.rbx+0x18ull)),64); R.rdx=uint64_t(T); goto L_180004047;
L_180004047:
  M.write64((R.r9), R.rdx); goto L_18000404a;
L_18000404a:
  goto L_18000405a;
L_18000404c:
  M.write64((R.r9), R.rbp); goto L_18000404f;
L_18000404f:
  R.rcx=uint32_t(uint32_t(R.r11)); goto L_180004052;
L_180004052:
  R.rax=uint64_t(R.rbp); goto L_180004055;
L_180004055:
  T=(uint32_t(R.r10)) & (uint32_t(R.r10)); M.logicflags(T,32);
  goto L_180004058;
L_180004058:
  if (M.sf) goto L_18000407f; goto L_18000405a;
L_18000405a:
  R.rdx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_18000405e;
L_18000405e:
  R.rax=uint64_t(R.rbp); goto L_180004061;
L_180004061:
  T=M.subflags(uint32_t(R.r10),M.read32((R.rdx+0x24ull)),32);
  goto L_180004065;
L_180004065:
  if (M.sf==M.of) goto L_18000407f; goto L_180004067;
L_180004067:
  T=(uint32_t(R.rcx)) & (uint32_t(R.rcx)); M.logicflags(T,32);
  goto L_180004069;
L_180004069:
  if (M.sf) goto L_18000407f; goto L_18000406b;
L_18000406b:
  T=M.subflags(uint32_t(R.rcx),M.read32((R.rdx+0x28ull)),32);
  goto L_18000406e;
L_18000406e:
  if (M.sf==M.of) goto L_18000407f; goto L_180004070;
L_180004070:
  R.rcx=uint32_t(int64_t(int32_t(uint32_t(R.rcx)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180004074;
L_180004074:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rcx)))); goto L_180004077;
L_180004077:
  R.rax=uint64_t((R.rcx+(R.r10*8ull))); goto L_18000407b;
L_18000407b:
  T=M.addflags(R.rax,M.read64((R.rdx+0x18ull)),64); R.rax=uint64_t(T); goto L_18000407f;
L_18000407f:
  R.rbx=uint32_t((R.r10+0x1ull)); goto L_180004083;
L_180004083:
  M.write64((R.r9+0x8ull), R.rax); goto L_180004087;
L_180004087:
  R.rax=uint64_t(R.rbp); goto L_18000408a;
L_18000408a:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_18000408c;
L_18000408c:
  if (M.sf) goto L_1800040b5; goto L_18000408e;
L_18000408e:
  R.rdx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_180004092;
L_180004092:
  T=M.subflags(uint32_t(R.rbx),M.read32((R.rdx+0x24ull)),32);
  goto L_180004095;
L_180004095:
  if (M.sf==M.of) goto L_1800040b5; goto L_180004097;
L_180004097:
  T=(uint32_t(R.r11)) & (uint32_t(R.r11)); M.logicflags(T,32);
  goto L_18000409a;
L_18000409a:
  if (M.sf) goto L_1800040b5; goto L_18000409c;
L_18000409c:
  T=M.subflags(uint32_t(R.r11),M.read32((R.rdx+0x28ull)),32);
  goto L_1800040a0;
L_1800040a0:
  if (M.sf==M.of) goto L_1800040b5; goto L_1800040a2;
L_1800040a2:
  R.r11=uint32_t(int64_t(int32_t(uint32_t(R.r11)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_1800040a7;
L_1800040a7:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rbx)))); goto L_1800040aa;
L_1800040aa:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.r11)))); goto L_1800040ad;
L_1800040ad:
  R.rax=uint64_t((R.rcx+(R.rax*8ull))); goto L_1800040b1;
L_1800040b1:
  T=M.addflags(R.rax,M.read64((R.rdx+0x18ull)),64); R.rax=uint64_t(T); goto L_1800040b5;
L_1800040b5:
  M.write64((R.r9+0x10ull), R.rax); goto L_1800040b9;
L_1800040b9:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_1800040bb;
L_1800040bb:
  if (M.sf) goto L_1800040ee; goto L_1800040bd;
L_1800040bd:
  R.r11=uint64_t(M.read64((R.rdi+0x18ull))); goto L_1800040c1;
L_1800040c1:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.r11+0x24ull)),32);
  goto L_1800040c5;
L_1800040c5:
  if (M.sf==M.of) goto L_1800040ee; goto L_1800040c7;
L_1800040c7:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_1800040ca;
L_1800040ca:
  if (M.sf) goto L_1800040ee; goto L_1800040cc;
L_1800040cc:
  T=M.subflags(uint32_t(R.r8),M.read32((R.r11+0x28ull)),32);
  goto L_1800040d0;
L_1800040d0:
  if (M.sf==M.of) goto L_1800040ee; goto L_1800040d2;
L_1800040d2:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_1800040d5;
L_1800040d5:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.r11+0x20ull))))); goto L_1800040da;
L_1800040da:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_1800040dd;
L_1800040dd:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rsi)))); goto L_1800040e0;
L_1800040e0:
  R.rdx=uint64_t((R.rcx+(R.rax*8ull))); goto L_1800040e4;
L_1800040e4:
  T=M.addflags(R.rdx,M.read64((R.r11+0x18ull)),64); R.rdx=uint64_t(T); goto L_1800040e8;
L_1800040e8:
  M.write64((R.r9+0x18ull), R.rdx); goto L_1800040ec;
L_1800040ec:
  goto L_1800040fa;
L_1800040ee:
  M.write64((R.r9+0x18ull), R.rbp); goto L_1800040f2;
L_1800040f2:
  R.rax=uint64_t(R.rbp); goto L_1800040f5;
L_1800040f5:
  T=(uint32_t(R.r10)) & (uint32_t(R.r10)); M.logicflags(T,32);
  goto L_1800040f8;
L_1800040f8:
  if (M.sf) goto L_180004124; goto L_1800040fa;
L_1800040fa:
  R.rdx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_1800040fe;
L_1800040fe:
  R.rax=uint64_t(R.rbp); goto L_180004101;
L_180004101:
  T=M.subflags(uint32_t(R.r10),M.read32((R.rdx+0x24ull)),32);
  goto L_180004105;
L_180004105:
  if (M.sf==M.of) goto L_180004124; goto L_180004107;
L_180004107:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_18000410a;
L_18000410a:
  if (M.sf) goto L_180004124; goto L_18000410c;
L_18000410c:
  T=M.subflags(uint32_t(R.r8),M.read32((R.rdx+0x28ull)),32);
  goto L_180004110;
L_180004110:
  if (M.sf==M.of) goto L_180004124; goto L_180004112;
L_180004112:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180004115;
L_180004115:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_180004119;
L_180004119:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_18000411c;
L_18000411c:
  R.rax=uint64_t((R.rcx+(R.r10*8ull))); goto L_180004120;
L_180004120:
  T=M.addflags(R.rax,M.read64((R.rdx+0x18ull)),64); R.rax=uint64_t(T); goto L_180004124;
L_180004124:
  M.write64((R.r9+0x20ull), R.rax); goto L_180004128;
L_180004128:
  R.rax=uint64_t(R.rbp); goto L_18000412b;
L_18000412b:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_18000412d;
L_18000412d:
  if (M.sf) goto L_180004158; goto L_18000412f;
L_18000412f:
  R.rdx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_180004133;
L_180004133:
  T=M.subflags(uint32_t(R.rbx),M.read32((R.rdx+0x24ull)),32);
  goto L_180004136;
L_180004136:
  if (M.sf==M.of) goto L_180004158; goto L_180004138;
L_180004138:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_18000413b;
L_18000413b:
  if (M.sf) goto L_180004158; goto L_18000413d;
L_18000413d:
  T=M.subflags(uint32_t(R.r8),M.read32((R.rdx+0x28ull)),32);
  goto L_180004141;
L_180004141:
  if (M.sf==M.of) goto L_180004158; goto L_180004143;
L_180004143:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_180004146;
L_180004146:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_18000414a;
L_18000414a:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_18000414d;
L_18000414d:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rbx)))); goto L_180004150;
L_180004150:
  R.rax=uint64_t((R.rcx+(R.rax*8ull))); goto L_180004154;
L_180004154:
  T=M.addflags(R.rax,M.read64((R.rdx+0x18ull)),64); R.rax=uint64_t(T); goto L_180004158;
L_180004158:
  T=M.addflags(uint32_t(R.r8),1,32); R.r8=uint32_t(T); goto L_18000415b;
L_18000415b:
  M.write64((R.r9+0x28ull), R.rax); goto L_18000415f;
L_18000415f:
  T=(uint32_t(R.rsi)) & (uint32_t(R.rsi)); M.logicflags(T,32);
  goto L_180004161;
L_180004161:
  if (M.sf) goto L_180004197; goto L_180004163;
L_180004163:
  R.r11=uint64_t(M.read64((R.rdi+0x18ull))); goto L_180004167;
L_180004167:
  T=M.subflags(uint32_t(R.rsi),M.read32((R.r11+0x24ull)),32);
  goto L_18000416b;
L_18000416b:
  if (M.sf==M.of) goto L_180004197; goto L_18000416d;
L_18000416d:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_180004170;
L_180004170:
  if (M.sf) goto L_180004197; goto L_180004172;
L_180004172:
  T=M.subflags(uint32_t(R.r8),M.read32((R.r11+0x28ull)),32);
  goto L_180004176;
L_180004176:
  if (M.sf==M.of) goto L_180004197; goto L_180004178;
L_180004178:
  R.rax=uint32_t(uint32_t(R.r8)); goto L_18000417b;
L_18000417b:
  R.rax=uint32_t(int64_t(int32_t(uint32_t(R.rax)))*int64_t(int32_t(M.read32((R.r11+0x20ull))))); goto L_180004180;
L_180004180:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rax)))); goto L_180004183;
L_180004183:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rsi)))); goto L_180004186;
L_180004186:
  R.rdx=uint64_t((R.rcx+(R.rax*8ull))); goto L_18000418a;
L_18000418a:
  R.rcx=uint32_t(uint32_t(R.r8)); goto L_18000418d;
L_18000418d:
  T=M.addflags(R.rdx,M.read64((R.r11+0x18ull)),64); R.rdx=uint64_t(T); goto L_180004191;
L_180004191:
  M.write64((R.r9+0x30ull), R.rdx); goto L_180004195;
L_180004195:
  goto L_1800041a6;
L_180004197:
  M.write64((R.r9+0x30ull), R.rbp); goto L_18000419b;
L_18000419b:
  R.rcx=uint32_t(uint32_t(R.r8)); goto L_18000419e;
L_18000419e:
  R.rax=uint64_t(R.rbp); goto L_1800041a1;
L_1800041a1:
  T=(uint32_t(R.r10)) & (uint32_t(R.r10)); M.logicflags(T,32);
  goto L_1800041a4;
L_1800041a4:
  if (M.sf) goto L_1800041cb; goto L_1800041a6;
L_1800041a6:
  R.rdx=uint64_t(M.read64((R.rdi+0x18ull))); goto L_1800041aa;
L_1800041aa:
  R.rax=uint64_t(R.rbp); goto L_1800041ad;
L_1800041ad:
  T=M.subflags(uint32_t(R.r10),M.read32((R.rdx+0x24ull)),32);
  goto L_1800041b1;
L_1800041b1:
  if (M.sf==M.of) goto L_1800041cb; goto L_1800041b3;
L_1800041b3:
  T=(uint32_t(R.rcx)) & (uint32_t(R.rcx)); M.logicflags(T,32);
  goto L_1800041b5;
L_1800041b5:
  if (M.sf) goto L_1800041cb; goto L_1800041b7;
L_1800041b7:
  T=M.subflags(uint32_t(R.rcx),M.read32((R.rdx+0x28ull)),32);
  goto L_1800041ba;
L_1800041ba:
  if (M.sf==M.of) goto L_1800041cb; goto L_1800041bc;
L_1800041bc:
  R.rcx=uint32_t(int64_t(int32_t(uint32_t(R.rcx)))*int64_t(int32_t(M.read32((R.rdx+0x20ull))))); goto L_1800041c0;
L_1800041c0:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.rcx)))); goto L_1800041c3;
L_1800041c3:
  R.rax=uint64_t((R.rcx+(R.r10*8ull))); goto L_1800041c7;
L_1800041c7:
  T=M.addflags(R.rax,M.read64((R.rdx+0x18ull)),64); R.rax=uint64_t(T); goto L_1800041cb;
L_1800041cb:
  M.write64((R.r9+0x38ull), R.rax); goto L_1800041cf;
L_1800041cf:
  T=(uint32_t(R.rbx)) & (uint32_t(R.rbx)); M.logicflags(T,32);
  goto L_1800041d1;
L_1800041d1:
  if (M.sf) goto L_180004201; goto L_1800041d3;
L_1800041d3:
  R.r10=uint64_t(M.read64((R.rdi+0x18ull))); goto L_1800041d7;
L_1800041d7:
  T=M.subflags(uint32_t(R.rbx),M.read32((R.r10+0x24ull)),32);
  goto L_1800041db;
L_1800041db:
  if (M.sf==M.of) goto L_180004201; goto L_1800041dd;
L_1800041dd:
  T=(uint32_t(R.r8)) & (uint32_t(R.r8)); M.logicflags(T,32);
  goto L_1800041e0;
L_1800041e0:
  if (M.sf) goto L_180004201; goto L_1800041e2;
L_1800041e2:
  T=M.subflags(uint32_t(R.r8),M.read32((R.r10+0x28ull)),32);
  goto L_1800041e6;
L_1800041e6:
  if (M.sf==M.of) goto L_180004201; goto L_1800041e8;
L_1800041e8:
  R.r8=uint32_t(int64_t(int32_t(uint32_t(R.r8)))*int64_t(int32_t(M.read32((R.r10+0x20ull))))); goto L_1800041ed;
L_1800041ed:
  R.rax=uint64_t(int64_t(int32_t(uint32_t(R.rbx)))); goto L_1800041f0;
L_1800041f0:
  R.rcx=uint64_t(int64_t(int32_t(uint32_t(R.r8)))); goto L_1800041f3;
L_1800041f3:
  R.rdx=uint64_t((R.rcx+(R.rax*8ull))); goto L_1800041f7;
L_1800041f7:
  T=M.addflags(R.rdx,M.read64((R.r10+0x18ull)),64); R.rdx=uint64_t(T); goto L_1800041fb;
L_1800041fb:
  M.write64((R.r9+0x40ull), R.rdx); goto L_1800041ff;
L_1800041ff:
  goto L_180004205;
L_180004201:
  M.write64((R.r9+0x40ull), R.rbp); goto L_180004205;
L_180004205:
  R.rbx=uint64_t(M.read64((R.rsp+0x8ull))); goto L_18000420a;
L_18000420a:
  R.rbp=uint64_t(M.read64((R.rsp+0x10ull))); goto L_18000420f;
L_18000420f:
  R.rsi=uint64_t(M.read64((R.rsp+0x18ull))); goto L_180004214;
L_180004214:
  R.rdi=uint64_t(M.read64((R.rsp+0x20ull))); goto L_180004219;
L_180004219:
  return;
