"""Bitwise old/new helper comparison, including exceptional float words."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance/helper'
S.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S))
BASE='00b91897d2fee8ba1b100af4f83dff6adeacbad2'
for file in ('olmblur_helper.h','olmblur_helper.cpp'):
 text=subprocess.check_output(['git','show',BASE+':core/'+file],cwd=ROOT,text=True)
 text=text.replace('namespace olm::blur {','namespace baseline {\nnamespace x86_float = olm::x86_float;')
 if file.endswith('.h'):text='#include "x86_float.h"\n'+text
 (S/file).write_text(text)
source=r'''
#include "olmblur_helper.h"
#include "CANDIDATE_HEADER"
#include <vector>
#include <cstring>
#include <cstdio>
#include <cfenv>
#include "olmblur_parallel_parts.h"
int main() {
 const unsigned special[]={0,0x80000000,0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7f800001,0xff812345,0x7fc12345,0x00000001,0x80000001,0x7f7fffff,0xff7fffff,0x3f800000};
 unsigned state=17;auto next=[&](){state^=state<<13;state^=state>>17;state^=state<<5;return state;};
 size_t words=0;
 for(int rounding: {FE_TONEAREST,FE_UPWARD,FE_DOWNWARD,FE_TOWARDZERO}) {
 std::fesetround(rounding);
 for(int iteration=0;iteration<400;++iteration) {
 size_t w=1+next()%33,h=1+next()%31,r=next()%40;
 std::vector<float> src(w*h*3),old(src.size()),now(src.size()),weights(r+1);
 std::vector<unsigned char> flags(w*h);
 for(auto& f:src) {unsigned b=iteration%2?next():special[next()%14];std::memcpy(&f,&b,4);}
 for(auto& f:weights) {unsigned b=iteration%3?special[next()%14]:next();std::memcpy(&f,&b,4);}
 for(auto& f:flags)f=next()%5!=0;
 for(int vertical=0;vertical<2;++vertical) {
 baseline::HelperParams a{w,h,vertical?w:h,0,r};
 olm::blur::HelperParams b{w,h,vertical?w:h,0,r};
 (vertical?baseline::vertical:baseline::horizontal)(flags.data(),src.data(),old.data(),weights.data(),a);
 (vertical?olm::blur::vertical:olm::blur::horizontal)(flags.data(),src.data(),now.data(),weights.data(),b);
 for(size_t i=0;i<src.size();++i)if(std::memcmp(&old[i],&now[i],4)) {
 unsigned x,y;std::memcpy(&x,&old[i],4);std::memcpy(&y,&now[i],4);
 std::printf("mismatch rounding=%d iteration=%d vertical=%d word=%zu old=%08x new=%08x\n",rounding,iteration,vertical,i,x,y);return 1;
 }
 words+=src.size();
 }
 }
 }
 for(int rounding: {FE_TONEAREST,FE_UPWARD,FE_DOWNWARD,FE_TOWARDZERO}) {
 std::fesetround(rounding);
 const size_t w=257,h=259,r=4;
 std::vector<float> src(w*h*3),old(src.size()),now(src.size()),weights(r+1);
 std::vector<unsigned char> flags(w*h,1);
 for(auto& f:src) {unsigned b=special[next()%14];std::memcpy(&f,&b,4);}
 for(auto& f:weights) {unsigned b=special[next()%14];std::memcpy(&f,&b,4);}
 for(int vertical=0;vertical<2;++vertical) {
 const size_t total=vertical?w:h;
 baseline::HelperParams a{w,h,total,0,r};
 (vertical?baseline::vertical:baseline::horizontal)(flags.data(),src.data(),old.data(),weights.data(),a);
 olm::blur::for_parts(w,h,[&](size_t part){
  olm::blur::HelperParams b{w,h,part==5?total-(total/6)*5:total/6,(total/6)*part,r};
  (vertical?olm::blur::vertical:olm::blur::horizontal)(flags.data(),src.data(),now.data(),weights.data(),b);
 });
 if(std::memcmp(old.data(),now.data(),old.size()*4)) {
  std::printf("parallel mismatch rounding=%d vertical=%d\n",rounding,vertical);return 1;
 }
 words+=src.size();
 }
 }
 std::printf("exact words=%zu, 3200 scalar + 8 parallel comparisons, four rounding modes\n",words);
}
'''.replace('CANDIDATE_HEADER',str(ROOT/'core/olmblur_helper.h'))
(S/'compare.cpp').write_text(source)
candidate=ROOT/'core/olmblur_helper.cpp'
if '--rejected-volatile-removal' in sys.argv:
 text=candidate.read_text().replace('volatile float','float').replace('#include "olmblur_helper.h"','#include "'+str(ROOT/'core/olmblur_helper.h')+'"')
 candidate=S/'rejected.cpp';candidate.write_text(text)
cmd=['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I'+str(ROOT/'core'),str(S/'compare.cpp'),str(S/'olmblur_helper.cpp'),str(candidate),'-o',str(S/'compare')]
subprocess.run(cmd,env=env,check=True)
subprocess.run([str(S/'compare')],env=env,check=True)
