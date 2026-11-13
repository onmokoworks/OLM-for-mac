#!/usr/bin/env python3
"""Sequential ten-original generation/build/inventory/PiPL verification in a fresh ignored directory."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import olm_scaffold as s

NAMES = ["ColorKeep", "DistanceGradation", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
         "OLMKiraKira", "OLMRadialBlur", "OLMSmoother", "OLMSmoother2", "OLMToonDilate"]


def verify(args):
    out=args.out.resolve()
    if s.HERE/"local" not in out.parents:
        raise ValueError("--out must be a new directory under scaffold/local (ignored)")
    out.mkdir(parents=True,exist_ok=False)
    oracle=s.oracle_module()
    if args.probe:
        probe=args.probe.resolve(strict=True)
    else:
        (out/"probe").mkdir();probe=s.build_probe(oracle,out/"probe")
    result={"schema_version":1,"harness":oracle.identity(args.harness.resolve()),"probe":oracle.identity(probe),
            "generator_sha256":s.sha((s.HERE/"olm_scaffold.py").read_bytes()),"plugins":[]}
    target=out/"target"
    for name in NAMES:
        folder=out/name;folder.mkdir();crate=folder/"crate"
        reference=args.originals.resolve()/(name+".aex")
        crate_name="scaffold-"+name.lower()
        row={"name":name,"reference":oracle.identity(reference)}
        result["plugins"].append(row)
        try:
            s.run_checked(oracle,[sys.executable,s.HERE/"olm_scaffold.py","new","--aex",reference,
                "--crate-name",crate_name,"--out",crate,"--harness",args.harness.resolve(),"--probe",probe],
                180,log=folder/"generate.json")
            for command in ("build","test"):
                r=s.run_checked(oracle,["cargo",command,"--offline","--release","--manifest-path",crate/"Cargo.toml",
                    "--target-dir",target,"-j","2"],600,log=folder/(command+".json"))
                row[command+"_exit"]=r["returncode"]
            candidate=folder/(name+".aex")
            shutil.copy2(target/"release"/(crate_name.replace('-','_')+".dll"),candidate)
            row["candidate"]=oracle.identity(candidate)
            r=s.run_checked(oracle,[sys.executable,s.ORACLE,"inventory","--reference",reference,"--candidate",candidate,
                "--harness",args.harness.resolve(),"--out",folder/"inventory"],180,log=folder/"inventory-run.json")
            row["inventory_stdout"]=r["stdout"].strip();row["inventory_identical"]=True
            original_resources=s.resources(reference);candidate_resources=s.resources(candidate)
            # Compare full bytes as well as resource name, type and language.
            row["pipl_identical"]=original_resources==candidate_resources
            row["pipl"]=[{k:v for k,v in r.items() if k!='bytes'}|{"size":len(r['bytes']),"sha256":s.sha(r['bytes'])} for r in original_resources]
            if not row["pipl_identical"]:raise ValueError("PiPL resource mismatch")
            # Recapture generated declarations; includes fields the public oracle cannot see.
            cap_path=folder/"candidate-declarations.json"
            desc=s.descriptor(candidate_resources)
            s.run_checked(oracle,[args.harness.resolve(),"--headless","--inspect-experimental-with-deps",probe,candidate.parent],60,
                {"OLM_SCAFFOLD_ORIGINAL":str(candidate),"OLM_SCAFFOLD_ENTRY":desc["entry"],"OLM_SCAFFOLD_CAPTURE":str(cap_path)},
                folder/"candidate-capture-run.json")
            expected=json.loads((crate/"declarations.json").read_text(encoding="utf-8"))
            actual=json.loads(cap_path.read_text(encoding="utf-8"))
            row["declarations_diff"]=oracle.differences(expected,actual)
            if row["declarations_diff"]:raise ValueError("supplemental declaration mismatch")
            row["limitations"]=json.loads((crate/"scaffold.json").read_text(encoding="utf-8"))["limitations"]
            row["params"]=len(expected['params'])
            row["status"]="pass"
        except Exception as e:
            row["status"]="fail";row["error"]=str(e)
        print(name,row["status"],row.get("error",row.get("inventory_stdout","")),flush=True)
        s.write_json(out/"summary.json",result)
    return 0 if all(r["status"]=="pass" for r in result["plugins"]) else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--originals",type=Path,default=Path(r"D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex"))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--harness",type=Path,default=s.DEFAULT_HARNESS)
    p.add_argument("--probe",type=Path)
    return verify(p.parse_args())


if __name__=="__main__":raise SystemExit(main())
