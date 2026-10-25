"""Keep compact reports and logs; generated binaries/raw frames remain scratch."""
import gzip,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[3];s=root/'orchestra/state/P07e-radialblur-rotation-parallel';e=root/'orchestra/reports/P07e-evidence'
paths=[s/name for name in ['baseline.sample.txt','profile-summary.json','profile.log','units-before-sdk.log','units-after.log','unit-comparison.json','threads/results.json','threads.log','bundle.log','bundle/bundle-builds.json','summary.json','closeout.json','replay-c46.json','replay-c46.log','concurrent.log','concurrent-summary.json','native.log']]
paths += list((s/'oracle').glob('*.json'))+list((s/'oracle').glob('*.log'))
for label in ['before-matrix','after-matrix']:
 paths += [s/label/'matrix.jsonl',s/label/'matrix-manifest.json',s/(label+'.log')]
paths += list((s/'native/radialblur').glob('*.json'))+list((s/'native/radialblur').glob('*.jsonl'))
for p in paths:
 if p.exists():
  with p.open('rb') as src,gzip.open(e/(str(p.relative_to(s)).replace('/','__')+'.gz'),'wb') as out:shutil.copyfileobj(src,out)
cache=Path.home()/'.cache/olm-emu/P07e-radialblur-rotation-parallel/build.json'
if cache.exists():shutil.copy2(cache,e/'candidate-build.json')
print('Archived',len([p for p in paths if p.exists()]),'files')
