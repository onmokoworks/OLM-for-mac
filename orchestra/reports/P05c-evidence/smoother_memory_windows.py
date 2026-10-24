"""Exhaustive byte-offset/width and native-pointer fallback checks under sanitizers."""
import ast,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];S=ROOT/'orchestra/state/P05c-blur-colorkey-smoother-performance/smooth-window-test';S.mkdir(parents=True,exist_ok=True)
tree=ast.parse((ROOT/'tests/test_olmsmoother_v1_synthetic_stack.py').read_text())
h=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HARNESS' for t in n.targets))
h=h[:h.index('int main() {')]
h=h.replace('template<class T, class M, class Read, class Write>','static size_t checks = 0;\ntemplate<class T, class M, class Read, class Write>')
h=h.replace('assert(read(M::kStack + offset) == value);','assert(read(M::kStack + offset) == value); ++checks;').replace('M::kStack','M::kStorage')
h='#include <cstdio>\n'+h+r'''
template<class M> void window() {
 M m;
 common(m);
 accesses<uint16_t>(m,[&](auto a){return m.read16(a);},[&](auto a,auto v){m.write16(a,v);});
 for(size_t offset=0;offset<sizeof(m.stack);++offset)
  assert(m.ptr(M::kStorage+offset)==m.stack+offset);
 uint8_t native=0;assert(m.ptr((uintptr_t)&native)==&native);
}
int main() {
 window<Classifier16Memory>();window<EdgeWalker16Memory>();
 std::printf("%zu byte-offset/width checks exact; guards and native fallback pass\n",checks);
}
'''
source=S/'probe.cpp';source.write_text(h);binary=S/'probe'
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
cmd=[str(ROOT/'tools/ucrt_cxx.py'),'-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g','-I',str(ROOT),'-I',str(ROOT/'cli/OLMSmoother/shim'),str(source),'-o',str(binary)]
with (S/'build.log').open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([str(binary)],env=env,check=True)
