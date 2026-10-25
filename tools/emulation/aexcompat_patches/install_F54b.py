#!/usr/bin/env python3
"""Install a reviewed F54b Release worker without changing the default oracle."""
import argparse, fcntl, hashlib, json, shutil, subprocess
from pathlib import Path

def sha(p):
    return hashlib.file_digest(p.open("rb"), "sha256").hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--binary", type=Path, required=True)
    a=ap.parse_args()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(a.source), *args], text=True).strip()
    if git("status", "--porcelain"):
        raise SystemExit("Commit reviewed source before installation")
    cache=Path.home()/".cache/olm-emu"
    out=cache/"worker-F54b"
    out.mkdir(exist_ok=True)
    binary=out/"aex-guest-worker"
    if binary.exists() and sha(binary)!=sha(a.binary):
        raise SystemExit("Refusing to overwrite a different registered worker")
    shutil.copy2(a.binary, binary)
    meta=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"),
              worker_sha256=sha(binary), base="5a9bd8f7",
              source_manifest={p:sha(a.source/p) for p in git("diff", "--name-only", "5a9bd8f7", "HEAD").splitlines()},
              recipe="cargo build --manifest-path guest/Cargo.toml --release -p aex-guest-worker -j 1",
              default_worker_changed=False)
    with (out/"source.tar").open("wb") as archive:
        subprocess.run(["git", "-C", str(a.source), "archive", "HEAD"], stdout=archive, check=True)
    meta["source_archive_sha256"] = sha(out/"source.tar")
    (out/"build.json").write_text(json.dumps(meta,indent=2)+"\n")
    with (cache/".index.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path=cache/"INDEX.json"; data=json.loads(path.read_text())
        entry=dict(name=out.name,parent="worker-F54",worker_path=str(binary),worker_sha256=sha(binary),
                   build_json=str(out/"build.json"),recipe="tools/emulation/aexcompat_patches/install_F54b.py",matches_recorded=True)
        existing=[v for v in data["links"] if v["name"]==out.name]
        if existing and existing!=[entry]:
            raise SystemExit("Conflicting INDEX entry")
        if not existing:
            data["links"].append(entry)
            staged=cache/"INDEX.F54b.json";staged.write_text(json.dumps(data,indent=2)+"\n");staged.replace(path)
    print(json.dumps(dict(head=meta["head"],worker_sha256=sha(binary))))
if __name__=="__main__": main()
