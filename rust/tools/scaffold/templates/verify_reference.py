#!/usr/bin/env python3
"""Invoke the shared oracle with this scaffold's explicit config; render is expected to fail until ported."""
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
    a=p.parse_args();root=Path(__file__).resolve().parent
    c=json.loads((root/"oracle.json").read_text(encoding="utf-8"))
    candidate=a.candidate.resolve() if a.candidate else root/c["candidate"]
    # Cargo outputs may be hardlinked; AEXCompat requires single-link modules.
    local=root/"local";local.mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix="oracle-",dir=local))
    staged=stage/(candidate.stem+".aex");shutil.copy2(candidate,staged);candidate=staged
    cmd=[sys.executable,c["oracle"],a.mode,"--reference",c["reference"],"--candidate",str(candidate),"--harness",c["harness"],"--out",str(a.out.resolve())]
    if a.mode=="render":
        cmd += ["--routes",','.join(c["routes"]),"--jobs",str(c["jobs"]),"--cases",str(c["cases"]),"--seed",str(c["seed"]),"--downsample",c["downsample"]]
    return subprocess.call(cmd)

if __name__=="__main__":raise SystemExit(main())
