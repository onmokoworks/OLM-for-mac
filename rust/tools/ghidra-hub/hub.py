"""Explicit, PID-safe lifecycle and maintenance CLI. No global Codex configuration writes."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from urllib.request import Request, urlopen

import psutil
from runtime import HOME, atomic_json

PIDFILE = HOME/'hub.pid.json'


def owned_process(identity):
    try:
        p = psutil.Process(identity['pid'])
        if abs(p.create_time()-identity['created']) > 0.01:
            return None
        args = p.cmdline()
        if identity['token'] not in args or 'serve' not in args:
            return None
        return p
    except psutil.NoSuchProcess:
        return None


def status():
    if not PIDFILE.exists():
        return {'running': False}
    identity = json.loads(PIDFILE.read_text())
    live = owned_process(identity)
    return dict(running=live is not None, pid=identity['pid'], port=identity['port'])


def start(port, workers):
    if status()['running']:
        return status()
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME/'logs').mkdir(exist_ok=True)
    token = uuid.uuid4().hex
    cmd = [sys.executable, str(Path(__file__).resolve()), 'serve', '--port', str(port),
           '--workers', str(workers), '--token', token]
    with (HOME/'logs/server.log').open('a', encoding='utf-8') as log:
        child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    spawned = psutil.Process(child.pid)
    atomic_json(HOME/'launch.json', dict(pid=child.pid, created=spawned.create_time(), token=token))
    try:
        deadline = time.monotonic()+180
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError('Server failed; see logs/server.log')
            if PIDFILE.exists():
                identity = json.loads(PIDFILE.read_text())
                if identity.get('token') == token:
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/health', timeout=1) as response:
                            health = json.load(response)
                        if health['pid'] == identity['pid']:
                            return dict(**status(), url=f'http://127.0.0.1:{port}/mcp')
                    except OSError:
                        pass
            time.sleep(.25)
        raise TimeoutError('Server start exceeded 180 seconds')
    except BaseException:
        # Only this exact Popen tree is eligible for failed-start cleanup.
        if spawned.is_running():
            members = spawned.children(recursive=True)+[spawned]
            for p in reversed(members):
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(members, timeout=15)
            if alive:
                raise RuntimeError(f'Owned start processes remain: {[p.pid for p in alive]}')
        child.wait(timeout=15)
        raise


def stop():
    if not PIDFILE.exists():
        return dict(running=False, exited=True)
    identity = json.loads(PIDFILE.read_text())
    process = owned_process(identity)
    if process is None:
        return dict(running=False, exited=True, stale_pid=identity['pid'])
    members = process.children(recursive=True)+[process]
    launch_file = HOME/'launch.json'
    if launch_file.exists():
        launch = json.loads(launch_file.read_text())
        if launch.get('token') == identity['token']:
            launcher = owned_process(launch)
            if launcher and launcher.pid != process.pid and process.ppid() == launcher.pid:
                members.append(launcher)
    request = Request(f"http://127.0.0.1:{identity['port']}/shutdown", b'',
                      {'x-hub-token': identity['token']})
    graceful_requested = False
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
        graceful_requested = True
    except OSError:
        pass
    _, alive = psutil.wait_procs(members, timeout=45 if graceful_requested else 1)
    forced = []
    for p in alive:
        # psutil Process objects bind PID + create time, defending against reuse.
        try:
            p.kill()
            forced.append(p.pid)
        except psutil.NoSuchProcess:
            pass
    _, survivors = psutil.wait_procs(alive, timeout=15)
    result = dict(pid=identity['pid'], exited=not survivors, forced=forced,
                  remaining=[p.pid for p in survivors], owned_pids=[p.pid for p in members],
                  graceful_requested=graceful_requested)
    atomic_json(HOME/'reports/last-stop.json', result)
    if survivors:
        raise RuntimeError(str(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('import-knowledge')
    sub.add_parser('status')
    sub.add_parser('stop')
    for name in ['start', 'serve']:
        p = sub.add_parser(name)
        p.add_argument('--port', type=int, default=8766)
        p.add_argument('--workers', type=int, choices=[1, 2, 3], default=3)
        if name == 'serve':
            p.add_argument('--token', required=True)
    p = sub.add_parser('add-version')
    p.add_argument('--aex', required=True)
    p.add_argument('--like', required=True)
    p.add_argument('--url', default='http://127.0.0.1:8766')
    p = sub.add_parser('add')
    p.add_argument('--aex', required=True)
    p.add_argument('--name')
    p.add_argument('--url', default='http://127.0.0.1:8766')
    args = parser.parse_args()
    if args.command == 'init':
        from runtime import bootstrap
        bootstrap()
    elif args.command == 'import-knowledge':
        from knowledge import import_knowledge
        import_knowledge()
    elif args.command == 'serve':
        from server import serve
        serve(args.port, args.token, args.workers)
    elif args.command == 'start':
        # Prevent simultaneous starters; OS releases this lock even after a crash.
        import msvcrt
        with (HOME/'start.lock').open('a+b') as lock:
            lock.seek(0)
            if lock.read(1) == b'':
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            print(json.dumps(start(args.port, args.workers)))
    elif args.command == 'add-version':
        from client import Client
        print(json.dumps(Client(args.url).add_version(aex=args.aex, like=args.like), indent=2))
    elif args.command == 'add':
        from client import Client
        print(json.dumps(Client(args.url).add_program(aex=args.aex, name=args.name)))
    else:
        print(json.dumps(stop() if args.command == 'stop' else status()))


if __name__ == '__main__':
    main()
