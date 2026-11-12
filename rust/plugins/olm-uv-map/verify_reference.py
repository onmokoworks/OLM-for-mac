#!/usr/bin/env python3
"""Invoke the shared oracle with the UV Map reference and explicit layer sizes."""
import argparse
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["inventory","render"])
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--cases", type=int)
    p.add_argument("--seed", type=int)
    p.add_argument("--jobs", type=int)
    p.add_argument("--sizes", default="1x1,3x7,11x7,31x19,97x61")
    p.add_argument("--layer-sizes", default="17x9,1x1,2x1,1x5,33x17,8x16")
    a=p.parse_args();root=Path(__file__).resolve().parent
    c=json.loads((root/"oracle.json").read_text(encoding="utf-8"))
    candidate=a.candidate.resolve() if a.candidate else root/c["candidate"]
    # Cargo outputs may be hardlinked; AEXCompat requires single-link modules.
    local=root/"local";local.mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix="oracle-",dir=local))
    staged=stage/(candidate.stem+".aex");shutil.copy2(candidate,staged);candidate=staged
    cmd=[sys.executable,c["oracle"],a.mode,"--reference",c["reference"],"--candidate",str(candidate),"--harness",c["harness"],"--out",str(a.out.resolve())]
    if a.mode=="render":
        cmd += ["--routes",','.join(c["routes"]),"--jobs",str(a.jobs if a.jobs is not None else c["jobs"]),"--cases",str(a.cases if a.cases is not None else c["cases"]),"--seed",str(a.seed if a.seed is not None else c["seed"]),"--downsample",c["downsample"],"--layer-sizes",a.layer_sizes,"--sizes",a.sizes]
    return subprocess.call(cmd)

if __name__=="__main__":raise SystemExit(main())
