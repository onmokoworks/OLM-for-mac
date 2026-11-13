"""Retain every failed comparison; independently test original repeatability.
No verdict is changed in the oracle's source campaign. Controls change only Offset,
and are supplementary comparisons, never counted as original-case passes.
"""
import argparse,copy,concurrent.futures,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools/oracle"))
import olm_oracle as o

def diagnose(source,out):
 manifest=json.loads((source/"case.json").read_text())
 route=manifest["route"];depth=o.ROUTES[route][0]
 ids={k:manifest[k] for k in ("reference","candidate","harness","tool")}
 original_ids={**ids,"candidate":ids["reference"]}
 out.mkdir()
 hashes=[];rows=[]
 original_diff=json.loads((source/"diff.json").read_text())
 if original_diff["processes"]["reference"]["ok"]:
  hashes.append(hashlib.sha256(o.load_output(source/"reference.png",depth).tobytes()).hexdigest())
 for repetition in range(3):
  case=copy.deepcopy(manifest["case"]);case["index"]=repetition
  row=o.run_case(out,case,route,original_ids,(),None,120);rows.append(row)
  if o.sha256(out/row["directory"]/"input.png")!=o.sha256(source/"input.png"):
   raise RuntimeError("regenerated input differs from saved witness")
  for side in ("reference","candidate"):
   path=out/row["directory"]/f"{side}.png"
   if row["processes"][side]["ok"]:
    hashes.append(hashlib.sha256(o.load_output(path,depth).tobytes()).hexdigest())
 case=copy.deepcopy(manifest["case"]);case["index"]=3
 for assignment in case["assignments"]:
  if assignment["slot"]==19:assignment["components"]=[0.0]
 control=o.run_case(out,case,route,ids,(),None,120)
 offset=next((a.get("components") for a in manifest["case"]["assignments"] if a["slot"]==19),None)
 original=json.loads((source/"diff.json").read_text())
 result={"source":str(source),"offset":offset,"original_comparison":original,"repeats":rows,"reference_pixel_hashes":hashes,"distinct_reference_outputs":len(set(hashes)),"reference_nondeterminism_proven":len(set(hashes))>1,"zero_offset_control":control}
 o.write_json(out/"summary.json",result);return result

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("campaigns",nargs="+");p.add_argument("--out",required=True);a=p.parse_args();out=Path(a.out).resolve();out.mkdir(exist_ok=False)
 jobs=[]
 for campaign in map(Path,a.campaigns):
  for file in sorted(campaign.glob("case-*/diff.json")):
   row=json.loads(file.read_text())
   if row["status"]!="exact":jobs.append((file.parent.resolve(),out/(campaign.name+"-"+file.parent.name)))
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for result in pool.map(lambda args:diagnose(*args),jobs):
   results.append(result);print(Path(result["source"]).name,"distinct originals",result["distinct_reference_outputs"],"control",result["zero_offset_control"]["status"],flush=True)
 o.write_json(out/"summary.json",results)
