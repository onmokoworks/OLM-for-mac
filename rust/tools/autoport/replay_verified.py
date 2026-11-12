"""Replay recorded native inputs against verified generated functions, without Codex."""
import argparse
from pathlib import Path
import time

import autoport as a


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    root=args.run.resolve()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    config=a.read(root/"config.json")
    state=a.read(root/"state.json")
    graph=a.read(root/"graph.json")
    dll=root/"work/target/release"/(config["crate_name"].replace("-","_")+".dll")
    if a.digest(config["aex"]) != state["original_sha256"]:
        raise ValueError("recorded original identity changed")
    results={}
    for address,row in state["functions"].items():
        if row["status"] != "verified":
            continue
        source=root/"work/src/autoport"/f"f_{address}.rs"
        if a.digest(source) != row["source_sha256"]:
            raise ValueError("verified source changed")
        vectors=root/"functions"/address/"vectors.json"
        recorded=a.read(vectors)
        contract=config["contracts"][address]
        evidence=out/address
        evidence.mkdir()
        results[address]=a.verify(contract,recorded,config,address,graph,dll,evidence,time.monotonic()+90)
        results[address]["recorded_inputs"]={"path":str(vectors),"sha256":a.digest(vectors)}
        print(address,results[address]["exact"],len(recorded),flush=True)
    a.write(out/"summary.json",results)
    return 0 if results and all(r["exact"] for r in results.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
