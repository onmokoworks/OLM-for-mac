from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
s=(root/'src/generated.rs').read_text().replace('unsafe fn Classifier16Exact(', 'unsafe fn Classifier16Slow(')
output=['// Acyclic classifier CFGs, structured by tools/structure.py.\n// Same operations and branch order as generated.rs; no runtime dispatch.\nuse super::{support::*, hot::*, kernels::{ColorBlend8,ColorBlend16,AlphaBlend8,AlphaBlend16,EdgeWalker8Exact,EdgeWalker16Exact,InterpExecutor8,InterpExecutor16}};\n']
names=['Classifier8Tail','Classifier16Slow','DispatchDirection16','DispatchDirection8','SubHandler16Exact','SubHandler8Exact','MainInterpKernel16','MainInterpKernel8','AltHandler16','AltHandler8']
for name in names:
 start=s.index('pub(super) unsafe fn '+name+'(');end=s.find('\npub(super) unsafe fn ',start+1);end=len(s) if end<0 else end
 f=s[start:end]; m=re.search(r'let mut pc: u32=(\d+);\nloop \{match pc \{\n',f);entry=int(m[1]);body=f[m.end():]
 states={int(n):b for n,b in re.findall(r'^(\d+) => \{ (.*?) \},$',body,re.M|re.S)}
 # Regex above consumes through next state only when at line end; body itself has multiline initializers.
 edges={}; kinds={}
 for n,b in states.items():
  pos=b.rfind('if ')
  match=re.fullmatch(r'if (.*?) \{pc=(\d+);\} else \{pc=(\d+);\} continue;',b[pos:],re.S) if pos>=0 else None
  if match:
   kinds[n]=('if',b[:pos],match[1],int(match[2]),int(match[3]));edges[n]=[int(match[2]),int(match[3])]
  else:
   q=re.search(r'pc=(\d+);\s*continue;$',b)
   if q: kinds[n]=('goto',b[:q.start()],int(q[1]));edges[n]=[int(q[1])]
   else:
    assert 'pc=' not in b,(name,n,b[-200:])
    kinds[n]=('end',b);edges[n]=[-1]
 # A self-edge is a natural single-block loop. Preserve its full body and
 # branch ordering, then remove only that back edge from the forward graph.
 for n,k in list(kinds.items()):
  if n in edges[n]:
   assert k[0]=='if' and (k[3]==n)!=(k[4]==n)
   condition=k[2] if k[3]==n else '!('+k[2]+')'
   target=k[4] if k[3]==n else k[3]
   kinds[n]=('goto','loop {\n'+k[1]+'\nif '+condition+' { continue; } else { break; }\n}',target)
   edges[n]=[target]
 seen=set();active=set()
 def visit(n):
  if n==-1 or n in seen:return
  assert n not in active,('cycle',name,n)
  active.add(n)
  for q in edges[n]:visit(q)
  active.remove(n);seen.add(n)
 visit(entry)
 print(name,'states',len(states),'reachable',len(seen),'acyclic')


 # Reverse DFS postorder is a topological ordering. All edges go forward, so
 # lexical block exits express them without a dispatcher or code duplication.
 order=[];done=set()
 def topo(n):
  if n==-1 or n in done:return
  done.add(n)
  for q in edges[n]:topo(q)
  order.append(n)
 topo(entry);order.reverse()
 positions={n:i for i,n in enumerate(order)}
 assert all(q==-1 or positions[n]<positions[q] for n in order for q in edges[n])
 result=["'b%d: {"%n for n in reversed(order[1:])]
 for index,n in enumerate(order):
  if index: result.append('}')
  k=kinds[n];result.append(k[1])
  if k[0]=='goto':result.append("break 'b%d;"%k[2])
  elif k[0]=='if':result.append("if %s { break 'b%d; } else { break 'b%d; }"%(k[2],k[3],k[4]))
 text=f[:m.start()]+'\n'.join(result)+'\n}\n'
 output.append(text)
 print(name,'structured bytes',len(text),flush=True)
(root/'src/structured.rs').write_text('\n'.join(output))

# Unmodified retained loops and blending helpers use the structured entry points.
excluded=set(names)|{'ColorCompare8','ColorCompare16','NeighborExtract8','NeighborExtract16','ScanlinePixel8_Main','ScanlinePixel16_Main','Classifier8'}
parts=re.split(r'(?=pub\(super\) unsafe fn )',s)
kept=[f for f in parts[1:] if re.match(r'pub\(super\) unsafe fn (\w+)',f)[1] not in excluded]
(root/'src/kernels.rs').write_text('// Retained contour loops and blending helpers.\nuse super::{support::*,hot::*};\npub(super) use super::structured::*;\n'+''.join(kept))
