from pathlib import Path
import json, subprocess, sys, os
scratch=Path('orchestra/state/F23-corpus-rebaseline-all').resolve()
scratch.mkdir(parents=True, exist_ok=True)
os.environ.update(TMPDIR=str(scratch),TMP=str(scratch),TEMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
phase=sys.argv[1]
failed = False
for corpus in sorted(Path('tests/fuzz_corpus').iterdir()):
    if not corpus.is_dir(): continue
    files=sorted(corpus.glob('*.json'))
    plugin=json.loads(files[0].read_text())['plugin'] if files else corpus.name
    report=scratch / f'{phase}-{corpus.name}.json'
    report.unlink(missing_ok=True)
    cmd=[sys.executable,'-B','tools/fuzz/run.py','--plugin',plugin,'--replay',str(corpus),'--jobs','2','--budget-minutes','30','--scratch',str(scratch),'--report',str(report)]
    with (scratch/f'{phase}-{corpus.name}.log').open('w') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    data=json.loads(report.read_text()) if report.exists() else {}
    rows=data.get('replays',[])
    print(corpus.name,'exit',result.returncode,'matches',sum(r['matches_saved'] for r in rows),'/',len(files),'status',data.get('status'),flush=True)
    if files:
        failed |= (data.get('status') != 'replay_complete' or len(rows) != len(files)
                   or result.returncode not in (0, 1)
                   or (phase != 'before' and not all(r['matches_saved'] for r in rows)))
    else:
        failed |= result.returncode != 2 or data.get('status') != 'setup_error'
sys.exit(1 if failed else 0)
