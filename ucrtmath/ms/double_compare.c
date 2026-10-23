#define ORACLE_EMBEDDED
#include "../../tools/ucrt_math_probe/rosetta/oracle.c"
typedef double (__attribute__((ms_abi)) *double_unary)(double);
int main(int argc,char **argv){
 if(argc!=4)return 2;
 if(strcmp(argv[2],"sin")&&strcmp(argv[2],"cos")&&strcmp(argv[2],"exp"))return 2;
 void *fn[2];uint8_t *images[2];size_t sizes[2];
 for(int m=0;m<2;m++){
  uint32_t er=load(argv[1]);images[m]=base;sizes[m]=size;
  *(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(m);
  if(u32(at(0x13bdf0,4))!=(m?3:0))die("mode mask");
  fn[m]=export_named(er,argv[2]);
 }
 _mm_setcsr(0x1f80);uint64_t count=0,bad[2]={0},first[2][3]={{0}},rows[4096][3];size_t n;
 while((n=fread(rows,1,sizeof rows,stdin))){
  if(n%24)die("truncated record");n/=24;
  for(size_t i=0;i<n;i++)for(int m=0;m<2;m++){
   double a,z;memcpy(&a,&rows[i][0],8);base=images[m];size=sizes[m];z=((double_unary)fn[m])(a);
   uint64_t u;memcpy(&u,&z,8);
   if(u!=rows[i][1+m]){
    if(bad[m]<8)fprintf(stderr,"mode %d input %016llx oracle %016llx native %016llx\n",m,rows[i][0],u,rows[i][1+m]);
    if(!bad[m]){first[m][0]=rows[i][0];first[m][1]=u;first[m][2]=rows[i][1+m];}bad[m]++;
   }
  }count+=n;
 }
 if(count!=strtoull(argv[3],0,0))die("wrong stream count");
 printf("{\"function\":\"%s\",\"count\":%llu,\"modes\":[",argv[2],count);
 for(int m=0;m<2;m++)printf("%s{\"mode\":%d,\"mismatches\":%llu,\"first_input_oracle_native\":[\"%016llx\",\"%016llx\",\"%016llx\"]}",m?",":"",m,bad[m],first[m][0],first[m][1],first[m][2]);
 puts("]}");return ferror(stdin)?2:(bad[0]||bad[1]?1:0);
}
