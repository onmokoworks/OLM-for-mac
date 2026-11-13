"""Bounded 540p one-depth defaults benchmark; deletes frames immediately."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'rust/tools/bench'))
import bench

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--staged',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--depth',type=int,choices=[8,16,32],default=32)
 args=p.parse_args(); args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=False)
 o=bench.o;o.WindowsJob=bench.AccountingJob
 run=SimpleNamespace(harness=o.DEFAULT_HARNESS,frame_cap=30,batch_cap=190,keep_frames=False)
 image=args.out/'input.png';bench.Image.fromarray(o.input_pixels(960,540,20261113)).save(image)
 report={'size':[960,540],'depth':args.depth,'warmup':1,'samples':5,'cells':[]}
 for name in ['OLMBlur','OLMDirectionalBlur','OLMRadialBlur']:
  directory=args.out/name;directory.mkdir()
  plugins={'original':o.identity(Path('D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex')/(name+'.aex')),'rust':o.identity(args.staged/(name+'.aex'))}
  route='smart'+str(args.depth);request=directory/'request.json'
  o.write_json(request,o.make_request({'assignments':[],'size':[960,540],'downsample':'1'},route=route))
  row={'plugin':name,'plugins':plugins}
  for side in ['original','rust']: row[side]=bench.run_side(run,directory,side,plugins[side],route,image,request)
  row['exact']=all(row[s]['status']=='ok' for s in ['original','rust']) and row['original']['outputs']==row['rust']['outputs']
  if row['exact']: row['ratio']=row['rust']['statistics']['render_selector_ns']['median_ms']/row['original']['statistics']['render_selector_ns']['median_ms']
  report['cells'].append(row);o.write_json(args.out/'summary.json',report)
  print(name,row['exact'],row.get('ratio'),flush=True)
 image.unlink()
 return 0 if all(c['exact'] for c in report['cells']) else 1
if __name__=='__main__':raise SystemExit(main())
