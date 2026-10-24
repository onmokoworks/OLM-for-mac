#!/usr/bin/env python3
"""F52c oracle qualification against F52, exact bytes only. Does not rebuild hosts."""
import atexit, copy, importlib, json, time
from pathlib import Path
from types import SimpleNamespace
from core import sha
from run import main_checkout
ROOT=Path(__file__).resolve().parents[2]; S=ROOT/'orchestra/state/F52c-geometry-hosts-and-campaigns/qualification'
CACHE=Path.home()/'.cache/olm-emu'
def main():
    S.mkdir(parents=True,exist_ok=True); deadline=time.monotonic()+1200; rows=[]
    atexit.register(lambda: (S/'results.json').write_text(json.dumps(rows,indent=2)+'\n'))
    for plugin in ('olmblur','olmcolorkey','olmdirectionalblur','colorkeep','olmdistancegradation','olmkirakira','radialblur','olmtoondilate','olmsmoother2','olmsmoother'):
        a=importlib.import_module('adapters.'+plugin).Adapter(SimpleNamespace(main=main_checkout(),worker=CACHE/'worker-F52c-geom/aex-guest-worker',max_size=16,case_timeout=10))
        a.env.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
        for depth in (8,16,32):
            case=a.generate(1,0);case.update(geometry=[7,5],depth=depth,parameters=a.defaults(7,5),pixels=bytes([0])* (7*5*depth//8*4))
            # Nontrivial byte-safe finite samples, independent of generation.
            import struct
            pixel=bytes([255,70,120,200]) if depth==8 else struct.pack('<4H',32768,9000,15000,27000) if depth==16 else struct.pack('<4f',1,.2,.5,.9)
            case['pixels']=pixel*35
            for route in (('classic',) if plugin=='olmsmoother' else a.routes):
                baseline=copy.copy(a);baseline.worker=CACHE/'worker-F52-geom/aex-guest-worker'
                old,ob=baseline.oracle(case,S,deadline,route);new,nb=a.oracle(case,S,deadline,route)
                rows.append(dict(plugin=plugin,depth=depth,route=route,test='default-F52',old=old,new=new,byte_equal=ob==nb))
                assert old['status']==new['status'], rows[-1]
                if old['status']=='ok':
                    assert new['status']=='ok' and ob==nb, rows[-1]
                    padded=copy.copy(a);padded.session_arguments=lambda c,d:['--rowbytes-pad','3']
                    status,raw=padded.oracle(case,S,deadline,route)
                    rows.append(dict(plugin=plugin,depth=depth,route=route,test='odd-stride',status=status,byte_equal=raw==nb))
                    assert status['status']=='ok' and raw==nb, rows[-1]
        # Check float32-scale then truncate hypothesis for odd radius/strength.
        if plugin in ('olmblur','olmdirectionalblur'):
            case=a.generate(1,0);case.update(geometry=[9,7],depth=8,parameters=a.defaults(9,7))
            case['pixels']=b''.join(bytes([255,(i*31)%256,(i*53)%256,(i*79)%256]) for i in range(63))
            slot=1 if plugin=='olmblur' else 5
            next(p for p in case['parameters'] if p['slot']==slot)['value']=9
            for den in (2,3,4,8):
                ds=copy.deepcopy(case);ds.update(full_geometry=[9*den-1,7*den-1],downsample=[[1,den],[1,den]])
                equiv=copy.deepcopy(case)
                next(p for p in equiv['parameters'] if p['slot']==slot)['value']=9/den if plugin=='olmblur' else 9//den
                left,lb=a.oracle(ds,S,deadline,'smart');right,rb=a.oracle(equiv,S,deadline,'smart')
                rows.append(dict(plugin=plugin,test='scaled-control',den=den,left=left,right=right,byte_equal=lb==rb,sha256=sha(lb)))
                assert left['status']=='ok' and right['status']=='ok' and lb==rb,rows[-1]
    (S/'results.json').write_text(json.dumps(rows,indent=2)+'\n'); print('PASS',len(rows),'checks')
if __name__=='__main__': main()
