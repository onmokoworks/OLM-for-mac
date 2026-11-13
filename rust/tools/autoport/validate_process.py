"""Real timeout test: the exact owned child and its descendant must both exit."""
import argparse
import json
from pathlib import Path
import sys

from process import run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    root=args.out.resolve()
    root.mkdir(parents=True,exist_ok=False)
    script=root/"child.py"
    script.write_text('''import json, os, subprocess, sys, time
from pathlib import Path
p = subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"], creationflags=0x08000000)
Path(sys.argv[1]).write_text(json.dumps({"child":os.getpid(),"descendant":p.pid}))
time.sleep(30)
''',encoding="utf-8")
    record=run([sys.executable,script,root/"pids.json"],root/"command",1.5)
    import psutil
    pids=json.loads((root/"pids.json").read_text())
    alive={k:psutil.pid_exists(pid) for k,pid in pids.items()}
    result={"process":record,"pids":pids,"alive":alive}
    (root/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    assert record["timeout"] and record["cleanup_verified"] and not any(alive.values()),result
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
