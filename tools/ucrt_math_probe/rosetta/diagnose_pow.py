#!/usr/bin/env python3
"""Read-only structural comparison of log tables and retained pow witnesses.
This is diagnostic arithmetic, not an AMD patch or replacement oracle.
"""
import argparse,collections,csv,json,math,pathlib,re,struct
import pefile
p=argparse.ArgumentParser();p.add_argument('--state',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
pe=pefile.PE(str(pathlib.Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'))
def table(r,n):return list(struct.unpack('<'+'d'*n,pe.get_data(r,8*n)))
log=table(0x10fae0,257);inv=table(0x10f0d0,257);exp=table(0x111000,64)
s=(a.state/'aocl/src/optimized/log_tables.c').read_text();checks={}
for name,values in [('log_256',log),('log_f_inv_256',inv)]:
 words=[int(x,16) for x in re.findall(r'0x[0-9a-fA-F]+',re.search(name+r'\[\]\s*=\s*\{(.*?)\}',s,re.S)[1])]
 own=[struct.unpack('<Q',struct.pack('<d',x))[0] for x in values]
 checks[name]=dict(amd_entries=len(words),ucrt_entries=len(own),equal_used_entries=words[:len(own)]==own,extra_amd_entries=[hex(x) for x in words[len(own):]])
rows=[r for r in csv.DictReader((a.state/'full/powf/first.csv').open()) if r['pair']=='ucrt0/amd-off'];assert len(rows)<2000,'incomplete witness list'
def f(h):return struct.unpack('<f',bytes.fromhex(h)[::-1])[0]
def bits(x):return f'{struct.unpack("<I",struct.pack("<f",x))[0]:08x}'
def cls(h):
 n=int(h,16)&0x7fffffff
 return 'nan' if n>0x7f800000 else 'inf' if n==0x7f800000 else 'zero' if not n else 'subnormal' if n<0x800000 else 'normal'
# Reconstruct only the table-log / exp path, in the SSE evaluation order.
# Compare rounded vs truncated index while keeping the same DLL tables.
def model(x,y,round_index):
 m,e=math.frexp(x);e-=1
 raw=struct.unpack('<Q',struct.pack('<d',m))[0]&((1<<52)-1)
 j=(raw>>44)+(((raw>>43)&1) if round_index else 0)
 r=((0.5+j/512)-m)*inv[j]
 q=r+r*r*(0.5+r*(1/3))
 logx=(e*float.fromhex('0x1.62e42fefa39efp-1')+log[j])-q
 t=y*logx;n=round(t*float.fromhex('0x1.71547652b82fep+6'))
 r=t-n*float.fromhex('0x1.62e42fefa39efp-7')
 poly=r+r*r*(0.5+r*(1/6))
 return bits(math.ldexp(exp[n&63]+exp[n&63]*poly,n>>6)),j
counts=collections.Counter();examples={};model_counts=collections.Counter()
for row in rows:
 kind=cls(row['left'])+'/'+cls(row['right']);counts[kind]+=1;examples.setdefault(kind,row)
 if kind=='nan/nan':
  model_counts['nan_sign_only']+=(int(row['left'],16)^int(row['right'],16))==0x80000000
  model_counts['negative_nan_odd_exponent']+=int(row['a'],16)>0xff800000 and abs(f(row['b']))%2==1
 if kind in ('normal/normal','subnormal/subnormal'):
  x,y=f(row['a']),f(row['b'])
  if not (0.9375<x<1.0625):
   u,j=model(x,y,True);d,k=model(x,y,False)
   model_counts['table_path_cases']+=1;model_counts['ucrt_model_matches']+=u==row['left'];model_counts['amd_model_matches']+=d==row['right'];model_counts['different_index']+=j!=k
  else:model_counts['near_one_cases']+=1
paper=[]
for row in json.loads((pathlib.Path(__file__).parent/'results-f27c/paper-results.json').read_text()):
 if row['function']=='powf' and row['outputs']['ucrt0']!=row['outputs']['amd-off']:
  x,y=[f(h) for h in row['bits']]
  if cls(row['outputs']['ucrt0'])=='normal':
   u,j=model(x,y,True);d,k=model(x,y,False)
   assert u==row['outputs']['ucrt0'] and d==row['outputs']['amd-off']
   paper.append(dict(bits=row['bits'],kind='rounded/truncated log index',ucrt_index=j,amd_index=k))
  else:paper.append(dict(bits=row['bits'],kind='underflow cutoff',ucrt=row['outputs']['ucrt0'],amd=row['outputs']['amd-off']))
result=dict(paper_mismatches=paper,table_comparison=checks,output_classes=counts,first_by_class=examples,table_index_diagnostic=model_counts)
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
