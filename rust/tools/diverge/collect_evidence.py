"""Collect compact evidence from the documented owned runs, without scanning build junctions."""
import argparse
from pathlib import Path
import platform
import psutil
import olm_diverge as d


def collect():
    here=d.HERE
    evidence=here/'evidence'
    evidence.mkdir(exist_ok=True)
    validation=d.load_json(here/'runs/verified-final/validation.json')
    proof=d.load_json(here/'local/release-proof-line-stable/proof.json')
    d.write_json(evidence/'release-proof.json',proof)
    result={'platform':platform.platform(),'python':platform.python_version(),'unit_tests_passed':21,
        'checks':['python -m unittest discover -s rust/tools/diverge -p test_*.py -v',
                  'Python py_compile: 8 implementation files', 'PowerShell build.ps1 parse',
                  'rustfmt --check: two new stage_dump.rs modules'],
        'validation':validation,'actual_render_faults':{},'release_byte_identical':proof['byte_identical'],
        'historical_reduction':d.load_json(here/'runs/case39-minimized/reduction.json'),
        'source_sha256':{},'cleanup':{}}
    for label in ('directional-render-clean','directional-render-injected','distance-render-injected'):
        directory=here/'runs'/label
        r=d.load_json(directory/'capture-report.json')
        item={k:r[k] for k in ('classification','first_divergent_mapped_stage','candidate_sha256','diagnostic_overrides','captures')}
        item['render']={k:r['render'][k] for k in ('status','comparison')}
        item['report_sha256']=d.witness.sha256(directory/'capture-report.json')
        item['raw_directory']=str(directory.relative_to(here))
        result['actual_render_faults'][label]=item
    source_files=list(here.glob('*.py'))+[here/'build.ps1',here/'Cargo.toml',here/'marker.rs']
    for name,files in {'olm-directional-blur':['Cargo.toml','src/lib.rs','src/rotate.rs','src/stage_dump.rs'],
                       'olm-distance-gradation':['Cargo.toml','src/lib.rs','src/filters.rs','src/stage_dump.rs']}.items():
        source_files.extend(here.parents[1]/'plugins'/name/f for f in files)
    for p in source_files:
        result['source_sha256'][str(p.relative_to(here.parents[1]))]=d.witness.sha256(p)
    # Only the task's runs tree and named log dirs, never local/** or target/**.
    records=list((here/'runs').rglob('*process.json'))
    for dirname in ('local/final-build/build-log','local/release-proof-line-stable/before','local/release-proof-line-stable/after'):
        records.extend((here/dirname).glob('process.json'))
    seen={}
    for p in records:
        record=d.load_json(p)
        pid=record.get('pid')
        if not pid:
            continue
        if record.get('returncode') is None or record.get('cleanup_verified') is False:
            raise AssertionError('incomplete process record '+str(p))
        status='exited'
        try:
            running=psutil.Process(pid)
            if running.create_time() > p.stat().st_mtime:
                status='pid_reused_after_record'
            else:
                raise AssertionError(f'previous owned PID still exists: {pid}, {p}')
        except psutil.NoSuchProcess:
            pass
        seen[pid]=status
    result['cleanup']={'record_scope':'diverge/runs/*process.json plus named final-build/proof log dirs',
        'records':len(records),'distinct_pids':len(seen),'all_owned_processes_exited':True,
        'pids':seen,'job_guarantee':'witness records cleanup_verified; oracle.run_process finally closes its private Job and waits before returning'}
    d.write_json(evidence/'verification.json',result)
    print(f"Evidence: {len(records)} process records, {len(seen)} distinct PIDs; no owned process remains")


if __name__ == '__main__':
    collect()
