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
    try:
        scripting_prefs(directory / 'prefs')
        preflight(directory)
        if screen_locked():
            raise RuntimeError('Screen locked immediately before launch')
        snapshot(directory / 'before-launch.jsonl')
        watcher.check()
        with (directory / 'ae.log').open('w') as log:
            proc = subprocess.Popen([str(APP / 'Contents/MacOS/After Effects'), '-r', str(jsx)],
                                    stdout=log, stderr=subprocess.STDOUT)
            (directory / 'pid.txt').write_text(str(proc.pid))
            watcher.bind(proc.pid)
            deadline = time.monotonic() + 180
            while proc.poll() is None and time.monotonic() < deadline:
                watcher.check()
                if (watcher.directory / 'snapshot-request').exists() and not (watcher.directory / 'snapshot-ready').exists():
                    snapshot(directory / 'dialog-state.jsonl')
                    (watcher.directory / 'snapshot-ready').touch()
                time.sleep(.5)
            if proc.poll() is None:
                raise RuntimeError('AE 180-second deadline exceeded')
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
            result = dict(marker=marker.read_text(), exit=proc.returncode, remaining=running(), flags=flags)
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
    first = launch(state / 'first-clean-launch', binary, allow_recovery=True)
    second = launch(state / 'next-clean-launch', binary)
    second_events = [json.loads(line) for line in (state/'next-clean-launch/dialogs/dialogs.jsonl').read_text().splitlines()]
    if any(e.get('event') == 'click' for e in second_events):
        raise RuntimeError('Next launch needed dialog handling; not a clean-start proof')
    print(json.dumps(dict(first=first,second=second)))


if __name__ == '__main__':
    main()
