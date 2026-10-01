import json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/directionalblur_sse_conversion_20261001.json'
class ConversionTests(unittest.TestCase):
 def test_instruction_boundary_results_and_extreme_scatter(self):
  report=json.loads(REPORT.read_text());self.assertEqual(report['case_count'],20);self.assertEqual(report['exact_count'],20)
  self.assertEqual(report['instruction_hex'],'f3440f2cc8')
  rows=','.join('{0x'+c['input_f32_bits']+'u,'+str(c['native_i32'])+'}' for c in report['cases'])
  cpp=r'''
#include "core/dblur_rowdriver.cpp"
#include <cstring>
#include <array>
struct Case { std::uint32_t bits; std::int32_t result; };
int main(){
 static_assert(sizeof(int)==sizeof(std::int32_t));
 Case cases[]={__ROWS__};
 for(const auto c:cases){float value;std::memcpy(&value,&c.bits,4);if(trunc_i(value)!=c.result)return 1;}
 std::array<float,9*4> source{},destination{};
 std::array<float,9> denominator{},alpha{},weights{};
 source.fill(.5f);destination.fill(.25f);denominator.fill(.125f);alpha.fill(1);weights.fill(.75f);
 const auto before=destination;const auto before_denominator=denominator;
 for(float coefficient:{1e28f,-1e28f,std::numeric_limits<float>::infinity(),
     -std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}){
  for(char backward:{char(0),char(1)})olm_dblur_scatter_f32(4,0,backward,source.data(),
   destination.data(),denominator.data(),alpha.data(),weights.data(),7,9,coefficient);
 }
 if(destination!=before||denominator!=before_denominator)return 2;
 return 0;
}
'''.replace('__ROWS__',rows)
  env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
  with tempfile.TemporaryDirectory(prefix='dblur_sse_conversion_') as td:
   src=Path(td)/'probe.cpp';src.write_text(cpp)
   for sanitize in (False,True):
    binary=Path(td)/('sanitized' if sanitize else 'o2')
    flags=['-O1','-g','-fsanitize=address,undefined,float-cast-overflow','-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++','-std=c++17',*flags,'-I',str(ROOT),str(src),'-o',str(binary)],check=True,capture_output=True)
    subprocess.run([str(binary)],check=True,capture_output=True,env=env)
if __name__=='__main__':unittest.main()
