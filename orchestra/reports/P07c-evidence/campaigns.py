"""Requested Classic oracle campaigns, followed by every retained corpus."""
import os,subprocess,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'orchestra/state/P07c-smoother-threading/oracle';S.mkdir(exist_ok=True)
env=dict(os.environ,TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='1',PYTHONDONTWRITEBYTECODE='1')
base=[sys.executable,'tools/fuzz/run.py','--plugin','olmsmoother','--jobs','1','--shrink-attempts','0','--scratch',str(S/'build'),'--corpus',str(S/'failures')]
commands=[]
def run(label,extra):
    cmd=[*base,*extra,'--report',str(S/(label+'.json'))]
    with (S/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    commands.append(dict(label=label,command=cmd,returncode=r.returncode))
    (S/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print(label,r.returncode,flush=True)
run('default',['--seed','1','--n','300'])
for geometry in ('realistic','realistic-v2'):
    for seed in (1,20261025):run(f'{geometry}-{seed}',['--geometry',geometry,'--seed',str(seed),'--n','100'])
run('odd',['--seed','2026','--n','150','--size-sampler','odd-even-v1','--max-size','1920','--size-max-height','1080'])
groups={}
for path in (R/'tests/fuzz_corpus').rglob('*.json'):
    if not path.relative_to(R/'tests/fuzz_corpus').parts[0].startswith('olmsmoother'):continue
    data=json.loads(path.read_text())
    if data.get('plugin')!='olmsmoother':continue
    groups.setdefault((path.parent,data['max_size'],data.get('size_sampler','default')),[]).append(path)
for (directory,maximum,sampler),paths in sorted(groups.items()):
    mixed=len([k for k in groups if k[0]==directory])>1
    for target in paths if mixed else [directory]:
        label='replay-'+str(target.relative_to(R/'tests/fuzz_corpus')).replace('/','_').replace('.json','')
        run(label,['--replay',str(target),'--max-size',str(maximum),'--size-sampler',sampler])
