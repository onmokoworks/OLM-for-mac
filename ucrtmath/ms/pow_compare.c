/* Test-only dependency on the qualified F27c PE loader, never library code. */
#define ORACLE_EMBEDDED
#include "../../tools/ucrt_math_probe/rosetta/oracle.c"
typedef double (__attribute__((ms_abi)) *pow_binary)(double,double);
int main(int argc,char **argv){
 if(argc!=3 && argc!=4)return 2;
 void *fn[2];uint8_t *images[2];size_t sizes[2];
 for(int m=0;m<2;m++){
  uint32_t er=load(argv[1]);images[m]=base;sizes[m]=size;
  *(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(m);
  if(u32(at(0x13bdf0,4))!=(m?3:0))die("mode mask");
  fn[m]=export_named(er,argv[2]);
 }
 _mm_setcsr(0x1f80);uint64_t count=0,bad[2]={0,0};uint64_t first[2][4]={{0}};
 uint64_t rows[4096][4];size_t n;
 while((n=fread(rows,1,sizeof rows,stdin))){
  if(n%32)die("truncated record");
  n/=32;
  for(size_t i=0;i<n;i++)for(int m=0;m<2;m++){
   double a,b,z;memcpy(&a,&rows[i][0],8);memcpy(&b,&rows[i][1],8);
   base=images[m];size=sizes[m];
   z=((pow_binary)fn[m])(a,b);
   uint64_t u;memcpy(&u,&z,8);
   if(u!=rows[i][2+m]){if(bad[m]<32)fprintf(stderr,"mode %d: %016llx %016llx oracle %016llx native %016llx\n",m,rows[i][0],rows[i][1],u,rows[i][2+m]);if(!bad[m]){first[m][0]=rows[i][0];first[m][1]=rows[i][1];first[m][2]=u;first[m][3]=rows[i][2+m];}bad[m]++;}
  }count+=n;
 }
 if(argc==4 && count!=strtoull(argv[3],0,0))die("wrong stream count");
 printf("{\"function\":\"%s\",\"count\":%llu,\"modes\":[",argv[2],count);
 for(int m=0;m<2;m++)printf("%s{\"mode\":%d,\"mismatches\":%llu,\"first_a_b_oracle_native\":[\"%016llx\",\"%016llx\",\"%016llx\",\"%016llx\"]}",m?",":"",m,bad[m],first[m][0],first[m][1],first[m][2],first[m][3]);
 puts("]}");return ferror(stdin)?2:(bad[0]||bad[1]?1:0);
}
