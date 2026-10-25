"""Build/start before AE; bind only the PID returned by the caller's Popen."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
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


def prepare_launch(directory, *, disabled=False):
    """Back up effective CFPreferences before inspecting two candidate session flags.

    Projects, auto-saves, PluginCache and all other preferences are untouched.
    The default backup is durable outside disposable worktrees.
    """
    directory = Path(directory)
    result = {'disabled': disabled, 'changes': []}
    if disabled:
        (directory / 'prevention.json').write_text(json.dumps(result, indent=2))
        return result
    info = plistlib.loads((APP / 'Contents/Info.plist').read_bytes())
    version = str(info['CFBundleShortVersionString']).split('.')
    if len(version) < 2 or version[0] != '26' or not version[1].isdigit():
        raise RuntimeError('Unexpected AE version; no preference changes')
    domain = 'com.Adobe.After Effects.' + '.'.join(version[:2])
    source = Path.home() / 'Library/Preferences' / (domain + '.plist')
    if not source.exists():
        result['reason'] = 'No existing version-specific preference domain'
    else:
        stamp = time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns())
        backup = Path.home() / '.cache/olm-emu/ae-dialog-watch/backups' / stamp
        backup.mkdir(parents=True, exist_ok=False)
        exported = backup / (domain + '.plist')
        # Export includes cfprefsd's effective values. Do not overwrite a live plist.
        subprocess.run(['defaults', 'export', domain, str(exported)], check=True,
                       stdout=subprocess.DEVNULL)
        data = exported.read_bytes()
        prefs = plistlib.loads(data)
        result.update(domain=domain, backup=str(exported), sha256=hashlib.sha256(data).hexdigest())
        result['candidate_flags'] = {key: prefs.get(key) for key in
                                     ('CrashOccurred', 'ForceQuitOccured')}
        result['reason'] = ('No validated deterministic recovery switch. '
                            'Observation only; rely on the dialog watcher.')
        (backup / 'changes.json').write_text(json.dumps(result, indent=2))
    (directory / 'prevention.json').write_text(json.dumps(result, indent=2))
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
