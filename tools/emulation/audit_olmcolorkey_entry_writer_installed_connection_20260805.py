#!/usr/bin/env python3
"""Connect actual entry/worker/writer evidence to the installed OLMColorKey code."""
import hashlib,json,subprocess
from pathlib import Path
from olm_installed_identity import verified_binary
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"refs/conformance/olmcolorkey_entry_writer_installed_connection_20260805.json"
def run(args,**kw): return subprocess.run(args,capture_output=True,text=True,check=False,**kw)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def section_hash(binary,arch,section):
 p1=run(["otool","-arch",arch,"-s","__TEXT",section,str(binary)])
 words=[]
 for line in p1.stdout.splitlines():
  fields=line.split()
  if fields and all(c in "0123456789abcdef" for c in fields[0].lower()): words.extend(fields[1:])
 return hashlib.sha256("".join(words).encode()).hexdigest()
def main():
 installed,identity=verified_binary("OLMColorKey")
 source=ROOT/identity["source_bundle"]/"Contents/MacOS/OLMColorKey"; sections={}
 for arch in ("x86_64","arm64"):
  sections[arch]={s:{"accepted_source":section_hash(source,arch,s),"installed":section_hash(installed,arch,s)} for s in ("__text","__const")}
 adapter=run(["python3",str(ROOT/"tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py")],cwd=ROOT); adapter_report=json.loads(adapter.stdout) if adapter.returncode==0 else {}
 actual=[]
 for fmt,callback in (("PF8","PF_Iterate8"),("PF16","PF_Iterate16"),("PF32","PF_IterateFloat")):
  report=json.loads((ROOT/f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text()); case=next(c for c in report["cases"] if c["case"]=="enabled_black_key_edge_blur_2_center"); events=case["execution"]["events"]
  actual.append({"pixel_format":fmt,"entrypoints":case["entrypoints"],"hits":case["execution"]["hits"],"writer_iterate_events":[e for e in events if e["callback"]==callback],"all_acceptance_gates":all(case["acceptance_gates"].values())})
 nm=run(["nm","-an",str(installed)]); sign=run(["codesign","--verify","--deep","--strict",str(Path(identity["installed_bundle"]))]); ae=run(["pgrep","-x","After Effects"]); pids=[int(x) for x in ae.stdout.split() if x.isdigit()]
 gates={"accepted_manifest_source_installed_exact":identity["source_installed_exact"] and source.is_file() and sha(source)==sha(installed),"accepted_source_installed_text_const_exact":all(v["accepted_source"]==v["installed"] for a in sections.values() for v in a.values()),"actual_entry_worker_writer_all_depths":all(a["all_acceptance_gates"] and a["writer_iterate_events"] and all(v==1 for v in a["hits"].values()) for a in actual),"production_effectmain_adapter_passes":adapter_report.get("status")=="pass" and len(adapter_report.get("cases",[]))==50,"installed_effectmain_and_smartrender_symbols":all(s in nm.stdout for s in ("_EffectMain","SmartRender","RenderWorld")),"installed_codesign_valid":sign.returncode==0,"installed_universal":set(run(["lipo","-archs",str(installed)]).stdout.split())=={"x86_64","arm64"}}
 report={"status":"pass" if all(gates.values()) else "fail","closed_boundary":"The accepted identity-manifest source product is byte-exact with the installed Universal bundle; actual center-key all-depth entry/worker/writer evidence and the production EffectMain adapter are connected without relying on historical PNGs.","remaining_boundary":"No current AE-host render or loaded-module mapping claim; this audit does not start, stop, or inspect a loaded plugin module in AE.","installed":{"path":str(Path(identity["installed_bundle"])),"sha256":sha(installed),"observed_ae_pids":pids},"executable_sections":sections,"actual_paths":actual,"gates":gates}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":report["status"],"json":str(OUT)})); return 0 if all(gates.values()) else 1
if __name__=="__main__": raise SystemExit(main())
