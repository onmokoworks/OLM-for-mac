#!/usr/bin/env python3
"""Read-only retained-fixture audit; generated binaries live in ticket scratch."""
import argparse, json, os, struct, sys, time, subprocess
sys.dont_write_bytecode = True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter
from run import default_worker, main_checkout
from core import sha
S=ROOT/'orchestra/state/F34-dg-fixture-f02-regression'
def comparison(a,b):
    assert len(a)==len(b)==2992
    diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    first=None
    if diffs:
        i=diffs[0]; j=i//4*4
        first=dict(offset=i,pixel=i//16,xy=[i//16%17,i//16//17],channel='ARGB'[i//4%4],byte_values=[a[i],b[i]],words=[f'0x{struct.unpack_from("<I",v,j)[0]:08x}' for v in (a,b)],float_values=[struct.unpack_from('<f',v,j)[0] for v in (a,b)])
    return dict(byte_mismatches=len(diffs),first=first)
def main():
    S.mkdir(parents=True,exist_ok=True)
    os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),PYTHONDONTWRITEBYTECODE='1')
    deadline=time.monotonic()+300
    a=Adapter(argparse.Namespace(max_size=256,case_timeout=30,main=main_checkout(),worker=default_worker()))
    build=S/'build';build.mkdir(exist_ok=True)
    report={'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'provenance':a.prepare(build,deadline),'rows':[]}
    workers={'default':default_worker(),'F30':Path('/Users/onmk/.cache/olm-emu/worker-F30-ucrtmath/aex-guest-worker')}
    try:
        for suffix in ('','_controlled_source'):
            f=ROOT/f'refs/fixtures/olmdistancegradation_pf32_owner_17x11{suffix}_20260805'
            expected=(f/'output_argb_f32.bin').read_bytes();src=(f/'source_argb_f32.bin').read_bytes()
            params=a.defaults(17,11)
            vals={1:1,2:1,3:4,4:4,5:1,6:1,7:[255,28,0,238],8:[255,255,0,0],9:2,10:1,11:1,12:0}
            for p in params:p['value']=vals[p['slot']]
            case=dict(geometry=[17,11],depth=32,parameters=params,pixels=src,input_padding=0,output_padding=0)
            wd=S/('controlled' if suffix else 'zero');wd.mkdir(exist_ok=True)
            prov=ROOT/f'refs/conformance/olmdistancegradation_pf32_owner_probe{suffix}_20260805.json'
            old=json.loads(prov.read_text())
            assert old['output_world']['sha256']==sha(expected)
            row={'retained_provenance':{'path':str(prov.relative_to(ROOT)),'sha256':sha(prov.read_bytes()),'aex_sha256':old['binary_sha256'],'entry':old['entry'],'checkout_values':[{k:e[k] for k in ('slot','value')} for e in old['events'] if e.get('callback')=='checkout_param'],'suites':sorted({e['suite'] for e in old['events'] if 'suite' in e})},'fixture':str(f.relative_to(ROOT)),'source_sha256':sha(src),'expected_sha256':sha(expected),'parameters':params,'mac':{},'aex':{}}
            mac={}
            for route in ('classic','smart'):
                status,raw,_=a.candidate(case,wd,route,deadline);assert status['status']=='ok',status
                mac[route]=raw; (wd/f'mac-{route}.raw').write_bytes(raw)
                row['mac'][route]={'status':status,'sha256':sha(raw),'vs_expected':comparison(raw,expected)}
            for name,worker in workers.items():
                a.worker=worker
                for route in ('classic','smart'):
                    status,raw=a.oracle(case,wd,deadline,route=route);assert status['status']=='ok',status
                    (wd/f'{name}-{route}.raw').write_bytes(raw)
                    row['aex'][name+'-'+route]={'worker_path':str(worker),'worker_sha256':sha(worker.read_bytes()),'status':status,'sha256':sha(raw),'vs_expected':comparison(raw,expected),'vs_mac_classic':comparison(raw,mac['classic']),'vs_mac_smart':comparison(raw,mac['smart'])}
            assert row['aex']['default-smart']['vs_mac_smart']['byte_mismatches']==0
            assert row['aex']['F30-smart']['vs_mac_smart']['byte_mismatches']==0
            for route in ('classic','smart'):
                assert row['aex']['default-'+route]['sha256']==row['aex']['F30-'+route]['sha256']
            report['rows'].append(row)
        path=S/'comparison.json';path.write_text(json.dumps(report,indent=2)+'\n')
        for row in report['rows']:
            print(row['fixture'])
            for name,r in row['aex'].items():print(name,'expected',r['vs_expected'],'mac classic',r['vs_mac_classic'])
    finally:
        (build/'mac').unlink(missing_ok=True)
if __name__=='__main__':main()
