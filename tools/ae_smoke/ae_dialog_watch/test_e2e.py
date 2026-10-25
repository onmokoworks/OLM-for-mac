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
from run_ae_smoke import preflight, wait_unlocked, screen_locked, running, quit_once


def launch(directory, binary):
    directory.mkdir(exist_ok=False)
    preflight(directory)
    wait_unlocked(directory)
    preflight(directory)
    if screen_locked():
        raise RuntimeError('Screen locked; no launch')
    marker = directory / 'jsx-marker.txt'
    jsx = directory / 'launch.jsx'
    jsx.write_text('var f=new File(' + json.dumps(str(marker)) + ');\n'
                   'if (!f.open("w")) throw new Error("marker open failed");\n'
                   'f.write("A03b JSX executed"); f.close();\n'
                   '$.sleep(5000); app.quit();\n')
    watcher = DialogWatcher(directory, binary=binary, prevention=True).start()
    proc = None
    quit_requested = False
    try:
        preflight(directory)
        if screen_locked():
            raise RuntimeError('Screen locked immediately before launch')
        watcher.check()
        with (directory / 'ae.log').open('w') as log:
            proc = subprocess.Popen([str(APP / 'Contents/MacOS/After Effects'), '-r', str(jsx)],
                                    stdout=log, stderr=subprocess.STDOUT)
            (directory / 'pid.txt').write_text(str(proc.pid))
            watcher.bind(proc.pid)
            deadline = time.monotonic() + 180
            while proc.poll() is None and time.monotonic() < deadline:
                watcher.check()
                time.sleep(.5)
            if proc.poll() is None:
                raise RuntimeError('AE 180-second deadline exceeded')
            if proc.returncode != 0 or not marker.exists() or running():
                raise RuntimeError('Missing marker or AE main process remains')
            watcher.check()
            flags = read_flags('com.Adobe.After Effects.26.3')
            if any(value != '0' for value in flags.values()):
                raise RuntimeError('Crash flags not false after quit: ' + str(flags))
            events = [json.loads(line) for line in (watcher.directory / 'dialogs.jsonl').read_text().splitlines()]
            if any(e.get('event') == 'click' for e in events):
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
        watcher.stop()
        (directory / 'final-processes.json').write_text(json.dumps(running()))


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
