"""Public kit API adapters with all generated files rooted in autoport's run."""
import argparse
import importlib.util
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent.parent


def scaffold(aex, out, name, probe, evidence):
    from button_scaffold import load_scaffold
    s = load_scaffold()
    evidence.mkdir(parents=True,exist_ok=False)
    oracle = s.oracle_module()
    res = s.resources(aex)
    desc = s.descriptor(res)
    inv = oracle.inspect(s.DEFAULT_HARNESS,aex,60)
    s.write_json(evidence/"inventory.json",inv)
    env = {"OLM_SCAFFOLD_ORIGINAL":str(aex),"OLM_SCAFFOLD_ENTRY":desc["entry"],
           "OLM_SCAFFOLD_CAPTURE":str(evidence/"declarations.json")}
    s.run_checked(oracle,[s.DEFAULT_HARNESS,"--headless","--inspect-experimental-with-deps",probe,aex.parent],
                  60,env,evidence/"capture-process.json")
    import json
    cap = json.loads((evidence/"declarations.json").read_text(encoding="utf-8"))
    s.emit(out,name,aex,inv,cap,res,desc,s.DEFAULT_HARNESS)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("aex",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("name")
    p.add_argument("probe",type=Path)
    p.add_argument("evidence",type=Path)
    a = p.parse_args()
    scaffold(a.aex,a.out,a.name,a.probe,a.evidence)
