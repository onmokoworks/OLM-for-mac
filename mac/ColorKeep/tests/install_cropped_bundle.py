"""Register the ColorKeep-only candidate built by build_F47_bundles.py."""
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[3]
S=ROOT/'orchestra/state/P04d-colorkeep-cropped-checkout/bundle-build'
CACHE=Path.home()/'.cache/olm-emu'
OUT=CACHE/'P04d-colorkeep-bundle'
OUT.mkdir(exist_ok=True)
shutil.copytree(S/'xcode/ColorKeep/products/ColorKeep.plugin',OUT/'ColorKeep.plugin',dirs_exist_ok=True)
executable=OUT/'ColorKeep.plugin/Contents/MacOS/ColorKeep'
record=dict(name=OUT.name,bundle_path=str(OUT/'ColorKeep.plugin'),candidate_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'mac/ColorKeep/ColorKeep.cpp').read_bytes()).hexdigest(),builds=json.loads((S/'bundle-builds.json').read_text()))
(OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n')
with (CACHE/'.index.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    path=CACHE/'INDEX.json';data=json.loads(path.read_text())
    data['links']=[x for x in data['links'] if x['name']!=record['name']]+[record]
    staged=CACHE/'INDEX.P04d.json';staged.write_text(json.dumps(data,indent=2)+'\n');staged.replace(path)
print(record['candidate_sha256'])
