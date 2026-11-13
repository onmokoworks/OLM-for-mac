"""Summarize retained measurements, token usage and cleanup without rerunning models."""
import argparse
from collections import Counter
import json
from pathlib import Path

import autoport as a


def summarize(root):
    state=a.read(root/"state.json")
    graph=a.read(root/"graph.json")
    config=a.read(root/"config.json")
    functions=[]
    usage=Counter()
    tools=[]
    for address,row in state["functions"].items():
        if not row["attempts"]:
            continue
        functions.append({"address":address,"status":row["status"],"attempts":len(row["attempts"]),
                          "seconds":round(row["seconds"],3),"vectors":row.get("vectors",0)})
        for attempt in row["attempts"]:
            log=root/"functions"/address/f"attempt-{attempt['number']:02d}"/"codex/stdout.txt"
            if not log.exists():
                continue
            for line in log.read_text(encoding="utf-8").splitlines():
                try:
                    event=json.loads(line)
                except ValueError:
                    continue
                usage.update(event.get("usage",{}))
                kind=event.get("item",{}).get("type")
                if kind in {"command_execution","file_change","mcp_tool_call","web_search"}:
                    tools.append({"log":str(log),"type":kind})
    # Exact scope: manifests inside this one run only, never the repository or
    # global sessions. Includes nested native workers, Cargo and oracle processes.
    processes=[]
    for path in root.rglob("*process.json"):
        data=a.read(path)
        processes.append({"file":str(path.relative_to(root)),"pid":data.get("pid"),
                          "returncode":data.get("returncode"),"cleanup":data.get("cleanup_verified",data.get("cleanup"))})
    result={"program":config["program"],"original_sha256":state["original_sha256"],
            "graph_nodes":len(graph["nodes"]),"internal_nodes":sum(not n.get("external") for n in graph["nodes"].values()),
            "frontier":len(graph["frontier"]),"statuses":dict(Counter(r["status"] for r in state["functions"].values())),
            "functions":functions,"usage":dict(usage),"generator_tool_events":tools,
            "budget":{k:config[k] for k in ["max_functions","attempts","generation_seconds","attempt_seconds","function_seconds"]},
            "model":config.get("model","installed CLI default; not pinned"),"effort":config["effort"],
            "oracle":state.get("oracle"),"process_records":processes,
            "graph_sha256":a.digest(root/"graph.json"),"state_sha256":a.digest(root/"state.json")}
    if (root/"oracle/summary.json").exists():
        oracle=a.read(root/"oracle/summary.json")
        result["oracle_verdict"]=oracle.get("verdict")
        result["inventory_identical"]=not oracle.get("inventory_diff",["missing"])
        result["routes"]=oracle.get("render_summary",{}).get("routes")
    return result


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("run",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=summarize(args.run.resolve())
    a.write(args.out,report)
    print(json.dumps({k:v for k,v in report.items() if k not in {"process_records","routes"}},indent=2))
