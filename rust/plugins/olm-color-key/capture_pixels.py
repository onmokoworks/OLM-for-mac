"""Use record's debugger on sparse fixtures, then replay captured pixels with witness.

No shared tool is modified. This only changes the recorder's harness command
from experimental-request (blocked at 1,024 slots) to render-fixture.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode=True
from verify_update import ROOT,HERE,ORIGINALS,sha,oracle
sys.path.insert(0,str(ROOT/'rust/tools/record'))
import record
from win_debug import Debugger
from contract import witness_spec,checked_blob,write_json
import pefile

def capture(fixture,out,depth,candidate):
    module=ORIGINALS['2025'];rva={8:0x2360,16:0x2f30,32:0x3b30}[depth];size=depth//8*4
    profile={'schema_version':1,'module_sha256':sha(module),'functions':[
        {'name':'pixel','rva':hex(rva),'args':['ptr','i32','i32','ptr','ptr'],'return':'u64','max_calls':4,
         'buffers':[{'arg':0,'size':0x2784,'role':'input'},{'arg':3,'size':size,'role':'input'},{'arg':4,'size':size,'role':'output'}]}]}
    cap=record.Capture(module,profile,out,4,1024*1024)
    debug=Debugger(module,profile['functions'],cap.entry,cap.returned,cap.loaded)
    command=[str(oracle.DEFAULT_HARNESS),'--headless','--render-fixture',str(module),str(fixture),str(out/'render')]
    job=record.witness.WindowsJob();process=None;cleanup=False;started=time.monotonic();failure=None
    try:
        with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
            process=subprocess.Popen(command,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,
                creationflags=0x1|0x4|0x08000000,env={**os.environ,**oracle.frame_deadline_environment(60)})
            debug.retain_wait_handle(process);write_json(out/'launch.json',{'pid':process.pid,'command':command})
            job.attach_resume(process)
            while process.pid not in debug.exits:
                if time.monotonic()-started>60:raise TimeoutError('capture timeout')
                debug.poll()
    except BaseException as error:
        failure=repr(error)
        raise
    finally:
        try:
            job.terminate()
            if process and process.pid not in debug.exits:process.kill()
            debug.drain(process.pid if process else None)
        finally:
            cleanup=job.close()
            if process:process.wait(timeout=10)
            write_json(out/'manifest.json',{'module_sha256':sha(module),'harness_sha256':sha(oracle.DEFAULT_HARNESS),
                'profile':profile,'fixture_sha256':sha(fixture),'command':command,'error':failure,
                'cleanup_verified':cleanup,'processes':debug.exits,'calls':len(cap.records),'counts':cap.counts})
    if process.returncode or not cap.records or any(r['status']!='complete' for r in cap.records):
        raise RuntimeError('incomplete capture')
    with pefile.PE(str(candidate)) as pe:
        address=next(s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name==f'olm_ck_witness{depth}'.encode())
    results=[]
    for n,rec in enumerate(cap.records):
        spec,regions=witness_spec(rec,out)
        folder=out/f'replay-{n}';folder.mkdir()
        for label,path,rva in [('original',module,int(rec['rva'],0)),('rust',candidate,address)]:
            current=copy.deepcopy(spec);current['module']=str(path);current['calls'][0]['rva']=hex(rva)
            m=record.witness.run(current,folder/label,timeout=30)
            if m['classification']!='success':raise RuntimeError(m)
        b=rec['buffers'][2];addr=int(b['address'],0);region=next(k for k,(s,e) in enumerate(regions) if s<=addr<e);offset=addr-regions[region][0]
        expected=checked_blob(out,b,'after');buffers=[]
        for label in ['original','rust']:
            call=json.loads((folder/label/'result.json').read_text(encoding='utf-8'))['calls'][0]
            data=(folder/label/call['buffers'][f'b{region}']).read_bytes()[offset:offset+size]
            buffers.append(data)
        results.append({'call':n,'exact':expected==buffers[0]==buffers[1],'recorded':expected.hex(),'native':buffers[0].hex(),'rust':buffers[1].hex()})
    write_json(out/'replay-summary.json',results)
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--candidate',type=Path,default=HERE/'validation/witness-candidate.aex')
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    results={}
    for depth in [8,16,32]:
        out=a.out/str(depth);out.mkdir()
        results[str(depth)]=capture((a.fixtures/f'0002-{depth}/fixture.json').resolve(),out,depth,a.candidate.resolve())
    write_json(a.out/'summary.json',results);print({d:sum(r['exact'] for r in rows) for d,rows in results.items()})
    sys.exit(0 if all(r['exact'] for rows in results.values() for r in rows) else 1)
