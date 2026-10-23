#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse,hashlib,importlib.util,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SOURCE=ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp"
PROBE=ROOT/"tools/emulation/probe_olmradialblur_type1_edge_noise_source_guard_20260813.cpp"
FRAME=ROOT/"tools/emulation/test_olmradialblur_offcenter_brightness_actual_aex_20260811.py"
REPORT=ROOT/"refs/conformance/olmradialblur_type1_edge_noise_source_guard_20260813.json"; DOC=REPORT.with_suffix(".md")
SOURCE_SHA="b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
RUN_SHA="352d37c7c33c62172a07fd0b6180e44b4c5d9d694ebee96b6b04db1d4af32fbe"
EXPECTED={"PF8":"85143eda82a237f32b5c9b1d3cf5f73a121bffa9eaba6e05d4728bda4216f000","PF16":"c9d92745cba73fde78d7ad5868d643ad7a88b1dd481e6caacfc7c945ae153b3c","PF32":"4a7af04987dad9d83589e8609698abaff3f3d89547143c8ad44255bbc62c73f7"}
BOUNDARY={"proven":"24 fixed Rotation Type1 edge/noise cells retain pre-guard output and nine source mutations reject on each architecture","not_proven":["Type2 numerical equality","arbitrary source","native AE","installed candidate","remaining Type1 families"]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load():
 s=importlib.util.spec_from_file_location("edge_frame",FRAME);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def identities():
 m=load();out={}
 for d in (8,16,32):
  pb={8:4,16:8,32:16}[d];rb=32*pb+{8:8,16:16,32:16}[d];raw=m.frame_for(d,"rotation",32,18,rb)()
  out[f"PF{d}"]=hashlib.sha256(b"".join(raw[y*rb:y*rb+32*pb] for y in range(18))).hexdigest()
 return out
def run(arch):
 with tempfile.TemporaryDirectory(prefix=f"radial-edge-{arch}.") as raw:
  exe=Path(raw)/"probe";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
  cmd=[_UCRT_CXX,"-std=c++17","-arch",arch,"-O2","-fno-fast-math","-ffp-contract=off","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations","-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),"-I",str(ROOT/"core"),"-I",str(ROOT/"mac/OLMRadialBlur"),str(PROBE),str(ROOT/"mac/OLMRadialBlur/OLMRadialBlur_Strings.cpp"),str(ROOT/"Util/AEGP_SuiteHandler.cpp"),str(ROOT/"Util/MissingSuiteError.cpp"),"-framework","Cocoa","-o",str(exe)]
  b=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
  if b.returncode:raise RuntimeError(b.stdout+b.stderr)
  r=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 if hashlib.sha256(r.stdout.encode()).hexdigest()!=RUN_SHA:raise RuntimeError("transcript drift")
 lines=r.stdout.splitlines()
 if len(lines)!=33 or sum(x.startswith("POS ") for x in lines)!=24 or sum(x.startswith("NEG ") for x in lines)!=9:raise RuntimeError("row drift")
 return lines
def generate():
 if sha(SOURCE)!=SOURCE_SHA or identities()!=EXPECTED:raise RuntimeError("source drift")
 text=SOURCE.read_text()
 if "MatchesRadial32x18PlainOrComponentFixture<PixelT>(input, false)" not in text:raise RuntimeError("guard missing")
 return {"schema":"olmradialblur.type1-edge-noise-source-guard/1","status":"pass_hostless","authorities":{"production_sha256":sha(SOURCE),"probe_sha256":sha(PROBE),"frame_generator_sha256":sha(FRAME)},"active_source_sha256":EXPECTED,"runs":[{"arch":a,"lines":run(a),"transcript_sha256":RUN_SHA} for a in ("arm64","x86_64")],"positive_cells_per_arch":24,"mutation_rejects_per_arch":9,"claim_boundary":BOUNDARY,"promotion_state":"hostless_closed_universal_rebuild_and_install_pending"}
def validate(v):
 if set(v)!={"schema","status","authorities","active_source_sha256","runs","positive_cells_per_arch","mutation_rejects_per_arch","claim_boundary","promotion_state"}:raise RuntimeError("schema")
 if v["schema"]!="olmradialblur.type1-edge-noise-source-guard/1" or v["status"]!="pass_hostless" or v["authorities"]!={"production_sha256":sha(SOURCE),"probe_sha256":sha(PROBE),"frame_generator_sha256":sha(FRAME)} or v["active_source_sha256"]!=EXPECTED or v["claim_boundary"]!=BOUNDARY:raise RuntimeError("identity")
 if v["positive_cells_per_arch"]!=24 or v["mutation_rejects_per_arch"]!=9 or v["promotion_state"]!="hostless_closed_universal_rebuild_and_install_pending":raise RuntimeError("count")
 if [x.get("arch") for x in v["runs"]]!=["arm64","x86_64"]:raise RuntimeError("arch")
 for r in v["runs"]:
  if set(r)!={"arch","lines","transcript_sha256"} or r["transcript_sha256"]!=RUN_SHA or hashlib.sha256(("\n".join(r["lines"])+"\n").encode()).hexdigest()!=RUN_SHA:raise RuntimeError("run")
def doc(v):return "# RadialBlur Type1 edge/noise source guard\n\n24 fixed PF8/PF16/PF32 Type1 rows remain exact on both architectures; nine source mutations per slice fail closed. Install and AE are pending.\n"
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args();fresh=generate()
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");DOC.write_text(doc(fresh))
 else:
  saved=json.loads(REPORT.read_text());validate(saved)
  if saved!=fresh or DOC.read_text()!=doc(saved):raise RuntimeError("persisted drift")
 print("PASS_OLMRADIALBLUR_TYPE1_EDGE_NOISE_SOURCE_GUARD")
if __name__=="__main__":main()
