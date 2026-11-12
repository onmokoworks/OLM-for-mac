import sys,json,copy,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools/oracle"))
import olm_oracle as o
parser=argparse.ArgumentParser();parser.add_argument("case");parser.add_argument("out");args=parser.parse_args()
src=Path(args.case).resolve();out=Path(args.out).resolve();out.mkdir(exist_ok=False)
m=json.loads((src/"case.json").read_text());rows=[]
for i in range(4):
 case=copy.deepcopy(m["case"]);case["index"]=i
 ids={k:m[k] for k in ("harness","reference","candidate","tool")}
 if i<3:ids["candidate"]=ids["reference"]
 else:
  for a in case["assignments"]:
   if a["slot"]==19:a["components"]=[0.0]
 row=o.run_case(out,case,m["route"],ids,(),None,120);rows.append(row);print(row["status"],row.get("comparison",{}))
o.write_json(out/"summary.json",rows)
