"""File-fed commands in suspended, owned Windows jobs. Never use a shell."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def witness_module():
    path = Path(__file__).resolve().parent.parent / "witness/witness.py"
    spec = importlib.util.spec_from_file_location("autoport_witness", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def codex_executable():
    exe = shutil.which("codex.exe")
    if exe:
        return exe
    # npm launcher is a script; use its installed native executable, not cmd.exe.
    launcher = shutil.which("codex") or shutil.which("codex.cmd")
    if launcher:
        root = Path(launcher).parent / "node_modules/@openai/codex"
        choices = list(root.glob("vendor/*/codex/codex.exe"))
        choices += list(root.glob("vendor/*/bin/codex.exe"))
        choices += list(root.parent.glob("codex-win32-*/vendor/*/bin/codex.exe"))
        choices += list(root.glob("node_modules/@openai/codex-win32-*/vendor/*/bin/codex.exe"))
        if len(choices) == 1:
            return str(choices[0])
    raise FileNotFoundError("supply --codex with the installed native codex.exe")


def run(argv, out, timeout, cwd=None, stdin=None, env=None):
    if timeout <= 0:
        raise TimeoutError("no command budget remains")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    job = witness_module().WindowsJob()
    proc = None
    started = time.monotonic()
    result = {"argv": [str(x) for x in argv], "cwd": str(cwd), "timeout": False,
              "cleanup_verified": False, "timeout_seconds": timeout}
    def save():
        result.update(pid=proc.pid if proc else None,
                      returncode=proc.poll() if proc else None,
                      seconds=time.monotonic()-started)
        (out/"process.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (out/"stdout.txt").open("wb") as stdout, (out/"stderr.txt").open("wb") as stderr:
        inp = open(stdin, "rb") if stdin else open(os.devnull, "rb")
        try:
            proc = subprocess.Popen(result["argv"], stdin=inp, stdout=stdout, stderr=stderr,
                cwd=cwd, env={**os.environ, **(env or {})}, creationflags=0x4 | 0x08000000)
            save()
            job.attach_resume(proc)
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                result["timeout"] = True
        finally:
            inp.close()
            try:
                result["cleanup_verified"] = job.close()
            finally:
                if proc:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=10)
                save()
    return result
