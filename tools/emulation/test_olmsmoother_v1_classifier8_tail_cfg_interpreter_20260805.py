#!/usr/bin/env python3
"""Execute the recovered Classifier8 tail CFG without Unicorn instruction execution.

Unicorn is used only to establish the architectural state at 0x1800087f0 and
to obtain the authoritative whole-function return.  Every instruction from
that point through RET is evaluated below from the checked-in CFG artifact.
"""
import hashlib, json, re, struct, sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
CFG = ROOT / "refs/conformance/olmsmoother_v1_classifier8_tail_cfg_20260805.json"
ENTRY, TAIL = 0x180008060, 0x1800087F0
DIRS = (5, 3, 1, 7)

BASES = {
    "rax": UC_X86_REG_RAX, "rbx": UC_X86_REG_RBX, "rcx": UC_X86_REG_RCX,
    "rdx": UC_X86_REG_RDX, "rsi": UC_X86_REG_RSI, "rdi": UC_X86_REG_RDI,
    "rbp": UC_X86_REG_RBP, "rsp": UC_X86_REG_RSP, "r8": UC_X86_REG_R8,
    "r9": UC_X86_REG_R9, "r10": UC_X86_REG_R10, "r11": UC_X86_REG_R11,
    "r12": UC_X86_REG_R12, "r13": UC_X86_REG_R13, "r14": UC_X86_REG_R14,
    "r15": UC_X86_REG_R15,
}
ALIASES = {}
for base in BASES:
    if base.startswith("r") and base[1:].isdigit():
        n = base[1:]; ALIASES.update({base:(base,64),base+"d":(base,32),base+"w":(base,16),base+"b":(base,8)})
ALIASES.update({
    "rax":("rax",64),"eax":("rax",32),"ax":("rax",16),"al":("rax",8),
    "rbx":("rbx",64),"ebx":("rbx",32),"bx":("rbx",16),"bl":("rbx",8),
    "rcx":("rcx",64),"ecx":("rcx",32),"cx":("rcx",16),"cl":("rcx",8),
    "rdx":("rdx",64),"edx":("rdx",32),"dx":("rdx",16),"dl":("rdx",8),
    "rsi":("rsi",64),"esi":("rsi",32),"si":("rsi",16),"sil":("rsi",8),
    "rdi":("rdi",64),"edi":("rdi",32),"di":("rdi",16),"dil":("rdi",8),
    "rbp":("rbp",64),"ebp":("rbp",32),"bp":("rbp",16),"bpl":("rbp",8),
    "rsp":("rsp",64),"esp":("rsp",32),"sp":("rsp",16),"spl":("rsp",8),
})

def split_ops(s):
    depth = 0
    for i, c in enumerate(s):
        depth += c == "["; depth -= c == "]"
        if c == "," and depth == 0: return s[:i].strip(), s[i+1:].strip()
    return (s.strip(),)

