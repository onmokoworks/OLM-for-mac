"""Paired default timing blocks with alternating order and immediate frame disposal.
All requested blocks are retained; no minimum-only or favorable-subset selection.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'rust/tools/bench'))
import bench

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,required=True)
 p.add_argument('--before',type=Path)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--size',default='960x540')
 p.add_argument('--depths',default='8')
 p.add_argument('--blocks',type=int,default=4)
 a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
 assert 2<=a.blocks<=12
 size=tuple(map(int,a.size.split('x')));depths=list(map(int,a.depths.split(',')))
 assert all(d in (8,16,32) for d in depths)
 o=bench.o;o.WindowsJob=bench.AccountingJob
 paths={'original':Path('D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex/OLMDirectionalBlur.aex')}
 if a.before:paths['before']=a.before
 paths['candidate']=a.candidate
 plugins={s:o.identity(p.resolve()) for s,p in paths.items()}
 run=SimpleNamespace(harness=o.DEFAULT_HARNESS,frame_cap=30,batch_cap=190,keep_frames=False)
 image=a.out/'input.png';bench.Image.fromarray(o.input_pixels(*size,20261113)).save(image)
 report={'size':size,'depths':depths,'blocks':a.blocks,'warmup_per_block':1,'measured_per_block':5,
         'plugins':plugins,'harness':o.identity(o.DEFAULT_HARNESS),'clock':'render_selector_ns','priority':'normal','cells':[],'complete':False}
 for depth in depths:
  cell={'depth':depth,'blocks':[]};report['cells'].append(cell)
  for number in range(a.blocks):
   folder=a.out/f'{depth}-{number}';folder.mkdir();request=folder/'request.json';route='smart'+str(depth)
   o.write_json(request,o.make_request({'assignments':[],'size':size,'downsample':'1'},route=route))
   # Reverse each successive pair. Three-side orders also rotate between pairs.
   names=list(plugins);shift=(number//2)%len(names);names=names[shift:]+names[:shift]
   order=names if number%2==0 else names[::-1]
   row={'order':order,'results':{}}
   for side in order:row['results'][side]=bench.run_side(run,folder,side,plugins[side],route,image,request)
   good=all(r['status']=='ok' for r in row['results'].values())
   row['exact']=good and len(set(json.dumps(r['outputs'],sort_keys=True) for r in row['results'].values()))==1
   cell['blocks'].append(row);o.write_json(a.out/'summary.json',report)
   if not row['exact']:raise RuntimeError('incomplete/mismatched block; retained evidence')
  samples={s:[x['render_selector_ns'] for b in cell['blocks'] for x in b['results'][s]['samples_ms']] for s in plugins}
  cell['statistics']={s:{'n':len(v),'median_ms':statistics.median(v),'min_ms':min(v)} for s,v in samples.items()}
  cell['ratio']=cell['statistics']['candidate']['median_ms']/cell['statistics']['original']['median_ms']
  cell['paired_block_ratios']=[b['results']['candidate']['statistics']['render_selector_ns']['median_ms']/b['results']['original']['statistics']['render_selector_ns']['median_ms'] for b in cell['blocks']]
  print(depth,cell['statistics'],'ratio',round(cell['ratio'],4),flush=True)
 report['complete']=True;o.write_json(a.out/'summary.json',report)
 return 0
if __name__=='__main__':raise SystemExit(main())
