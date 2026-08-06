#include <cstdio>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
int main(){
 RenderState s{};s.tolerance_lo=6;
 for(int mask=0;mask<512;mask++){
  uint8_t p[9][4];uintptr_t n[9];
  for(int i=0;i<9;i++){p[i][0]=255;p[i][1]=(mask&(1<<i))?255:0;p[i][2]=p[i][3]=0;n[i]=(uintptr_t)p[i];}
  std::printf("%d %d %d %d %d\n",mask,Classifier8(&s,0,0,n,5),Classifier8(&s,0,0,n,3),Classifier8(&s,0,0,n,1),Classifier8(&s,0,0,n,7));
 }
}
