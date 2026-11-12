"""Record original calls while a separately identified host-contract bridge launches it.
Does not modify record or original; the derived controller differs in launch module only.
"""
import argparse,hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent

def run(original,bridge,profile,request,out):
    sys.path.insert(0,str(TOOLS/'record'))
    path=TOOLS/'record/record.py';source=path.read_text(encoding='utf-8')
    old="oracle.ROUTES[args.route][1], str(module),"
    if source.count(old)!=1:raise ValueError('record launch anchor changed')
    source=source.replace(old,"oracle.ROUTES[args.route][1], str(args.launch_module),",1)
    m=types.ModuleType('record_bridge');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    args=argparse.Namespace(module=original,launch_module=bridge,profile=profile,request=request,out=out,harness=m.oracle.DEFAULT_HARNESS,route='smart32',width=11,height=7,seed=20261113,max_calls=64,max_bytes=1048576,timeout=60)
    result=m.capture(args)
    (out/'bridge-provenance.json').write_text(json.dumps({'original':str(original),'bridge':str(bridge),'bridge_sha256':hashlib.sha256(bridge.read_bytes()).hexdigest(),'record_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'intervention':'launch bridge; suppress one unmatched param checkin only; original hook target unchanged'},indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raise SystemExit(run(*[getattr(a,k).resolve() for k in ['original','bridge','profile','request','out']]))
