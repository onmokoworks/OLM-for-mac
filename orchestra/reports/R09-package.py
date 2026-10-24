#!/usr/bin/env python3
"""Archive a completed v2 gate's logs, JSON and saved witnesses, never build trees."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'orchestra/reports'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,default=ROOT/'orchestra/state/R09-release-gate-v2/complete')
    args=parser.parse_args();state=args.state.resolve()
    assert state.is_relative_to(ROOT/'orchestra/state/R09-release-gate-v2')
    result=json.loads((state/'summary.json').read_text())
    assert len(result['stages'])==7 and 'finished_utc' in result
    findings=[]; diagnostics=Counter(); omitted=0
    for path in sorted(state.glob('fresh-*.json'))+sorted((state/'f47d').glob('*-plugin-bundle.json')):
        report=json.loads(path.read_text());plugin=report['plugin']
        route='classic' if plugin=='olmsmoother' else 'smart'
        for row in report.get('cases',[]):
            for other, value in row.get('result',{}).get('routes',{}).items():
                if other != route:
                    diagnostics[other+'_'+value['status']]+=1
            omitted += row.get('corpus_retained') is False
        mismatches=[r for r in report.get('cases',[]) if r.get('result',{}).get('routes',{}).get(route,{}).get('status') in ('mismatch','no_write_violation')]
        if mismatches:
            first=mismatches[0]
            findings.append(dict(report=str(path.relative_to(state)),plugin=plugin,route=route,
                mismatch_count=len(mismatches),first_index=first['index'],witness=first.get('corpus'),
                first_result=first['result']['routes'][route]))
    result['owner_mismatch_findings']=findings
    result['non_owner_route_diagnostics']=dict(diagnostics)
    result['omitted_witnesses']=omitted
    result['static_configuration_findings']=[]
    static=next(r for r in result['stages'] if r['name']=='static')
    for row in static.get('plugins',[]):
        if row['release_config']:continue
        log=state/('settings-'+row['plugin']+'.log')
        for target in json.loads(log.read_text()):
            values=target['buildSettings']
            result['static_configuration_findings'].append(dict(plugin=row['plugin'],
                target=target['target'], effective={k:values.get(k) for k in
                ('ARCHS','MACOSX_DEPLOYMENT_TARGET','OTHER_CFLAGS','OTHER_CPLUSPLUSFLAGS')},
                project_sha256=sha(ROOT/f"mac/{row['plugin']}/Mac/{row['plugin']}.xcodeproj/project.pbxproj"),
                log=str(log.relative_to(state))))
    (OUT/'R09-results.json').write_text(json.dumps(result,indent=2)+'\n')
    archive=OUT/'R09-evidence.tar.gz';members=[]
    with tarfile.open(archive,'w:gz') as tar:
        for path in sorted(state.rglob('*')):
            if not path.is_file() or path.is_symlink():continue
            rel=path.relative_to(state)
            if 'xcode' in rel.parts or path.suffix not in ('.json','.jsonl','.log','.txt'):continue
            tar.add(path,arcname=str(rel),recursive=False)
            members.append(dict(path=str(rel),bytes=path.stat().st_size,sha256=sha(path)))
    manifest=dict(archive=archive.name,sha256=sha(archive),files=members)
    (OUT/'R09-artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(archive=archive.name,sha256=manifest['sha256'],members=len(members),
        bytes=archive.stat().st_size,stages={r['name']:r['status'] for r in result['stages']},
        owner_mismatch_campaigns=len(findings))))

if __name__=='__main__':main()
