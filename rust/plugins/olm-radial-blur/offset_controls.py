"""Saved-case controls: change only Noise Offset (slot 28), never baseline verdicts."""
import argparse, copy, json, shutil, sys
from pathlib import Path
sys.dont_write_bytecode = True
from triage import oracle, digest_output

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();source=args.source.resolve();args.out.mkdir(parents=True,exist_ok=False)
    baseline=json.loads((source/'case.json').read_text())
    for side in ['reference','candidate','harness']:
        assert oracle.sha256(baseline[side]['path'])==baseline[side]['sha256']
    rows=[]
    for offset in [0.0,1.0]:
        folder=args.out/f'offset-{int(offset)}';folder.mkdir();manifest=copy.deepcopy(baseline)
        for rel,sha in manifest['assets'].items():
            src=source/rel;assert oracle.sha256(src)==sha
            dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        for a in manifest['case']['assignments']:
            if a['slot']==28:a['components']=[offset]
        for side in ['reference','candidate']:
            request=folder/'requests'/f'{side}.json';d=json.loads(request.read_text())
            before=copy.deepcopy(d)
            for a in d['assignments']:
                if a['slot']==28:a['components']=[offset]
            assert [a for a in before['assignments'] if a['slot']!=28]==[a for a in d['assignments'] if a['slot']!=28]
            oracle.write_json(request,d)
        for rel in manifest['assets']:manifest['assets'][rel]=oracle.sha256(folder/rel)
        manifest['control']={'source':str(source),'changed_slot':28,'offset_degrees':offset}
        oracle.write_json(folder/'case.json',manifest)
        row=oracle.evaluate_case(folder,manifest,600)
        row['offset_degrees']=offset
        row['hashes']={s:digest_output(folder,s,manifest['route']) for s in ['reference','candidate']}
        rows.append(row);print(offset,row['status'],flush=True)
    oracle.write_json(args.out/'summary.json',{'identities':{s:baseline[s] for s in ['reference','candidate','harness']},'results':rows,'complete':True})
