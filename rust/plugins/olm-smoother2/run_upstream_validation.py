"""Final new-original campaigns. Artifacts stay local to this crate; jobs <= 2."""
import argparse,json,subprocess,sys
from pathlib import Path
from verify_upstream_leaves import ROOT,WORK,ORIGINAL,save

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prefix',default='final')
    parser.add_argument('--resident',action='store_true')
    args=parser.parse_args()
    candidate=WORK/'OLMSmoother2-final.aex'
    tool=ROOT/'rust/tools/oracle/olm_oracle.py'
    processes=[]
    runs=[(2025,20261114,103,args.resident),(2025,20261115,103,args.resident),
          (2025,20261116,12,False),(2026,20261116,12,False)]
    for year,seed,cases,resident in runs:
        name=f'{args.prefix}-{year}-{seed}'
        reference=ORIGINAL if year==2025 else ORIGINAL.parent.parent/'2026/OLMSmoother2.aex'
        command=[sys.executable,str(tool),'render','--reference',str(reference),'--candidate',str(candidate),
                 '--cases',str(cases),'--seed',str(seed),'--jobs','2','--routes','smart8,smart16,smart32',
                 '--downsample','1,1/2,1/4','--out',str(WORK/name)]
        if resident:command+=['--resident']
        with (WORK/(name+'.log')).open('x',encoding='utf-8') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
            print(name,'PID',child.pid,flush=True)
            code=child.wait()
        processes.append(dict(name=name,pid=child.pid,exit_code=code,argv=command))
        save(WORK/(args.prefix+'-processes.json'),processes)
        print(name,'exit',code,flush=True)
        if code:raise SystemExit(code)

if __name__=='__main__':main()
