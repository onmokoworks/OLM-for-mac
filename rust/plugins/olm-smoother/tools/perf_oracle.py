"""Run the bounded S-smoother oracle campaign; raw evidence stays outside Git."""
from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[4]
out=Path(sys.argv[1]).resolve()
staged=Path(sys.argv[2]).resolve()
base=Path(r'D:\Projects\01_Project\04_Tools\olm for mac')
refs={'OLMSmoother':base/'ghidra_windows_aex/OLMSmoother.aex'}
paths=list((base/'upstream_20261112/extracted').glob('*/*/Plugins/64/2025/OLMSmoother2.aex'))
assert len(paths)==1
refs['OLMSmoother2']=paths[0]
for name,reference in refs.items():
 routes='classic8,classic16' if name=='OLMSmoother' else 'smart8,smart16,smart32'
 for seed in [20261121,20261122]:
  command=[sys.executable,'-X','utf8',str(root/'rust/tools/oracle/olm_oracle.py'),'render','--reference',str(reference),'--candidate',str(staged/(name+'.aex')),'--routes',routes,'--cases','103','--seed',str(seed),'--jobs','2','--resident','--downsample','1,1/2,1/4','--sizes','1x1,3x7,97x61,257x193','--out',str(out/f'{name}-{seed}')]
  print(' '.join(command),flush=True)
  subprocess.run(command,check=True,cwd=root)
