"""Run the unchanged public oracle check with its Cargo target inside autoport."""
import argparse
from pathlib import Path
import sys

import autoport as a
from process import run


def check(work,original,name,out,full=True):
    out.mkdir(parents=True,exist_ok=False)
    driver=out/'driver.py'
    driver.write_text('import sys\nfrom pathlib import Path\n'+
        f'sys.path.insert(0,{str(a.TOOLS/"oracle")!r})\nimport olm_oracle, oracle_workflows\n'+
        f'oracle_workflows.HERE=Path({str(out/"owned")!r})\nraise SystemExit(olm_oracle.main())\n',encoding='utf-8')
    cmd=[sys.executable,driver,'check',name,'--rust-root',work,'--reference',original,
         '--out',out/'oracle','--jobs','2','--timeout','30','--build-timeout','120']
    if full:cmd.append('--full')
    return run(cmd,out/'process',240)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('work',type=Path);p.add_argument('--original',type=Path,required=True)
    p.add_argument('--name',required=True);p.add_argument('--out',type=Path,required=True)
    x=p.parse_args()
    result=check(x.work.resolve(),x.original.resolve(),x.name,x.out.resolve())
    print(result)
    raise SystemExit(result['returncode'])
