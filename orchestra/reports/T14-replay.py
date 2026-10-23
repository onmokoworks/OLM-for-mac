#!/usr/bin/env python3
"""Read-only original-worker / cached I03 bundle replay; evidence only."""
import importlib,json,os,sys,tarfile,time,struct
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from core import load_corpus,command,sha,raw_diff
S=ROOT/'orchestra/state/T14-classic-route-triage'
S.mkdir(parents=True,exist_ok=True)
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1')
MAIN=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
W=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker'
H=Path.home()/'.cache/olm-emu/worker-F51-x86host/plugin-host'
B=Path.home()/'.cache/olm-emu/I03-bundles-545f06bd924497e5/bundles'
plugins={'olmcolorkey':'OLMColorKey','olmdirectionalblur':'OLMDirectionalBlur','olmdistancegradation':'OLMDistanceGradation'}
report={'worker_sha256':sha(W.read_bytes()),'mac_host_sha256':sha(H.read_bytes()),'cases':[]}
with tarfile.open(ROOT/'orchestra/reports/I03-evidence.tar.gz') as archive:
 for plugin,name in plugins.items():
  a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=MAIN,worker=W,max_size=256,case_timeout=60))
  selected={}
  for member in archive.getmembers():
   if member.name.startswith('witnesses/'+plugin+'/') and member.name.endswith('.json'):
    d=json.load(archive.extractfile(member));depth=d['case']['depth']
    if depth not in selected and d['result']['routes']['classic']['status']=='mismatch': selected[depth]=(member,d)
  for depth,(member,d) in sorted(selected.items()):
   directory=S/plugin/str(depth);directory.mkdir(parents=True,exist_ok=True)
   witness=directory/'witness.json';witness.write_text(json.dumps(d,indent=2)+'\n')
   case,_=load_corpus(witness,a)
   exe=B/'xcode'/name/'products'/(name+'.plugin')/'Contents/MacOS'/name
   config=directory/'params.txt';config.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
   types=[0]+[p['param_type'] for p in a.binding['parameters']]
   decl=directory/'declarations.txt';decl.write_text(' '.join(map(str,[len(types),*types])))
   row={'plugin':plugin,'witness':member.name,'depth':depth,'geometry':case['geometry'],'index':case['index'],'input_sha256':sha(case['pixels']),'aex_sha256':sha(a.aex.read_bytes()),'bundle_sha256':sha(exe.read_bytes()),'saved':d['result'],'routes':{}}
   outputs={}
   for route in ('classic','smart'):
    status,raw=a.oracle(case,directory,time.monotonic()+65,route)
    (directory/('aex-'+route+'.raw')).write_bytes(raw)
    argv=['/usr/bin/arch','-arm64',H,exe,*case['geometry'],depth,case['input_padding'],int(route=='smart'),decl,config]
    proc,out,err=command(argv,data=case['pixels'],timeout=60,deadline=time.monotonic()+65,env=dict(a.env,TMPDIR=str(S),TMP=str(S),TEMP=str(S)))
    (directory/('mac-'+route+'.log')).write_bytes(err)
    mac=out[4:];error=struct.unpack('<i',out[:4])[0] if len(out)>=4 else None
    (directory/('mac-'+route+'.raw')).write_bytes(mac)
    row['routes'][route]={'oracle':status,'oracle_sha256':sha(raw),'oracle_nonzero_bytes':sum(v!=0 for v in raw),'mac_process':proc,'mac_error':error,'mac_sha256':sha(mac),'equal':raw==mac if error==0 and status['status']=='ok' else None,'diff':raw_diff(raw,mac,depth) if error==0 and status['status']=='ok' and len(raw)==len(mac) and raw!=mac else None,'saved_oracle_hash_equal':sha(raw)==d['result']['oracles'][route]['raw_sha256'],'saved_mac_hash_equal':sha(mac)==d['result']['routes'][route].get('raw_sha256')}
    outputs[route]=(raw,mac)
   row['mac_classic_equals_smart']=outputs['classic'][1]==outputs['smart'][1]
   report['cases'].append(row)
   print(plugin,depth,case['index'],[(r,v['equal'],v['oracle_nonzero_bytes'],v['mac_error']) for r,v in row['routes'].items()],flush=True)
assert len(report['cases'])==9
assert all(x['routes']['classic']['saved_oracle_hash_equal'] and x['routes']['classic']['saved_mac_hash_equal'] and x['routes']['classic']['equal'] is False for x in report['cases'])
(S/'replay.json').write_text(json.dumps(report,indent=2)+'\n')
