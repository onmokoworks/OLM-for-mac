#!/usr/bin/env python3
"""Staged real-AE probe and no-effect project preparation.

Fail closed on launch timeout; captures the screen without interacting with dialogs.
Render/corpus/host comparison stages are not yet implemented (see A01b report).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path.home() / '.cache/olm-emu/A01'
STATE = ROOT / 'orchestra/state/A01b-real-ae-render-compare'
PLUGINS = ['OLMBlur','ColorKeep','OLMColorKey','OLMDirectionalBlur',
           'OLMDistanceGradation','OLMKiraKira','OLMSmoother2','OLMToonDilate',
           'OLMRadialBlur','OLMSmoother']


def capture(cmd):
    return subprocess.check_output(cmd, text=True)


def preflight():
    for year in (2026, 2025):
        folder = Path(f'/Applications/Adobe After Effects {year}/Plug-ins/OLM-smoke')
        if not folder.is_dir() or not os.access(folder, os.W_OK):
            raise RuntimeError(f'needs user sudo: sudo mkdir -p "{folder}" && sudo chown "$USER":staff "{folder}"')


def install():
    records = []
    for name in PLUGINS:
        bundle = CACHE / f'xcode/{name}/products/{name}.plugin'
        binary = bundle / f'Contents/MacOS/{name}'
        arch = capture(['lipo', '-info', str(binary)])
        build = capture(['xcrun', 'vtool', '-show-build', str(binary)])
        if not all(a in arch for a in ('arm64', 'x86_64')) or re.findall(r'minos\s+(\S+)', build) != ['11.0', '11.0']:
            raise RuntimeError(f'{name}: unexpected architecture/deployment target: {arch} {build}')
        paths = []
        for year in (2026, 2025):
            dest = Path(f'/Applications/Adobe After Effects {year}/Plug-ins/OLM-smoke') / bundle.name
            if dest.exists():
                raise RuntimeError(f'Refusing to overwrite existing bundle: {dest}')
            shutil.copytree(bundle, dest)
            paths.append(str(dest))
        records.append(dict(plugin=name, sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                            lipo=arch, vtool=build, installed=paths))
    manifest = dict(head=capture(['git','-C',str(ROOT),'rev-parse','HEAD']).strip(), bundles=records)
    (STATE / 'bundles.json').write_text(json.dumps(manifest, indent=2)+'\n')


def running():
    listing = capture(['ps', '-axo', 'pid=,command='])
    return [line.strip().split(None, 1)[0] for line in listing.splitlines()
            if re.search(r'MacOS/After Effects$', line)]


def probe(year, timeout, inputs=None, controls_only=False):
    deadline = time.monotonic() + 7200
    while running():
        if time.monotonic() >= deadline:
            raise RuntimeError('AE busy for 2 hours; left existing process untouched')
        print('AE already running; waiting five minutes', flush=True)
        time.sleep(300)
    pressure = capture(['memory_pressure'])
    (STATE / f'memory-{year}.txt').write_text(pressure)
    free = re.search(r'memory free percentage:\s*(\d+)%', pressure)
    if not free or int(free[1]) < 30:
        raise RuntimeError('Need at least 30% free memory')
    out = STATE / f'probe-{year}.json'
    if out.exists():
        raise RuntimeError(f'Refusing stale result: {out}')
    specs=[]
    for name in PLUGINS:
        pipl=(ROOT / f'mac/{name}/{name}PiPL.r').read_text()
        specs.append(dict(plugin=name, matchName=re.search(r'AE_Effect_Match_Name\s*\{\s*"([^"]+)"',pipl)[1]))
    wrapper=STATE / f'launch-{year}.jsx'
    config=dict(output=str(out),plugins=[] if controls_only else specs,directory=str(STATE))
    if inputs: config['inputs']=json.loads(inputs.read_text())
    payload='prepare.jsx' if inputs else 'probe.jsx'
    wrapper.write_text('var A01='+json.dumps(config)+';\n$.evalFile(new File('+json.dumps(str(Path(__file__).with_name(payload)))+'));\n')
    exe=f'/Applications/Adobe After Effects {year}/Adobe After Effects {year}.app/Contents/MacOS/After Effects'
    env=dict(os.environ,TMPDIR=str(STATE),TMP=str(STATE),TEMP=str(STATE))
    with (STATE / f'ae-{year}.log').open('w') as log:
        process=subprocess.Popen([exe,'-r',str(wrapper)],stdout=log,stderr=subprocess.STDOUT,env=env)
        (STATE / f'pid-{year}.txt').write_text(str(process.pid)+'\n')
        owned_helpers = {}
        try:
            start=time.monotonic()
            end=start+timeout
            dispatched=False
            while time.monotonic()<end and process.poll() is None:
                # Remember only descendants inside this AE installation.
                listing=capture(['ps','-axo','pid=,ppid=,command='])
                rows=[line.strip().split(None,2) for line in listing.splitlines()]
                parents={process.pid, *owned_helpers}
                for _ in range(5):
                    for row in rows:
                        if len(row)==3 and int(row[1]) in parents and row[2].startswith(str(Path(exe).parents[2])+'/'):
                            pid=int(row[0]); parents.add(pid); owned_helpers[pid]=row[2]
                if out.exists():
                    try:
                        if json.loads(out.read_text()).get('phase') in ('complete','error'):
                            with (STATE / f'vmmap-{year}.txt').open('w') as f:
                                subprocess.run(['vmmap',str(process.pid)],stdout=f,stderr=subprocess.STDOUT,timeout=30)
                            if json.loads(out.read_text()).get('phase')=='error':
                                raise RuntimeError('JSX reported an error; see '+str(out))
                            return
                    except json.JSONDecodeError:
                        pass
                if not dispatched and time.monotonic()-start > 35 and not out.exists():
                    dispatched=True
                    with (STATE / f'doscript-{year}.log').open('w') as f:
                        try:
                            subprocess.run(['osascript','-e',f'tell application \"Adobe After Effects {year}\" to DoScriptFile POSIX file '+json.dumps(str(wrapper))],stdout=f,stderr=subprocess.STDOUT,timeout=20)
                        except subprocess.TimeoutExpired:
                            pass
                time.sleep(1)
            screens=STATE / 'screens'
            screens.mkdir(parents=True,exist_ok=True)
            subprocess.run(['screencapture','-x',str(screens / f'blocked-{year}.png')],check=True)
            shot = screens / f'blocked-{year}.png'
            edge = 1000
            while True:
                subprocess.run(['sips','-Z',str(edge),str(shot)], stdout=subprocess.DEVNULL, check=True)
                if shot.stat().st_size <= 400_000:
                    break
                edge = max(1, edge * 3 // 4)
            raise RuntimeError(f'AE did not complete probe; exit={process.poll()}; inspect blocked-{year}.png')
        finally:
            # Only signal the exact child started here, never another AE process.
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try: process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=30)
            for pid, command in owned_helpers.items():
                current=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
                if current.returncode==0 and current.stdout.strip()==command:
                    try: os.kill(pid,signal.SIGTERM)
                    except ProcessLookupError: pass


def main():
    global STATE
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=('probe','io','matrix','compare','screens','all'), default='probe')
    p.add_argument('--prepare-inputs', type=Path, help='Prepare default render projects using this inputs.json')
    p.add_argument('--run-id', default='', help='New subdirectory for a rerun')
    p.add_argument('--build',action='store_true')
    p.add_argument('--install',action='store_true')
    p.add_argument('--year',type=int,choices=(2025,2026),default=2026)
    p.add_argument('--timeout',type=int,default=120)
    args=p.parse_args()
    if args.run_id:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id): p.error('invalid run id')
        STATE = STATE / args.run_id
    if args.stage in ('matrix', 'compare', 'screens', 'all'):
        p.error('Stage not implemented; see A01b report')
    if args.stage == 'io' and not args.prepare_inputs:
        p.error('--stage io requires --prepare-inputs')
    preflight(); STATE.mkdir(parents=True,exist_ok=True)
    if args.build:
        with (STATE/'build.log').open('w') as log:
            subprocess.run(['python3',str(ROOT/'tools/fuzz/build_F47_bundles.py'),'--scratch',str(CACHE)],stdout=log,stderr=subprocess.STDOUT,check=True)
    if args.install: install()
    probe(args.year,args.timeout,args.prepare_inputs,args.stage == 'io')
    if args.stage == 'io':
        print('No-effect projects prepared only; render/decode gate is not implemented.', flush=True)

if __name__=='__main__':
    main()
