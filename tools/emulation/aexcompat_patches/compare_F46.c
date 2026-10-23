/* Test only: execute the pinned F27c PE oracle, comparing one selected mode. */
#define ORACLE_EMBEDDED
#include "../../ucrt_math_probe/rosetta/oracle.c"
int main(int argc, char **argv) {
 if (argc != 5) return 2;
 int mode=atoi(argv[3]); if(mode!=0 && mode!=1) return 2;
 uint32_t er=load(argv[1]);
 *(uint32_t*)at(0x13bdf4,4)=3;
 ((setter)export_named(er,"_set_FMA3_enable"))(mode);
 if(u32(at(0x13bdf0,4))!=(mode?3:0))die("mode mask");
 void *fn=export_named(er,argv[2]); _mm_setcsr(0x1f80);
 uint64_t count=0,bad=0; uint64_t rows[4096][4], first[4]={0};size_t n;
 while((n=fread(rows,1,sizeof rows,stdin))) {
  if(n%32)die("truncated record");
  for(size_t i=0;i<n/32;i++) {
   double a,b,z; memcpy(&a,&rows[i][0],8);memcpy(&b,&rows[i][1],8);
   z=((double (__attribute__((ms_abi)) *)(double, double))fn)(a,b);
   uint64_t u;memcpy(&u,&z,8);
   if(u!=rows[i][2]) {if(!bad){first[0]=rows[i][0];first[1]=rows[i][1];first[2]=u;first[3]=rows[i][2];}bad++;}
  }count+=n/32;
 }
 if(ferror(stdin)||count!=strtoull(argv[4],0,0))die("wrong stream count");
 printf("{\"function\":\"%s\",\"mode\":%d,\"count\":%llu,\"mismatches\":%llu,\"first_a_b_oracle_worker\":[\"%016llx\",\"%016llx\",\"%016llx\",\"%016llx\"]}\n",argv[2],mode,count,bad,first[0],first[1],first[2],first[3]);
 return bad?1:0;
}
