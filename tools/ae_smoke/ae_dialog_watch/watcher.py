"""Build/start before AE; bind only the PID returned by the caller's Popen."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import time

APP = Path('/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app')
SOURCE = Path(__file__).resolve().parent


def compile_tool(directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / 'ae-dialog-watch'
    env = dict(os.environ, TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    with (directory / 'swift-build.log').open('w') as log:
        subprocess.run(['xcrun', 'swiftc', '-module-cache-path', str(directory / 'module-cache'),
                        str(SOURCE / 'Policy.swift'), str(SOURCE / 'main.swift'), '-o', str(binary)],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    return binary


FLAGS = ('CrashOccurred', 'ForceQuitOccured')


def read_flags(domain):
    return {key: subprocess.check_output(['defaults', 'read', domain, key],
                                        text=True).strip() for key in FLAGS}


def prepare_launch(directory, *, disabled=False):
    """Prevent recovery prompts; preserve both effective and on-disk preferences."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    result = {'disabled': disabled, 'changes': []}
    record = directory / 'prevention.json'
    if disabled:
        record.write_text(json.dumps(result, indent=2))
        return result
    processes = subprocess.check_output(['ps', '-axo', 'comm='], text=True)
    if any(line.rstrip().endswith(('/MacOS/After Effects', '/aerender'))
           for line in processes.splitlines()):
        raise RuntimeError('AE busy; no preference changes')
    info = plistlib.loads((APP / 'Contents/Info.plist').read_bytes())
    version = str(info['CFBundleShortVersionString']).split('.')
    if version[:2] != ['26', '3']:
        raise RuntimeError('Only AE 26.3 crash flags are authorized')
    domain = 'com.Adobe.After Effects.26.3'
    source = Path.home() / 'Library/Preferences' / (domain + '.plist')
    backup = directory / ('preferences-' + str(time.time_ns()))
    backup.mkdir(exist_ok=False)
    exported = backup / 'effective.plist'
    copied = backup / 'on-disk.plist'
    subprocess.run(['defaults', 'export', domain, str(exported)], check=True,
                   stdout=subprocess.DEVNULL)
    shutil.copy2(source, copied)
    result.update(domain=domain, backups={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in (exported, copied)},
                  before=read_flags(domain))
    record.write_text(json.dumps(result, indent=2))
    # Persist progress even if a write/read fails. Never import the whole backup.
    try:
        for key in FLAGS:
            subprocess.run(['defaults', 'write', domain, key, '-bool', 'false'], check=True)
            result['changes'].append(key)
            record.write_text(json.dumps(result, indent=2))
        result['after'] = read_flags(domain)
        if any(value != '0' for value in result['after'].values()):
            raise RuntimeError('Crash flags did not read back false')
    finally:
        record.write_text(json.dumps(result, indent=2))
    return result


class DialogWatcher:
    def __init__(self, state, *, binary=None, prevention=True):
        self.directory = Path(state).resolve() / 'dialogs'
        self.directory.mkdir(parents=True, exist_ok=False)
        self.binary = Path(binary) if binary else compile_tool(self.directory)
        self.prevention = prevention
        self.proc = None
        self.log = None

    def start(self):
        self.log = (self.directory / 'dialogs.jsonl').open('w')
        self.proc = subprocess.Popen([str(self.binary), 'watch', str(self.directory)],
                                     stdout=self.log, stderr=self.log)
        deadline = time.monotonic() + 15
        try:
            while not (self.directory / 'ready').exists():
                self.check()
                if time.monotonic() >= deadline:
                    raise RuntimeError('Dialog watcher readiness timeout; no AE launch')
                time.sleep(0.1)
            prepare_launch(self.directory, disabled=not self.prevention)
        except BaseException:
            self.stop()
            raise
        return self

    def bind(self, pid):
        target = self.directory / 'pid'
        temporary = self.directory / 'pid.new'
        temporary.write_text(str(pid))
        temporary.replace(target)

    def _owned_alive(self):
        pid = int((self.directory / "pid").read_text())
        result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="],
                                capture_output=True, text=True)
        return result.stdout.strip() == str(APP / "Contents/MacOS/After Effects")

    def check(self):
        if self.proc is not None and self.proc.poll() is not None and not (
                self.proc.returncode == 0 and (self.directory / 'pid').exists() and
                not self._owned_alive()):
            raise RuntimeError('Dialog watcher stopped; ' +
                               (self.directory / 'dialogs.jsonl').read_text()[-2000:])

    def capture_owned(self, pid):
        with (self.directory / 'blocked-capture.jsonl').open('w') as log:
            subprocess.run([str(self.binary), 'inspect', str(pid), str(self.directory)],
                           stdout=log, stderr=log, timeout=20, check=True)

    def stop(self):
        (self.directory / 'stop').touch()
        if self.proc is not None:
            # Cooperative stop only. Never signal AE or the watcher.
            self.proc.wait(timeout=30)
        if self.log is not None:
            self.log.close()
