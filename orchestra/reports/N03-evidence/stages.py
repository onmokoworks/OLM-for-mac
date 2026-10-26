"""Instrument copies of baseline/current production radius-two code, compare live AEX sums."""
import argparse,gzip,json,os,subprocess,sys,tempfile,time,struct
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/N03-distancegradation-bilateral-refusals'
os.environ['TMPDIR']=str(S);sys.path[:0]=[str(R/'tools/fuzz'),str(R/'tools/emulation')]
from adapters.olmdistancegradation import Adapter,SOURCE,FIELDGEN
from core import raw_diff
from run import main_checkout
args=argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=Path.home()/'.cache/olm-emu/worker-F54b/aex-guest-worker')
a=Adapter(args);deadline=time.monotonic()+600;E=R/'orchestra/reports/N03-evidence';rows=[]
for variant in ('baseline','current'):
 source=subprocess.check_output(['git','show','41369ff07d1a785849597fe57f9b294cc0b3deb0:mac/OLMDistanceGradation/OLMDistanceGradation.cpp']).decode() if variant=='baseline' else SOURCE.read_text()
 begin=source.index('static void bilateral_blur_ipp_radius_two(');end=source.index('static bool is_scalar_bilateral_shape',begin);body=source[begin:end]
 body=body.replace('float numerators[3], denominators[3];','float numerators[3], denominators[3];\n\t\tFILE *dump=fopen(getenv("N03_STAGE"),"ab");')
 body=body.replace('\t\t\tdenominators[group]=','\t\t\tfwrite(&spatial[group],4,1,dump);fwrite(weights,4,4,dump);fwrite(products,4,4,dump);\n\t\t\tdenominators[group]=')
 body=body.replace('\t\tmat[(size_t)y*w+x]=','\t\tfwrite(numerators,4,3,dump);fwrite(denominators,4,3,dump);fwrite(&center,4,1,dump);fwrite(&numerator,4,1,dump);fwrite(&denominator,4,1,dump);fclose(dump);\n\t\tmat[(size_t)y*w+x]=')
 source=source[:begin]+body+source[end:]
 with tempfile.TemporaryDirectory(dir=S) as td:
  hd=Path(td);a.binary,_=a.build(hd,deadline)
  source=source.replace('#include "OLMDistanceGradation.h"','#include "'+str(SOURCE.with_suffix('.h'))+'"').replace('"../../core/','"'+str(R/'core')+'/').replace('"../../ucrtmath/','"'+str(R/'ucrtmath')+'/')
  cpp=hd/'candidate.cpp';cpp.write_text(source);host=hd/'host.cpp'
  host.write_text(host.read_text().replace(str(SOURCE),str(cpp)).replace('int main(int argc,char **argv)','int public_main(int argc,char **argv)')+'\nint main(int argc,char **argv){int w=atoi(argv[1]),h=atoi(argv[2]);std::vector<float> f(w*h);fread(f.data(),4,f.size(),stdin);bilateral_blur_ipp_radius_two(f.data(),w,h);fwrite(f.data(),4,f.size(),stdout);}')
  a.compile(['clang++','-std=c++17','-O2','-fno-fast-math','-ffp-contract=off','-I',hd/'geometry-shim',host,FIELDGEN,'-o',a.binary],deadline)
  for name in ('witness','vector'):
   leaf=json.load(gzip.open(E/f'{name}-leaf.json.gz'));dump=hd/'stage.raw';dump.unlink(missing_ok=True)
   output=subprocess.run([str(a.binary),str(leaf['w']),str(leaf['h'])],input=bytes.fromhex(leaf['input_hex']),capture_output=True,env=dict(os.environ,N03_STAGE=str(dump)),check=True).stdout
   stages=dump.read_bytes();assert len(stages)==leaf['w']*leaf['h']*36*4
   with gzip.open(E/f'{name}-{variant}-stages.raw.gz','wb') as f:f.write(stages)
   first=leaf['sums'][0];nr,dr,lanes={'0x1806be0e3':('xmm13','xmm12',1),'0x1806b791d':('xmm10','xmm11',4),'0x1806b7c5a':('xmm11','xmm10',4)}[first['pc']]
   orig_n=bytes.fromhex(first['xmm'][nr])[:4*lanes];orig_d=bytes.fromhex(first['xmm'][dr])[:4*lanes]
   # First dispatched tile starts at output (0,0); first division covers 1/4 pixels.
   native_n=b''.join(stages[i*144+136:i*144+140] for i in range(lanes));native_d=b''.join(stages[i*144+140:i*144+144] for i in range(lanes))
   from collections import Counter
   original_pairs=Counter()
   for sm in leaf['sums']:
    nr2,dr2,lanes2={'0x1806be0e3':('xmm13','xmm12',1),'0x1806b791d':('xmm10','xmm11',4),'0x1806b7c5a':('xmm11','xmm10',4)}[sm['pc']]
    lanes2=sm['valid_lanes'];assert 0<lanes2<=4
    for i in range(lanes2):
     original_pairs[(bytes.fromhex(sm['xmm'][nr2])[i*4:i*4+4].hex(),bytes.fromhex(sm['xmm'][dr2])[i*4:i*4+4].hex())]+=1
   native_pairs=Counter((stages[i*144+136:i*144+140].hex(),stages[i*144+140:i*144+144].hex()) for i in range(leaf['w']*leaf['h']))
   all_sum_checks=dict(original_pixels=original_pairs.total(),mac_pixels=native_pairs.total(),unmatched_original=(original_pairs-native_pairs).total(),unmatched_mac=(native_pairs-original_pairs).total(),comparison='multiset of paired sums; ordered final output compared separately')
   weight_checks=[]
   if name=='vector':
    events={e['pc']:e['xmm'] for e in leaf['events']}
    for g,(pc,reg) in enumerate([(0x1806b77fd,'xmm14'),(0x1806b7905,'xmm0'),(0x1806b7723,'xmm1')]):
     expected=bytes.fromhex(events[hex(pc)][reg])
     actual=b''.join(stages[i*144+g*36:i*144+g*36+4] for i in range(4))
     weight_checks.append(dict(group=g,kind='spatial',pc=hex(pc),diff=raw_diff(expected,actual,32)))
    groups=[[(0x1806b7743,'xmm13'),(0x1806b776c,'xmm0'),(0x1806b77aa,'xmm14'),(0x1806b77e0,'xmm0')],[(0x1806b7841,'xmm6'),(0x1806b786c,'xmm0'),(0x1806b78a7,'xmm13'),(0x1806b78f0,'xmm1')],[(0x1806b7678,'xmm10'),(0x1806b76b7,'xmm3'),(0x1806b769d,'xmm1'),(0x1806b76fa,'xmm11')]]
    if variant=='baseline':groups[0]=[groups[0][i] for i in (2,0,1,3)]
    for g,group in enumerate(groups):
     for tap,(pc,reg) in enumerate(group):
      expected=bytes.fromhex(events[hex(pc)][reg])
      actual=b''.join(stages[i*144+g*36+4+tap*4:i*144+g*36+8+tap*4] for i in range(4))
      weight_checks.append(dict(group=g,tap=tap,pc=hex(pc),diff=raw_diff(expected,actual,32)))
   rows.append(dict(all_sum_checks=all_sum_checks,weight_checks=weight_checks,variant=variant,field=name,output=raw_diff(bytes.fromhex(leaf['output_hex']),output,32),first_numerator=raw_diff(orig_n,native_n,32),first_denominator=raw_diff(orig_d,native_d,32),original_numerator_hex=orig_n.hex(),mac_numerator_hex=native_n.hex(),original_denominator_hex=orig_d.hex(),mac_denominator_hex=native_d.hex()))
(E/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(r['variant'],r['field'],'output',r['output']['different_words'],'numerator',r['first_numerator']['different_words'],'denominator',r['first_denominator']['different_words'])

for row in rows:
 if row['variant']=='current':
  assert row['output']['different_words']==0
  assert row['all_sum_checks']['unmatched_original']==row['all_sum_checks']['unmatched_mac']==0
  assert all(w['diff']['different_words']==0 for w in row['weight_checks'])
