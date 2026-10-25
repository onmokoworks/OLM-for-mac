"""Summarize native ARM64 sample by disassembled rotation stage ranges."""
import collections, json, re
from pathlib import Path
s=Path(__file__).resolve().parents[3]/'orchestra/state/P07e-radialblur-rotation-parallel'
lines=(s/'baseline.sample.txt').read_text().splitlines();counts=collections.Counter()
for i,line in enumerate(lines):
 if re.match(r'          \+   \d+ ',line):
  n=int(re.search(r'\d+',line)[0]);detail=lines[i+1] if '???' in line else line
  m=re.search(r'RenderRotationTyped.*? \+ (\d+)',detail)
  if m:
   offset=int(m[1]);stage='scatter' if 22800<=offset<25776 else 'prepass' if 19000<=offset<22800 else 'other'
  else:stage='other'
  counts[stage]+=n
result=dict(counts=counts,total=sum(counts.values()),classification='INFERENCE: inline stage ranges in retained P05b ARM64 code; not exact stage wall times',sampling='No SampleScalar/SampleRGBA frames observed; sampling may finish before sample attaches. Not a claim of zero work.')
(s/'profile-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
