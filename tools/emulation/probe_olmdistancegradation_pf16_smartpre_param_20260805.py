#!/usr/bin/env python3
"""Execute AEX Smart pre-render parameter/depth preparation FUN_181174060."""
import hashlib,json,struct,sys
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_RSP
H=Path(__file__).resolve().parent;R=H.parents[1];sys.path.insert(0,str(H))
from aex_loader import AexLoader
A=R/'plugins_2025/DistanceGradation.aex';ENTRY=0x181174060
def main():
 ld=AexLoader(str(A),fast=True);events=[];ind=ld.host_alloc(0x300);ld.write_bytes(ind,b'\0'*0x300);basic=ld.host_alloc(0x10);suite=ld.host_alloc(0x20)
 def checkout(l,args):
  rsp=l.uc.reg_read(UC_X86_REG_RSP);dest=struct.unpack('<Q',l.read_bytes(rsp+0x30,8))[0];l.write_bytes(dest,b'\0'*0xb0);l.write_bytes(dest+0x38,struct.pack('<i',4));events.append({'callback':'checkout','slot':int(args[1]),'dest':hex(dest),'raw':l.read_bytes(dest,0xb0).hex()});return 0
 def checkin(l,args):events.append({'callback':'checkin','param':hex(int(args[1]))});return 0
 def param_suite(l,args):events.append({'callback':'ParamUtils','slot':int(args[1]),'depth_word':struct.unpack('<I',l.read_bytes(int(args[2])+4,4))[0]});return 0
 p=ld.install_callback('DG.smart.checkout',checkout);q=ld.install_callback('DG.smart.checkin',checkin);u=ld.install_callback('DG.smart.ParamUtils',param_suite);ld.write_bytes(ind,struct.pack('<2Q',p,q));ld.write_bytes(suite,struct.pack('<Q',u)+b'\0'*0x18)
 def acquire(l,args):l.write_bytes(int(args[2]),struct.pack('<Q',suite));events.append({'callback':'AcquireSuite'});return 0
 def release(l,args):return 0
 ld.write_bytes(basic,struct.pack('<2Q',ld.install_callback('acquire',acquire),ld.install_callback('release',release)));ld.write_bytes(ind+0x180,struct.pack('<Q',basic));regs=ld.call_function(ENTRY,int_args=[ind,3,1],max_instructions=500000)
 report={'schema':'olmdistancegradation.pf16-smartpre-param-probe/1','status':'exact_entry_return','binary_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'entry':hex(ENTRY),'args':{'param_index':3,'depth_bool':1},'expected_depth_word':32,'events':events,'instructions':int(regs['instructions']),'return_eax':int(regs['rax']&0xffffffff)};assert report['return_eax']==0 and any(e.get('depth_word')==32 for e in events);print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
