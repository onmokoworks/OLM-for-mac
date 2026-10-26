"""Retain and trace the two additional PF16 odd-even campaign mismatches."""
import argparse,base64,gzip,json,os,subprocess,sys,tempfile,time,zlib,struct
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals';E=R/'orchestra/reports/N03-evidence'
os.environ['TMPDIR']=str(S);sys.path[:0]=[str(E),str(R/'tools/fuzz')]
from adapters.olmdistancegradation import Adapter,SOURCE,FIELDGEN
from core import sha,raw_diff,load_corpus
from geometry import sample
from run import main_checkout
args=argparse.Namespace(max_size=1920,size_sampler='odd-even-v1',size_max_height=1080,case_timeout=120,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker',geometry='realistic')
a=Adapter(args);deadline=time.monotonic()+1200
cases=[load_corpus(E/f'pf16-{index}.json',a)[0] for index in (121,172)];rows=[]
for variant in ('filtered',):
 source=subprocess.check_output(['git','show','41369ff07d1a785849597fe57f9b294cc0b3deb0:mac/OLMDistanceGradation/OLMDistanceGradation.cpp']).decode() if variant=='baseline' else SOURCE.read_text()
 marker='// ============================================================================\n// Per-pixel color combination'
 pos=source.index(marker);end=source.rfind('\n}',0,pos)
 source=source[:end]+'\n if(const char *p=getenv("N03_FIELD")){FILE *f=fopen(p,"wb");fwrite(df.x.data(),4,df.x.size(),f);fclose(f);}\n'+source[end:]
 source=source.replace('if (blurred) df.pre_blur_x = df.x;', 'if (const char *p=getenv("N03_PRE")){FILE *f=fopen(p,"wb");for(float v:df.x){v*=32768.0f;fwrite(&v,4,1,f);}fclose(f);}if (blurred) df.pre_blur_x = df.x;')
 with tempfile.TemporaryDirectory(dir=S) as td:
  hd=Path(td);a.binary,_=a.build(hd,deadline)
  source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
  cpp=hd/'copy.cpp';cpp.write_text(source);host=hd/'host.cpp';host.write_text(host.read_text().replace(str(SOURCE),str(cpp)))
  a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
  for c in cases:
   idx=c['index'];field=hd/'field.raw';trace=hd/'trace.json';a.env.update(N03_FIELD=str(field),N03_PRE=str(hd/"pre.raw"),AEXCOMPAT_SMART_TRACE=str(trace),AEXCOMPAT_SMART_TRACE_WATCH=f"c2f0,{c['geometry'][0]*c['geometry'][1]*4},all")
   status,raw,guards=a.candidate(c,hd,'smart',deadline);oracle,reference=a.oracle(c,hd,deadline,'smart')
   t=json.loads(trace.read_text());mem=[m for m in t['memory_witnesses'] if m['register']=='rcx'];original_field=b''.join(bytes.fromhex(m['before']['hex']) for m in mem)
   native_field=field.read_bytes();native_words=[round(v*32768) for v, in struct.iter_unpack('<f',native_field)];original_words=[x[1] for x in struct.iter_unpack('<4H',original_field)]
   orig=struct.pack('<'+'H'*len(original_words),*original_words);nat=struct.pack('<'+'H'*len(native_words),*native_words)
   row=dict(index=idx,variant=variant,output_diff=raw_diff(reference,raw,16),field_rows=len(mem),pre_diff=raw_diff(original_field,(hd/"pre.raw").read_bytes(),32),unhookable=t['trace_configuration']['unhookable_watches'],dropped=t['dropped_memory_witnesses'])
   rows.append(row)
   with gzip.open(E/f'pf16-{idx}-input-trace.json.gz','wt') as f:json.dump(t,f)
   with gzip.open(E/f'pf16-{idx}-{variant}-field.raw.gz','wb') as f:f.write(native_field)
   print(row,flush=True)
(E/'pf16-input-diagnostic.json').write_text(json.dumps(rows,indent=2)+'\n')
