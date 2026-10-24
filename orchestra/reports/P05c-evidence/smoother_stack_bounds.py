"""Exhaustively propagate virtual RSP through two literal generated CFGs.

Reject changed/unsupported RSP expressions rather than guessing bounds. Neither
kernel copies RSP to another register or passes its virtual stack to a callee.
Include wrapper-owned return/argument writes in the reported byte interval.
"""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
port=(ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp').read_text()
results=[]
for name,args_end in [('classifier16',0x830),('edgewalker16',0x848)]:
 wrapper_name='Classifier16Exact' if name=='classifier16' else 'EdgeWalker16Exact'
 wrapper=port.rsplit(wrapper_name+'(',1)[1].split('#include',1)[0]
 assert 'R.rsp=SubHandler8Memory::kStack+0x800;' in wrapper
 assert 'M.write64(R.rsp,0xdeadbeefdeadbeefull);' in wrapper
 if name=='classifier16':assert 'M.write64(R.rsp+0x28,dir);' in wrapper
 else:
  assert 'const uint64_t args[]={dir2,(uintptr_t)out_x,(uintptr_t)out_y,uint32_t(threshold)};' in wrapper
  assert 'M.write64(R.rsp+0x28+i*8,args[i]);' in wrapper
 p=ROOT/f'mac/OLMSmoother/Mac/OLMSmoother_{name}.generated.inc';source=p.read_text()
 chunks=re.split(r'^(L_[0-9a-f]+):\n',source,flags=re.M)
 blocks=dict(zip(chunks[1::2],chunks[2::2]));entry=chunks[1]
 memory=re.compile(r'M\.(read|write)(8|16|32|64)\(\(*(R\.rsp(?:\+0x[0-9a-f]+(?:ull)?)?)\)*(?=[,)])')
 arithmetic=re.compile(r'T=M\.(subflags|addflags)\(R\.rsp,0x([0-9a-f]+)ull,64\);\s*R\.rsp=uint64_t\(T\)')
 pushpop=re.compile(r'R\.rsp([+-])=8')
 remaining=memory.sub('MEM',source);remaining=arithmetic.sub('ADJUST',remaining);remaining=pushpop.sub('PUSHPOP',remaining)
 assert 'R.rsp' not in remaining, [l for l in remaining.splitlines() if 'R.rsp' in l]
 pending=[(entry,0x800)];seen={};low=0x800;high=args_end;accesses=0
 while pending:
  label,rsp=pending.pop()
  if label in seen:
   assert seen[label]==rsp,(label,seen[label],rsp)
   continue
  seen[label]=rsp;body=blocks[label];events=[]
  for m in memory.finditer(body):events.append((m.start(),'memory',int(m[2])//8,int(m[3].split('+0x')[1].replace('ull',''),16) if '+0x' in m[3] else 0))
  for m in arithmetic.finditer(body):events.append((m.start(),'adjust',(1 if m[1]=='addflags' else -1)*int(m[2],16),0))
  for m in pushpop.finditer(body):events.append((m.start(),'adjust',8 if m[1]=='+' else -8,0))
  if any(e[1]=='adjust' for e in events):assert 'if' not in body,body
  for _,kind,n,offset in sorted(events):
   if kind=='adjust':rsp+=n
   else:low=min(low,rsp+offset);high=max(high,rsp+offset+n);accesses+=1
  for dest in re.findall(r'goto (L_[0-9a-f]+)',body):
   assert dest in blocks,dest
   pending.append((dest,rsp))
 alias='Classifier16Memory' if name=='classifier16' else 'EdgeWalker16Memory'
 selected=re.search(r'using '+alias+r' = SubHandlerMemory<0x([0-9a-f]+), 0x([0-9a-f]+)>;',port)
 if selected:
  begin,size=(int(v,16) for v in selected.groups());assert begin<=low and high<=begin+size,(name,begin,size,low,high)
 results.append(dict(kernel=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),reachable_blocks=len(seen),stack_access_sites=accesses,begin=hex(low),end_exclusive=hex(high),wrapper_rsp='0x800'))
print(json.dumps(results,indent=2))
