#!/usr/bin/env python3
import hashlib,json,struct,subprocess,sys,tempfile
from collections import Counter,defaultdict
from pathlib import Path
from unicorn import UC_HOOK_CODE
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/emulation'));from aex_loader import AexLoader
AEX=ROOT/'plugins_2025/OLMSmoother.aex';SHA='6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82';SRC=ROOT/'tools/emulation/olmsmoother_v1_classifier8_binary_patterns_production_harness_20260805.cpp';OUT=ROOT/'refs/conformance/olmsmoother_v1_classifier8_binary_families_20260805.json';ENTRY=0x180008060;END=0x18000946e;DIRS=(5,3,1,7)
def blocks(trace):
 if not trace:return []
 result=[trace[0]]
 for a,b in zip(trace,trace[1:]):
  if b!=a+SIZES.get(a,0):result.append(b)
 return result
SIZES={}
def main():
 assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
 with tempfile.TemporaryDirectory() as td:
  exe=Path(td)/'patterns';subprocess.run(['clang++','-std=c++17','-I'+str(ROOT/'cli/OLMSmoother/shim'),str(SRC),'-o',str(exe)],check=True,capture_output=True)
  prod={int(a[0]):list(map(int,a[1:])) for line in subprocess.run([str(exe)],text=True,capture_output=True,check=True).stdout.splitlines() if (a:=line.split())}
 l=AexLoader(str(AEX),verbose=False,fast=True);s=l.host_alloc(64,align=16);l.write_bytes(s,b'\0'*64);l.write_bytes(s+8,struct.pack('<i',6));ps=[l.host_alloc(4,align=4) for _ in range(9)];n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));trace=[]
 def hook(uc,address,size,user):trace.append(address);SIZES[address]=size
 l.uc.hook_add(UC_HOOK_CODE,hook,begin=ENTRY,end=END);mismatches=[]
 for mask in range(512):
  for i,p in enumerate(ps):l.write_bytes(p,bytes((255,255 if mask>>i&1 else 0,0,0)))
  for di,d in enumerate(DIRS):
   trace.clear();actual=l.call_function(ENTRY,[s,0,0,n,d],max_instructions=100000)['rax'];expected=prod[mask][di]
   if actual!=expected:
    bb=blocks(trace);sig=hashlib.sha256(struct.pack('<%dQ'%len(bb),*bb)).hexdigest()[:16]
    mismatches.append({'mask':mask,'direction':d,'actual':actual,'production':expected,'signature':sig,'basic_blocks':[hex(x) for x in bb]})
 groups=defaultdict(list)
 for x in mismatches:groups[x['signature']].append({k:x[k] for k in ('mask','direction','actual','production')})
 report={'schema_version':1,'status':'exact' if not mismatches else 'mismatch_families_captured','actual_aex_sha256':SHA,'total_calls':2048,'mismatch_count':len(mismatches),'family_count':len(groups),'families':[{'signature':sig,'count':len(items),'members':items,'basic_blocks':next(x['basic_blocks'] for x in mismatches if x['signature']==sig)} for sig,items in sorted(groups.items(),key=lambda kv:(-len(kv[1]),kv[0]))]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':report['status'],'total_calls':2048,'mismatch_count':len(mismatches),'family_count':len(groups),'counts':[len(x) for x in groups.values()]},indent=2));assert not mismatches
if __name__=='__main__':main()
