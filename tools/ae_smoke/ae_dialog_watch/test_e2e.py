#!/usr/bin/env python3
"""Two prevented launches, requiring markers, clean exits and false crash flags."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ae_dialog_watch.watcher import APP, DialogWatcher, compile_tool, read_flags
from ae_dialog_watch.prefs import scripting_prefs
from ae_dialog_watch.crash_snapshot import snapshot
from run_ae_smoke import preflight, wait_unlocked, screen_locked, running, quit_once


class LaunchWait:
    """Separate startup, marker and quit budgets; transitions happen only once."""
    def __init__(self, now):
        self.deadline = now + 180
        self.workspace_seen = False
        self.marker_seen = False

    def observe(self, now, workspace, marker):
        if workspace and not self.workspace_seen:
            self.workspace_seen = True
            if not self.marker_seen:
                self.deadline = now + 180
        if marker and not self.marker_seen:
            self.marker_seen = True
            self.deadline = now + 60

    @property
    def phase(self):
        return 'quit' if self.marker_seen else 'JSX marker' if self.workspace_seen else 'workspace'


def launch(directory, binary, allow_recovery=False):
    directory.mkdir(exist_ok=False)
    preflight(directory)
    wait_unlocked(directory)
    preflight(directory)
    if screen_locked():
        raise RuntimeError('Screen locked; no launch')
    marker = directory / 'jsx-marker.txt'
    jsx = directory / 'launch.jsx'
    jsx.write_text('try { var f=new File(' + json.dumps(str(marker)) + ');\n'
                   'if (!f.open("w")) throw new Error("marker open failed: " + f.error);\n'
                   'f.write("A03c JSX executed; scripting=" + app.preferences.getPrefAsLong("Main Pref Section v2", "Pref_SCRIPTING_FILE_NETWORK_SECURITY")); f.close();\n'
                   '} catch (e) { $.writeln("A03c marker error: " + e); }\n'
                   'finally { app.quit(); }\n')
    snapshot(directory / 'before-prevent.jsonl')
    watcher = DialogWatcher(directory, binary=binary, prevention=True).start()
    (watcher.directory / "snapshot-hook").touch()
    proc = None
    quit_requested = False
    dispatch = None
    dispatch_log = None
    try:
        scripting_prefs(directory / 'prefs')
        preflight(directory)
        if screen_locked():
            raise RuntimeError('Screen locked immediately before launch')
        snapshot(directory / 'before-launch.jsonl')
        watcher.check()
        with (directory / 'ae.log').open('w') as log:
            proc = subprocess.Popen([str(APP / 'Contents/MacOS/After Effects')],
                                    stdout=log, stderr=subprocess.STDOUT)
            (directory / 'pid.txt').write_text(str(proc.pid))
            watcher.bind(proc.pid)
            wait = LaunchWait(time.monotonic())
            while proc.poll() is None and time.monotonic() < wait.deadline:
                watcher.check()
                wait.observe(time.monotonic(), (watcher.directory / 'workspace-ready').exists(),
                    marker.exists() and marker.read_text() == 'A03c JSX executed; scripting=1')
                if wait.workspace_seen and dispatch is None:
                    # One dispatch only, after startup; no concurrent -r submission.
                    if running() != [str(proc.pid)]:
                        raise RuntimeError('Owned AE is not the sole running instance')
                    dispatch_log = (directory / 'dispatch.log').open('w')
                    script = 'tell application ' + json.dumps(str(APP)) + ' to DoScriptFile POSIX file ' + json.dumps(str(jsx))
                    dispatch = subprocess.Popen(['osascript', '-e', script], stdout=dispatch_log, stderr=subprocess.STDOUT)
                if (watcher.directory / 'snapshot-request').exists() and not (watcher.directory / 'snapshot-ready').exists():
                    snapshot(directory / 'dialog-state.jsonl')
                    (watcher.directory / 'snapshot-ready').touch()
                time.sleep(.5)
            if proc.poll() is None:
                raise RuntimeError('AE deadline exceeded: ' + wait.phase)
            if proc.returncode != 0 or not marker.exists() or marker.read_text() != 'A03c JSX executed; scripting=1' or running():
                raise RuntimeError('Missing marker or AE main process remains')
            watcher.check()
            snapshot(directory / 'after-clean-quit.jsonl')
            flags = read_flags('com.Adobe.After Effects.26.3')
            if any(value != '0' for value in flags.values()):
                raise RuntimeError('Crash flags not false after quit: ' + str(flags))
            events = [json.loads(line) for line in (watcher.directory / 'dialogs.jsonl').read_text().splitlines()]
            if any(e.get('event') == 'click' and (not allow_recovery or e.get('rule') != 'crash_recovery_layout') for e in events):
                raise RuntimeError('Prevented launch required a dialog click')
            result = dict(marker=marker.read_text(), exit=proc.returncode, remaining=running(), flags=flags, workspace_seen=wait.workspace_seen, dialog_events=sum(e.get('event') in ('dialog', 'unknown', 'no-safe-button') for e in events), clicks=sum(e.get('event') == 'click' for e in events))
            (directory / 'result.json').write_text(json.dumps(result,indent=2))
            return result
    except BaseException:
        if proc is not None and proc.poll() is None and not quit_requested:
            # Capture only this owned AE process, never the desktop or other apps.
            try:
                with (directory / 'blocked-capture.jsonl').open('w') as log:
                    subprocess.run([str(binary), 'inspect', str(proc.pid), str(directory)],
                                   stdout=log, stderr=log, timeout=20)
            finally:
                quit_requested = True
                quit_once(directory)
            # Only wait; no signals even if normal quit fails.
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
        raise
    finally:
        try:
            try:
                if dispatch is not None:
                    dispatch.wait(timeout=30)
            finally:
                if dispatch_log is not None:
                    dispatch_log.close()
                watcher.stop()
        finally:
            try:
                (directory / 'final-processes.json').write_text(json.dumps(running()))
                (directory / 'lifecycle.json').write_text(json.dumps(dict(
                    exit=proc.poll() if proc else None, quit_requested=quit_requested)))
                if not running():
                    snapshot(directory / 'after-exit.jsonl')
            finally:
                if (directory / 'prefs/scripting-prefs.json').exists():
                    scripting_prefs(directory / 'prefs', restore=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scratch', type=Path, required=True)
    p.add_argument('--binary', type=Path)
    a = p.parse_args()
    state = a.scratch.resolve()
    state.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(state), TMP=str(state), TEMP=str(state))
    binary = a.binary.resolve() if a.binary else compile_tool(state / 'build')
    first = launch(state / 'first-clean-launch', binary)
    second = launch(state / 'next-clean-launch', binary)
    second_events = [json.loads(line) for line in (state/'next-clean-launch/dialogs/dialogs.jsonl').read_text().splitlines()]
    if any(e.get('event') == 'click' for e in second_events):
        raise RuntimeError('Next launch needed dialog handling; not a clean-start proof')
    print(json.dumps(dict(first=first,second=second)))


if __name__ == '__main__':
    main()