class Machine:
    def __init__(self, loader, regs, ins):
        self.l, self.r, self.ins = loader, regs.copy(), ins
        self.mem = {}; self.zf = self.sf = self.of = 0; self.trace=[]
        # A nested builtin call uses the loader's synthetic call frame.  Preserve
        # the Classifier8 frame eagerly so its later stack reads remain isolated.
        lo=self.r["rsp"]-0x40
        for i,b in enumerate(self.l.uc.mem_read(lo,0x180)): self.mem[lo+i]=b
    def reg(self, name):
        b,w=ALIASES[name]; return self.r[b] & ((1<<w)-1)
    def setreg(self,name,v):
        b,w=ALIASES[name]; m=(1<<w)-1; v &= m
        if w==64 or w==32: self.r[b]=v
        else: self.r[b]=(self.r[b]&~m)|v
    def addr(self, expr, pc, size):
        e=expr.strip()[1:-1].replace(" ","")
        total=pc+size if e.startswith("rip") else 0
        if e.startswith("rip"): e=e[3:]
        for sign,term in re.findall(r'(^|[+-])([^+-]+)',e):
            mul=1
            if "*" in term: term,m=term.split("*"); mul=int(m,0)
            val=self.reg(term)*mul if term in ALIASES else int(term,0)
            total = total-val if sign=="-" else total+val
        return total & ((1<<64)-1)
    def operand(self, op, pc, size, forced=None):
        op=op.strip()
        mm=re.match(r'(?:(byte|dword|qword) ptr )?(\[.*\])$',op)
        if mm:
            w={"byte":1,"dword":4,"qword":8}[mm.group(1)] if mm.group(1) else forced
            a=self.addr(mm.group(2),pc,size); bs=bytes(self.mem.get(a+i,self.l.uc.mem_read(a+i,1)[0]) for i in range(w))
            return int.from_bytes(bs,"little"),w,a
        if op in ALIASES: return self.reg(op),ALIASES[op][1]//8,None
        return int(op,0),forced,None
    def write(self,op,v,pc,size,forced=None):
        _,w,a=self.operand(op,pc,size,forced)
        if a is None: self.setreg(op,v)
        else:
            for i,b in enumerate(int(v).to_bytes(w,"little",signed=False)): self.mem[a+i]=b
    def flags_sub(self,a,b,w):
        bits=w*8;m=(1<<bits)-1;r=(a-b)&m; self.zf=int(r==0);self.sf=(r>>(bits-1))&1
        self.of=int((((a^b)&(a^r))>>(bits-1))&1); return r
    def run(self, start=TAIL):
        pc=start
        for steps in range(10000):
            i=self.ins[pc]; m=i["mnemonic"]; ops=split_ops(i["operands"]); size=len(bytes.fromhex(i["bytes"])); nxt=pc+size
            self.trace.append(pc)
            if m in ("mov","movzx","movsxd"):
                v,w,_=self.operand(ops[1],pc,size)
                if m=="movsxd": v=v-(1<<(w*8)) if v>>(w*8-1) else v
                self.write(ops[0],v,pc,size); pc=nxt
            elif m=="lea": self.setreg(ops[0],self.addr(ops[1],pc,size));pc=nxt
            elif m in ("sub","cmp"):
                a,w,_=self.operand(ops[0],pc,size);b,_,_=self.operand(ops[1],pc,size,forced=w);r=self.flags_sub(a,b,w)
                if m=="sub": self.write(ops[0],r,pc,size)
                pc=nxt
            elif m in ("xor","test"):
                a,w,_=self.operand(ops[0],pc,size);b,_,_=self.operand(ops[1],pc,size,forced=w);r=(a^b) if m=="xor" else (a&b)
                self.zf=int(r==0);self.sf=(r>>(w*8-1))&1;self.of=0
                if m=="xor":self.write(ops[0],r,pc,size)
                pc=nxt
            elif m=="cdq": self.setreg("edx",0xffffffff if self.reg("eax")&0x80000000 else 0);pc=nxt
            elif m in ("je","jne","jg","jle","jmp"):
                take=m=="jmp" or (m=="je" and self.zf) or (m=="jne" and not self.zf) or (m=="jg" and not self.zf and self.sf==self.of) or (m=="jle" and (self.zf or self.sf!=self.of))
                pc=int(ops[0],0) if take else nxt
            elif m=="call":
                assert int(ops[0],0)==0x180002430
                p,q=self.reg("rcx"),self.reg("rdx")
                # Use the actual sole builtin, while keeping all CFG instruction
                # execution outside Unicorn.  Preserve the interpreter register file.
                rv=self.l.call_function(0x180002430,[p,q],max_instructions=10000)["rax"]
                self.setreg("eax",rv);pc=nxt
            elif m=="add":
                a,w,_=self.operand(ops[0],pc,size);b,_,_=self.operand(ops[1],pc,size,forced=w);self.write(ops[0],a+b,pc,size);pc=nxt
            elif m=="pop":
                sp=self.reg("rsp");v=int.from_bytes(self.l.uc.mem_read(sp,8),"little");self.setreg(ops[0],v);self.setreg("rsp",sp+8);pc=nxt
            elif m=="ret": return self.reg("eax"),steps+1
            else: raise AssertionError((hex(pc),m,ops))
        raise AssertionError("CFG did not return")

def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest()==SHA
    cfg=json.loads(CFG.read_text());ins={int(i["address"],0):i for b in cfg["blocks"] for i in b["instructions"]}
    assert len(ins)==1001 and cfg["block_count"]==195 and len(cfg["edges"])==340
    l=AexLoader(str(AEX),verbose=False,fast=True);s=l.host_alloc(64,align=16);l.write_bytes(s,b'\0'*64);l.write_bytes(s+8,struct.pack('<i',6))
    ps=[l.host_alloc(4,align=4) for _ in range(9)];n=l.host_alloc(72,align=16);l.write_bytes(n,struct.pack('<9Q',*ps));mismatch=[]
    for mask in range(512):
        for j,p in enumerate(ps):l.write_bytes(p,bytes((255,255 if mask>>j&1 else 0,0,0)))
        for d in DIRS:
            snap={}
            def hook(uc,address,size,user):
                if address==TAIL:
                    snap.update({k:uc.reg_read(v) for k,v in BASES.items()});uc.emu_stop()
            h=l.uc.hook_add(UC_HOOK_CODE,hook,begin=ENTRY,end=0x18000946e)
            prefix_result=l.call_function(ENTRY,[s,0,0,n,d],max_instructions=100000)["rax"];l.uc.hook_del(h)
            # A fresh whole-function call is authoritative and also restores the
            # loader's normal call frame after the deliberate tail stop.
            atr=[]
            ha=l.uc.hook_add(UC_HOOK_CODE,lambda uc,a,z,u: atr.append(a) if a>=TAIL else None,begin=ENTRY,end=0x18000946e)
            actual=l.call_function(ENTRY,[s,0,0,n,d],max_instructions=100000)["rax"];l.uc.hook_del(ha)
            machine=Machine(l,snap,ins) if snap else None
            if snap: got,steps=machine.run()
            else: got,steps=prefix_result,0
            if got!=actual:
                div=None
                for k,(a,b) in enumerate(zip(atr,machine.trace if machine else [])):
                    if a!=b:div=(k,hex(a),hex(b));break
                if div:
                    k=div[0];div=div+( [hex(x) for x in atr[max(0,k-4):k+2]], [hex(x) for x in machine.trace[max(0,k-4):k+2]] )
                mismatch.append((mask,d,actual,got,steps,div))
    print(json.dumps({'status':'pass' if not mismatch else 'fail','calls':2048,'mismatch_count':len(mismatch),'first_mismatches':mismatch[:10]},indent=2))
    assert not mismatch
if __name__=='__main__':main()
