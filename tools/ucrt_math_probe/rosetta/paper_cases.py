#!/usr/bin/env python3
"""Extract the binary32 atan2/pow table inputs (including continuation columns)."""
import argparse,hashlib,json,pathlib,re,struct,subprocess
p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
pin='c2b897fb393ed8df33452b225953ccd2003cd389'
root=a.source.resolve().parents[1]
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==pin
assert subprocess.check_output(['git','-C',str(root),'show',pin+':latex/glibc244.tex'])==a.source.read_bytes()
s=a.source.read_text();rows=[];active=None
for number,line in enumerate(s.splitlines(),1):
 if r'\section{Double Precision}' in line:break
 if re.match(r'\s*(atan2|pow)\s+&',line):active=re.match(r'\s*(atan2|pow)',line)[1]+'f'
 elif not (active and re.match(r'\s*&',line)):active=None
 if active:
  vals=re.findall(r'\\verb\|([^|]+)\|',line)
  if len(vals)==2:
   bits=[struct.unpack('<I',struct.pack('<f',float.fromhex(v)))[0] for v in vals]
   rows.append(dict(function=active,line=number,hex=vals,bits=[f'{b:08x}' for b in bits]))
a.out.write_text(json.dumps(dict(url='https://gitlab.inria.fr/zimmerma/math_accuracy',commit='c2b897fb393ed8df33452b225953ccd2003cd389',file='latex/glibc244.tex',sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),cases=rows),indent=2)+'\n')
print('extracted',len(rows),'table input pairs')
