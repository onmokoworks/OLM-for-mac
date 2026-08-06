#include <cstdio>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
int main(){
 uint8_t p[9][4]={{255,0,0,0},{255,0,0,0},{255,0,0,0},{255,0,0,0},{255,0,0,0},{255,255,0,0},{255,255,0,0},{255,255,0,0},{255,255,0,0}};
 uintptr_t n[9];for(int i=0;i<9;i++)n[i]=(uintptr_t)p[i];RenderState s{};s.tolerance_lo=6;
 std::printf("[%d,%d,%d,%d]\n",Classifier8(&s,464,170,n,5),Classifier8(&s,464,170,n,3),Classifier8(&s,464,170,n,1),Classifier8(&s,464,170,n,7));
}
