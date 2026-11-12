"""Read-only Git dry-run/size/link audit, confined to this repository's rust/.

No index mutation. The output manifest includes itself, using a fixed point for
its byte size; no file hashes are used so there is no self-hash dependency.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

RUST = Path(__file__).resolve().parents[1]
ROOT = RUST.parent


def git(*args):
    resolved = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip()).resolve()
    if resolved != ROOT.resolve():
        raise RuntimeError(f"Unexpected repository root: {resolved}")
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    output = args.out.resolve()
    if not output.is_relative_to(RUST):
        raise ValueError("Audit output must be inside rust/")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text("{}\n", encoding="utf-8")
    dry = git("add", "-n", "--", "rust").decode("utf-8")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", "--", "rust").decode("utf-8").split("\0")
    untracked = sorted(filter(None, untracked))
    tracked = set(filter(None, git("ls-files", "-z", "--", "rust").decode("utf-8").split("\0")))
    candidates = set(untracked) | tracked
    forbidden = {".aex", ".dll", ".exe", ".pdb", ".obj", ".lib", ".png", ".log", ".rgba16le", ".rgba32f-le"}
    invalid = [f for f in candidates if Path(f).suffix.lower() in forbidden]
    pe_files = []
    for f in candidates:
        with (ROOT / f).open("rb") as stream:
            if stream.read(2) == b"MZ":
                pe_files.append(f)
    if invalid or pe_files:
        raise RuntimeError(f"Generated artifact or executable selected: {invalid + pe_files}")
    links = []
    for doc in sorted((RUST / "plugins").glob("*/VALIDATION.md")):
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8-sig")):
            if re.match(r"https?://", target) or target.startswith("#"):
                continue
            path = (doc.parent / target.split("#", 1)[0]).resolve()
            relative = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
            ok = path.is_file() and relative in candidates
            links.append({"document": doc.relative_to(ROOT).as_posix(), "target": target, "versionable": ok})
            if not ok:
                raise RuntimeError(f"Unversioned Markdown link: {doc}: {target}")
    justification = {
        "rust/plugins/olm-smoother/src/generated.rs":
            "Required mechanical C++/instruction translation imported by lib.rs; preserve operation order and generated structure. Regenerator tools/translate.py is retained."
    }
    for _ in range(12):
        files = [{"path": f, "bytes": (ROOT / f).stat().st_size} for f in untracked]
        large = [dict(f, justification=justification.get(f["path"])) for f in files if f["bytes"] > 1_000_000]
        if any(f["justification"] is None for f in large):
            raise RuntimeError(f"Unjustified file over 1 MB: {large}")
        report = {"scope": "rust/ only; git add -n does not stage", "file_count": len(files),
                  "total_bytes": sum(f["bytes"] for f in files),
                  "existing_tracked_files": sorted(tracked),
                  "counts_by_area": dict(sorted(Counter('/'.join(f.split('/')[:3]) if f.startswith(('rust/plugins/', 'rust/crates/')) else '/'.join(f.split('/')[:2]) for f in untracked).items())),
                  "largest_files": sorted(files, key=lambda f: f["bytes"], reverse=True)[:15],
                  "over_1_MB": large, "forbidden_artifacts": invalid, "pe_executables": pe_files,
                  "validation_links": links, "git_add_dry_run": dry.splitlines(), "files": files}
        encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
        old_size = output.stat().st_size
        output.write_bytes(encoded)
        if len(encoded) == old_size:
            break
    else:
        raise RuntimeError("Audit manifest size did not stabilize")
    print(json.dumps({k: report[k] for k in ("file_count", "total_bytes", "over_1_MB", "counts_by_area")}, indent=2))


if __name__ == "__main__":
    main()
