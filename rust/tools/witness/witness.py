#!/usr/bin/env python3
"""Run native Windows x64 internal-function witnesses in an owned disposable job."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import struct
import time

HERE = Path(__file__).resolve().parent
KINDS = {"u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "f32", "f64", "ptr"}


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class WindowsJob:
    """Private kill-on-close Job Object; assign suspended child before it runs.

    Same ownership pattern as tools/oracle, kept dependency-free here.
    """
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c = c
        self.k = c.WinDLL("kernel32", use_last_error=True)

        class Basic(c.Structure):
            _fields_ = [("process_time", c.c_int64), ("job_time", c.c_int64),
                        ("flags", w.DWORD), ("min_ws", c.c_size_t), ("max_ws", c.c_size_t),
                        ("active_limit", w.DWORD), ("affinity", c.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]

        class Extended(c.Structure):
            _fields_ = [("basic", Basic), ("io", c.c_uint64 * 6),
                        ("process_mem", c.c_size_t), ("job_mem", c.c_size_t),
                        ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]

        self.k.CreateJobObjectW.argtypes = [c.c_void_p, w.LPCWSTR]
        self.k.CreateJobObjectW.restype = w.HANDLE
        for name, args in {
            "SetInformationJobObject": [w.HANDLE, c.c_int, c.c_void_p, w.DWORD],
            "AssignProcessToJobObject": [w.HANDLE, w.HANDLE],
            "TerminateJobObject": [w.HANDLE, w.UINT],
            "QueryInformationJobObject": [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p],
            "CloseHandle": [w.HANDLE],
        }.items():
            getattr(self.k, name).argtypes = args
            getattr(self.k, name).restype = w.BOOL
        self.handle = self.k.CreateJobObjectW(None, None)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k.SetInformationJobObject(self.handle, 9, c.byref(limits), c.sizeof(limits)):
            error = c.WinError(c.get_last_error())
            self.k.CloseHandle(self.handle)
            raise error

    def attach_resume(self, process):
        if not self.k.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise self.c.WinError(self.c.get_last_error())
        nt = self.c.WinDLL("ntdll")
        nt.NtResumeProcess.argtypes = [self.c.c_void_p]
        nt.NtResumeProcess.restype = self.c.c_long
        if nt.NtResumeProcess(int(process._handle)) != 0:
            raise RuntimeError("could not resume owned process")

    def terminate(self):
        if not self.k.TerminateJobObject(self.handle, 124):
            raise self.c.WinError(self.c.get_last_error())

    def close(self):
        try:
            self.terminate()
            accounting = self.c.create_string_buffer(48)
            deadline = time.monotonic() + 10
            while True:
                if not self.k.QueryInformationJobObject(self.handle, 1, accounting, 48, None):
                    raise self.c.WinError(self.c.get_last_error())
                if int.from_bytes(accounting.raw[40:44], "little") == 0:
                    return True
                if time.monotonic() >= deadline:
                    raise RuntimeError("owned job still has active descendants")
                time.sleep(.01)
        finally:
            self.k.CloseHandle(self.handle)


def run_owned(argv, timeout, out):
    """Capture to files, not pipes: descendants cannot hold communicate open."""
    if os.name != "nt":
        raise OSError("native witness requires Windows; use tools/emulation elsewhere")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    job = WindowsJob()
    process = None
    timed_out = False
    cleanup = False
    started = time.monotonic()
    record = {}

    def save_process():
        code = process.poll() if process is not None else None
        record.update(pid=process.pid if process is not None else None, returncode=code,
            exit_hex=f"0x{code & 0xffffffff:08x}" if code is not None else None,
            timeout=timed_out, elapsed_seconds=time.monotonic()-started,
            cleanup_verified=cleanup)
        (out / "process.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

    with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
        try:
            process = subprocess.Popen([str(a) for a in argv], stdout=stdout, stderr=stderr,
                stdin=subprocess.DEVNULL, creationflags=0x4 | 0x08000000,
                env={**os.environ, "AEX_WITNESS_CHILD": "1"})
            save_process()
            job.attach_resume(process)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                job.terminate()
                process.wait(timeout=10)
        finally:
            try:
                cleanup = job.close()
            finally:
                try:
                    if process is not None:
                        if process.poll() is None:
                            process.kill()  # exact owned PID, also covers failed job assignment
                        process.wait(timeout=10)
                finally:
                    save_process()
    return record


def integer(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not an integer argument")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16 if value.startswith("0x") else 10)
    raise ValueError("expected integer or integer string")


def normalize(spec, base):
    """Resolve files relative to the input spec, validate before starting the child."""
    spec = json.loads(json.dumps(spec, allow_nan=False))
    if spec.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    spec["module"] = str((base / spec["module"]).resolve(strict=True))
    if spec.get("fma", "auto") not in {"auto", "fma", "no-fma"}:
        raise ValueError("unknown FMA mode")
    buffers = spec.get("buffers", {})
    total = 0
    for name, b in buffers.items():
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name):
            raise ValueError("unsafe buffer name")
        if type(b["size"]) is not int or b["size"] < 0:
            raise ValueError("invalid buffer size")
        total += b["size"]
        if "file" in b and "hex" in b:
            raise ValueError("choose buffer file or hex")
        if "file" in b:
            b["file"] = str((base / b["file"]).resolve(strict=True))
            if Path(b["file"]).stat().st_size > b["size"]:
                raise ValueError("input file exceeds buffer")
        if "hex" in b and len(bytes.fromhex(b["hex"])) > b["size"]:
            raise ValueError("hex exceeds buffer")
        for p in b.get("pointers", []):
            if not 0 <= p["offset"] <= b["size"] - 8:
                raise ValueError("pointer relocation outside struct")
            if p["buffer"] not in buffers or not 0 <= p.get("addend", 0) <= buffers[p["buffer"]]["size"]:
                raise ValueError("invalid pointer target")
    if total > 256 * 1024 * 1024:
        raise ValueError("buffer budget exceeds 256 MiB")
    calls = spec.get("calls", [])
    if not 1 <= len(calls) <= 100000:
        raise ValueError("requires 1..100000 calls")
    for call in calls:
        if not 0 <= integer(call["rva"]) <= 0xffffffff:
            raise ValueError("invalid RVA")
        if call["return"] not in KINDS | {"void"} or len(call.get("args", [])) > 32:
            raise ValueError("invalid return type or too many arguments")
        for a in call.get("args", []):
            kind = a["type"]
            if kind not in KINDS or sum(k in a for k in ("value", "bits", "buffer")) != 1:
                raise ValueError("argument needs type and exactly one of value/bits/buffer")
            if "buffer" in a:
                if kind != "ptr" or a["buffer"] not in buffers or not 0 <= a.get("offset", 0) <= buffers[a["buffer"]]["size"]:
                    raise ValueError("invalid buffer pointer")
            elif "bits" in a:
                width = 64 if kind == "ptr" else int(kind[1:])
                if not 0 <= integer(a["bits"]) < 1 << width:
                    raise ValueError("bits exceed argument width")
            elif kind[0] in "ui" or kind == "ptr":
                width = 64 if kind == "ptr" else int(kind[1:])
                low = -(1 << (width-1)) if kind[0] == "i" else 0
                high = (1 << (width-1)) if kind[0] == "i" else (1 << width)
                if not low <= integer(a["value"]) < high:
                    raise ValueError("integer exceeds argument range")
            elif type(a["value"]) not in (int, float) or not math.isfinite(a["value"]):
                raise ValueError("float requires finite numeric value; use bits for NaN/Inf")
            elif kind == "f32":
                try:
                    struct.pack("<f", a["value"])
                except OverflowError as e:
                    raise ValueError("f32 value out of range; use bits for Inf") from e
    trace = spec.get("trace", {})
    if type(trace.get("budget", 10000)) is not int or not 0 <= trace.get("budget", 10000) <= 1000000:
        raise ValueError("trace budget requires 0..1000000 records")
    for imp in trace.get("imports", []):
        if len(imp["args"]) > 32 or any(k not in KINDS for k in imp["args"]) or imp["return"] not in KINDS | {"void"}:
            raise ValueError("invalid import signature")
    return spec


def run(spec, out, host=None, timeout=30, base=None):
    host = Path(host or HERE / "target/release/witness-host.exe").resolve(strict=True)
    normalized = normalize(spec, Path(base or Path.cwd()))
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    spec_path = out / "spec.json"
    spec_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    manifest = {"schema_version": 1, "host": str(host), "host_sha256": sha256(host),
        "module_sha256": sha256(normalized["module"]), "spec_sha256": sha256(spec_path),
        "platform": platform.platform(), "processor": os.environ.get("PROCESSOR_IDENTIFIER"),
        "input_files": {b["file"]: sha256(b["file"]) for b in normalized.get("buffers", {}).values() if "file" in b},
        "timeout_seconds": timeout}
    try:
        process = run_owned([host, "--child", spec_path, out], timeout, out)
        manifest["process"] = process
        result_path = out / "result.json"
        manifest["classification"] = ("timeout" if process["timeout"] else "child_failure" if process["returncode"]
            else "success" if result_path.exists() else "missing_result")
        manifest["module_sha256_after"] = sha256(normalized["module"])
        if manifest["module_sha256_after"] != manifest["module_sha256"]:
            manifest["classification"] = "module_changed"
        if manifest["classification"] == "success":
            result = json.loads(result_path.read_text(encoding="utf-8"))
            manifest["ucrt_sha256"] = sha256(result["fma"]["ucrt_path"])
        manifest["artifacts"] = {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    except BaseException as error:
        manifest.update(classification="controller_error", error=repr(error))
        if (out / "process.json").exists():
            manifest["process"] = json.loads((out / "process.json").read_text(encoding="utf-8"))
        raise
    finally:
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("spec", type=Path)
    p.add_argument("--out", type=Path, required=True, help="new output directory")
    p.add_argument("--host", type=Path)
    p.add_argument("--timeout", type=float, default=30)
    args = p.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
    result = run(spec, args.out, args.host, args.timeout, args.spec.resolve().parent)
    print(json.dumps(result, indent=2))
    return 0 if result["classification"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
