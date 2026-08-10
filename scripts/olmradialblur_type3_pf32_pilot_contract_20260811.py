"""Contract helpers for the eight-process PF32 Type-3 Windows AE pilot."""
from __future__ import annotations
import hashlib,json,struct,zlib
from pathlib import Path
AEX_SHA256="ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb";AE_VERSION="26.3x87";OUTPUT_TEMPLATE="OLM EXR 32 Float";WIDTH,HEIGHT=9,7
def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def canonical_hash(v:object)->str:return digest(json.dumps(v,sort_keys=True,separators=(",",":")).encode())
def png_rgba(kind:str)->bytes:
 rows=bytearray()
 for y in range(HEIGHT):
  rows.append(0)
  for x in range(WIDTH):
   a=255 if (x+y)%4 else 96;v=((x*31+y*7)&255,(x*11+y*29)&255,(x*47+y*13)&255,a)
   if kind=="inverse":v=(255-v[0],255-v[1],255-v[2],v[3])
   elif kind=="primary":v=((x*19+y*53+17)&255,(x*71+y*5+29)&255,(x*3+y*97+43)&255,224 if (2*x+y)%5 else 80)
   rows.extend(v)
 def ch(n:bytes,p:bytes)->bytes:
  b=n+p;return struct.pack(">I",len(p))+b+struct.pack(">I",zlib.crc32(b))
 return b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",WIDTH,HEIGHT,8,6,0,0,0))+ch(b"IDAT",zlib.compress(bytes(rows),9))+ch(b"IEND",b"")
def cases()->list[dict]:
 fixed={"OLM RadialBlur-0002":[4.5,3.5],"OLM RadialBlur-0004":4,"OLM RadialBlur-0028":1,"OLM RadialBlur-0029":0,"OLM RadialBlur-0008":0,"OLM RadialBlur-0012":1,"OLM RadialBlur-0013":0,"OLM RadialBlur-0015":5,"OLM RadialBlur-0016":1,"OLM RadialBlur-0017":0,"OLM RadialBlur-0019":25,"OLM RadialBlur-0020":3,"OLM RadialBlur-0022":3}
 out=[]
 for mode,blur in (("zoom",1),("rotation",2)):
  for layer in ("pattern","inverse"):
   for repeat in (1,2):
    rid=f"pf32_{mode}_{layer}_r{repeat}";params=dict(fixed);params["OLM RadialBlur-0001"]=blur
    row={"row_id":rid,"case_id":f"pf32_{mode}_{layer}","repeat":repeat,"depth":32,"renderer":"Software","source_member":"inputs/primary_rgba.png","noise_layer_member":f"inputs/{layer}.png","noise_layer_match_name":"OLM RadialBlur-0021","noise_layer_expected_source_name":f"{layer}.png","parameters":params,"comp":{"width":9,"height":7,"pixel_aspect":1,"frame_rate":24,"duration_seconds":1}}
    row["execution_row_sha256"]=canonical_hash(row);out.append(row)
 return out
def contract(files:dict[str,bytes])->dict:
 if len({digest(b) for b in files.values()})!=3:raise ValueError("primary/pattern/inverse fixtures must have distinct hashes")
 return {"schema":"olmradialblur-type3-windows-ae-pilot/1","package_id":"olmradialblur_type3_windows_ae_pilot_20260811","target":{"ae_version":AE_VERSION,"ae_file_version":[26,3,0,87],"renderer":"Software","renderer_raw":1816,"depth":32,"output_template":OUTPUT_TEMPLATE},"plugin":{"member":"aex/OLMRadialBlur.aex","sha256":AEX_SHA256},"fixtures":{n:{"member":f"inputs/{n}.png","sha256":digest(b),"dimensions":[9,7],"alpha":"straight"}for n,b in files.items()},"rows":cases(),"process_contract":{"fresh_afterfx_per_row":True,"expected_rows":8,"all_ae_pids_unique":True},"noise_layer_binding":{"write_then_readback_required":True,"known_risk":"PF layer stream may expose PropertyValueType.NO_VALUE to ExtendScript","fail_closed_code":"NOISE_LAYER_BINDING_UNAVAILABLE","forbidden_fallback":"rendering with PF_LayerDefault_NONE"},"claim_boundary":"PF32, AE 26.3x87 Software, fixed 9x7 fixture, Zoom/Rotation x pattern/inverse Noise Layer x repeat2 only"}
def validate_return(package_root:Path,return_root:Path)->dict:
 req=json.loads((package_root/"BATCH_CONTRACT.json").read_text(encoding="utf-8"));got=[]
 for exp in req["rows"]:
  p=return_root/"outputs"/exp["row_id"]/"attestation.json"
  if not p.is_file():raise ValueError(f"missing attestation: {exp['row_id']}")
  row=json.loads(p.read_text(encoding="utf-8-sig"))
  for k,v in (("row_id",exp["row_id"]),("case_id",exp["case_id"]),("repeat",exp["repeat"]),("execution_row_sha256",exp["execution_row_sha256"]),("ae_version",AE_VERSION),("renderer","Software"),("depth",32),("aex_sha256",AEX_SHA256),("noise_layer_source_name",exp["noise_layer_expected_source_name"])):
   if row.get(k)!=v:raise ValueError(f"{exp['row_id']}: {k} mismatch")
  if row.get("noise_layer_readback")!=row.get("noise_layer_written"):raise ValueError(f"{exp['row_id']}: Noise Layer readback mismatch")
  if row.get("output_template")!=OUTPUT_TEMPLATE or not isinstance(row.get("output_settings"),dict):raise ValueError(f"{exp['row_id']}: output template/settings missing")
  if row.get("parameters_before")!=row.get("parameters_after"):raise ValueError(f"{exp['row_id']}: parameter readback drift")
  observed={x.get("match_name"):x.get("value") for x in row.get("parameters_before",[])}
  if observed!=exp["parameters"]:raise ValueError(f"{exp['row_id']}: parameter values mismatch")
  source_name=Path(exp["source_member"]).stem;noise_name=Path(exp["noise_layer_member"]).stem
  if row.get("source_sha256")!=req["fixtures"][source_name]["sha256"] or row.get("noise_layer_sha256")!=req["fixtures"][noise_name]["sha256"]:raise ValueError(f"{exp['row_id']}: source/layer hash mismatch")
  member=f"outputs/{exp['row_id']}/effect_on.exr"
  if row.get("output_member")!=member:raise ValueError(f"{exp['row_id']}: output member mismatch")
  output=return_root/member
  if not output.is_file() or digest(output.read_bytes())!=row.get("output_sha256"):raise ValueError(f"{exp['row_id']}: EXR missing/hash mismatch")
  got.append(row)
 pids=[r.get("ae_pid") for r in got]
 if any(not isinstance(p,int)or p<=0 for p in pids)or len(set(pids))!=8:raise ValueError("all eight rows must bind unique fresh AE PIDs")
 groups={}
 for r in got:groups.setdefault(r["case_id"],set()).add(r["output_sha256"])
 unstable=[k for k,v in groups.items()if len(v)!=1]
 if unstable:raise ValueError("fresh-process nondeterminism: "+", ".join(unstable))
 return {"status":"exact_return_contract","rows":8,"cases":4}
