"""Pair the actual AEX HSV leaf with the current extracted C++ conversion."""
import base64,ctypes,hashlib,json,os,pathlib,struct,subprocess,sys,zlib
R=pathlib.Path(__file__).resolve().parents[3];M=R.parent.parent;E=pathlib.Path(__file__).parent
S=R/'orchestra/state/N02-olmcolorkey-nightly-20261025/hsv';S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),PYTHONDONTWRITEBYTECODE='1');sys.path.insert(0,str(R/'tools/emulation'))
from aex_loader import AexLoader
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
import pefile
A=M/'plugins_2025/OLMColorKey.aex';ld=AexLoader(str(A),verbose=False,fast=True)
# Execute only the original conversion instructions before fmodf; both sides
# return max/min/delta/hue at precisely 0x180009eea, no library substitution.
from unicorn.x86_const import UC_X86_REG_RIP
ld.add_code_hook(0x180009eea,lambda l,a,s:l.uc.emu_stop())
src=(R/'mac/OLMColorKey/OLMColorKey.cpp').read_text();func=src[src.index('static void RGBToPluginHSV('):src.index('static void RGBToPluginYUV(')]
func=func[:func.index('\th = std::fmod')]+ '\tout[0]=mx;out[1]=mn;out[2]=delta;out[3]=h;\n}\n'
cpp='#include <cmath>\n#include <cstdio>\n#include <cstring>\n#include "'+str(R/'core/x86_float.h')+'"\n'+func+'''int main(){unsigned u[3];while(scanf("%x %x %x",u,u+1,u+2)==3){float f[3],o[4];memcpy(f,u,12);RGBToPluginHSV(f,o);unsigned v[4];memcpy(v,o,16);printf("%08x %08x %08x %08x\\n",v[0],v[1],v[2],v[3]);}}\n'''
(S/'leaf.cpp').write_text(cpp);subprocess.run(['clang++','-std=c++17','-O2','-ffp-contract=off',str(S/'leaf.cpp'),'-o',str(S/'leaf')],check=True)
inputs=[]
for path in sorted((R/'orchestra/reports/nightly-20261025/witnesses').glob('*.json')):
 d=json.loads(path.read_text())
 if d['plugin']!='olmcolorkey' or d['case']['depth']!=32:continue
 raw=zlib.decompress(base64.b64decode(d['pixels_zlib_base64']));premul=next(p['value'] for p in d['case']['parameters'] if p['slot']==4)
 for i in range(0,len(raw),16):
  f=struct.unpack('<4f',raw[i:i+16]);rgb=[ctypes.c_float(v*f[0]).value if premul else v for v in f[1:]]
  inputs.append((path.stem+':'+str(i//16),struct.pack('<3f',*rgb)))
# Explicit finite equality/infinity and NaN placements qualify the branch boundary.
for rgb in [(0.,0.,0.),(1.,1.,1.),(float('inf'),)*3,(float('nan'),1.,2.),(1.,float('nan'),2.),(1.,2.,float('nan'))]:inputs.append(('boundary',struct.pack('<3f',*rgb)))
lines=[' '.join(f'{v:08x}' for v in struct.unpack('<3I',raw)) for _,raw in inputs]
native=subprocess.check_output([str(S/'leaf')],input=('\n'.join(lines)+'\n').encode()).decode().splitlines()
rows=[]
for (label,raw),line in zip(inputs,native):
 ptr=ld.host_alloc(12);dst=ld.host_alloc(12);ld.write_bytes(ptr,raw);ld.call_function(0x180009e10,int_args=[ptr,dst],max_instructions=1000)
 assert ld.uc.reg_read(UC_X86_REG_RIP)==0x180009eea
 words=[struct.unpack('<I',struct.pack('<f',ld.read_xmm_f32(n)))[0] for n in (6,0,7,2)]
 # XMM0 is overwritten by reciprocal in green/blue hue branches; capture
 # only mx/delta/hue which retain the same meanings on every branch.
 actual=[int(v,16) for v in line.split()];slots=(0,2,3)
 same=all(words[i]==actual[i] for i in slots)
 rows.append(dict(label=label,input=raw.hex(),aex=[f'{words[i]:08x}' for i in slots],mac=[f'{actual[i]:08x}' for i in slots],same_classification_values=same))
(E/'hsv.json').write_text(json.dumps(dict(aex_sha256=hashlib.sha256(A.read_bytes()).hexdigest(),fields=['max','delta','hue_before_fmod'],comparison='Exact FLOAT32 words',rows=rows),indent=2)+'\n')
pe=pefile.PE(str(A));(E/'hsv-disassembly.txt').write_text('\n'.join(f'{i.address:x}: {i.mnemonic} {i.op_str}'.rstrip() for i in Cs(CS_ARCH_X86,CS_MODE_64).disasm(pe.get_data(0x9e10,0x136),0x180009e10))+'\n')
print('pairs',len(rows),'matches',sum(r['same_classification_values'] for r in rows));assert all(r['same_classification_values'] for r in rows)
for f in ('leaf','leaf.cpp'):(S/f).unlink()
