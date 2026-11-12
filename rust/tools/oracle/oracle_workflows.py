"""Optional CLI workflows; imported lazily so existing oracle APIs stay usable."""
import copy
import json
import math
from pathlib import Path
import shutil
import time
from fractions import Fraction
from types import SimpleNamespace

import numpy as np
from PIL import Image

ORIGINALS = Path(r"D:\Projects\01_Project\04_Tools\olm for mac\ghidra_windows_aex")
CRATES = dict(zip(
    ("color-keep", "olm-blur", "olm-color-key", "olm-directional-blur", "olm-distance-gradation",
     "olm-kirakira", "olm-radial-blur", "olm-smoother", "olm-smoother2", "olm-toon-dilate"),
    ("ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur", "DistanceGradation",
     "OLMKiraKira", "OLMRadialBlur", "OLMSmoother", "OLMSmoother2", "OLMToonDilate")))
HERE = Path(__file__).resolve().parent


def add_commands(sub, harness):
    p = sub.add_parser("check", help="build, stage, inspect and compare a Rust plug-in")
    p.add_argument("crate")
    p.add_argument("--reference", type=Path)
    p.add_argument("--originals", type=Path, default=ORIGINALS)
    p.add_argument("--rust-root", type=Path, default=HERE.parents[1])
    p.add_argument("--lib-name", help="Cargo lib target name if different from the crate name")
    p.add_argument("--harness", type=Path, default=harness)
    p.add_argument("--out", type=Path)
    p.add_argument("--full", action="store_true", help="20 cases per applicable route instead of 6")
    p.add_argument("--seed", type=int, default=20261112)
    p.add_argument("--jobs", type=int, choices=range(1, 4), default=3)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--build-timeout", type=float, default=900)
    p = sub.add_parser("minimize", help="shrink a saved pixel mismatch, preserving every trial")
    p.add_argument("case_dir", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--max-attempts", type=int, default=80)
    p.add_argument("--confirmations", type=int, default=2)


def dispatch(args, o):
    if args.timeout <= 0 or not math.isfinite(args.timeout):
        raise ValueError("timeout must be finite and positive")
    return check(args, o) if args.command == "check" else minimize(args, o)


def dll_from_build(stdout, lib_name):
    matches = set()
    for line in stdout.splitlines():
        try:
            message = json.loads(line)
        except ValueError:
            continue
        target = message.get("target", {})
        if (message.get("reason") == "compiler-artifact" and target.get("name") == lib_name
                and "cdylib" in target.get("crate_types", [])):
            matches.update(Path(f).resolve() for f in message.get("filenames", []) if f.lower().endswith(".dll"))
    if len(matches) != 1:
        raise ValueError(f"expected one emitted cdylib DLL for {lib_name}; found {len(matches)}")
    return matches.pop()


def check(args, o):
    out = (args.out or HERE / "runs" / ("check-" + time.strftime("%Y%m%d-%H%M%S"))).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "crate": args.crate, "full": args.full, "tool": o.identity(o.__file__),
              "workflow_tool": o.identity(__file__), "complete": False}
    code, verdict = 2, "ERROR"
    try:
        if not 1 <= args.jobs <= 3 or not 0 < args.build_timeout < float("inf"):
            raise ValueError("jobs must be 1..3 and build timeout finite/positive")
        reference = args.reference
        if reference is None:
            if args.crate not in CRATES:
                raise ValueError("unknown crate; supply --reference")
            reference = args.originals / (CRATES[args.crate] + ".aex")
        reference = reference.resolve(strict=True)
        rust = args.rust_root.resolve(strict=True)
        report["reference"] = o.identity(reference)
        build = o.run_process(["cargo", "build", "--release", "-p", args.crate, "--locked",
                               "--jobs", str(args.jobs), "--message-format=json-render-diagnostics"],
                              args.build_timeout, cwd=rust,
                              env_overrides={"CARGO_TARGET_DIR": str(HERE / "runs" / "cargo-target")})
        o.write_json(out / "build.process.json", build)
        if build["returncode"] or build["timeout"] or build.get("cancelled"):
            raise RuntimeError("cargo build failed/timed out; see build.process.json")
        dll = dll_from_build(build["stdout"], args.lib_name or args.crate.replace("-", "_"))
        stage = out / "stage"
        stage.mkdir()
        (stage / ".gitignore").write_text("*\n", encoding="utf-8")
        candidate = stage / reference.name
        shutil.copyfile(dll, candidate)
        report["candidate"] = o.identity(candidate)
        report["build_artifact"] = o.identity(dll)
        inventories = {side: o.inspect(args.harness.resolve(strict=True), path, args.timeout)
                       for side, path in (("reference", reference), ("candidate", candidate))}
        diff = o.inventory_diff(inventories["reference"], inventories["candidate"])
        o.write_json(out / "inventory.json", {"identical": not diff, "diff": diff, **inventories})
        render_args = SimpleNamespace(out=out / "render", harness=args.harness.resolve(),
            reference=reference, candidate=candidate, timeout=args.timeout, cases=20 if args.full else 6,
            seed=args.seed, jobs=args.jobs, sizes=o.SIZES, downsample=["1", "1/2", "1/4"],
            routes=list(o.ROUTES), force_classic=False, extent=None, perturb_candidate=[])
        code = o.render(render_args)
        if diff:
            code = 1
        report["inventory_diff"] = diff
        report["render_summary"] = json.loads((out / "render/summary.json").read_text())
        applicable = [v for v in report["render_summary"]["routes"].values() if v["cases_run"]]
        if not applicable and code == 0:
            code = 2
        verdict = {0: "PASS", 1: "FAIL", 2: "INCOMPLETE"}.get(code, "ERROR")
        report["complete"] = True
    except Exception as exc:
        code, verdict = 2, "ERROR"
        report["error"] = str(exc)
    finally:
        report.update(exit_code=code, verdict=verdict)
        o.write_json(out / "summary.json", report)
        print(f"ORACLE {verdict} crate={args.crate} mode={'full' if args.full else 'quick'} summary={out / 'summary.json'}")
    return code


def load_bundle(source, o):
    source = source.resolve(strict=True)
    manifest = json.loads((source / "case.json").read_text(encoding="utf-8"))
    for key in ("reference", "candidate", "harness"):
        if o.sha256(manifest[key]["path"]) != manifest[key]["sha256"]:
            raise ValueError(f"{key} identity changed; minimization refused")
    assets = {}
    for name, digest in manifest["assets"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe bundle asset path")
        path = (source / relative).resolve(strict=True)
        if not path.is_relative_to(source) or o.sha256(path) != digest:
            raise ValueError(f"changed bundle asset: {name}")
        assets[relative.as_posix()] = path.read_bytes()
    if any(f"requests/{side}.json" not in assets for side in ("reference", "candidate")):
        raise ValueError("bundle is missing a side's request JSON")
    requests = {side: json.loads(assets[f"requests/{side}.json"]) for side in ("reference", "candidate")}
    images = {}
    import io
    for name, raw in assets.items():
        if name.endswith(".png"):
            with Image.open(io.BytesIO(raw)) as im:
                images[name] = im.convert("RGBA").copy()
    if "input.png" not in images:
        raise ValueError("minimize requires a PNG input bundle")
    # External layers would make a purported reduced bundle incomplete.
    for request in requests.values():
        for a in request["assignments"]:
            if "layer" in a and a["layer"] not in images:
                raise ValueError("minimize requires bundle-relative PNG layers")
    return {"manifest": manifest, "assets": assets, "requests": requests, "images": images}


def write_bundle(directory, state, o):
    directory.mkdir()
    assets = dict(state["assets"])
    import io
    for name, im in state["images"].items():
        buffer = io.BytesIO()
        im.save(buffer, format="PNG")
        assets[name] = buffer.getvalue()
    for side, request in state["requests"].items():
        assets[f"requests/{side}.json"] = (json.dumps(request, indent=2) + "\n").encode()
    for name, raw in assets.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    manifest = copy.deepcopy(state["manifest"])
    manifest["case"]["size"] = list(state["images"]["input.png"].size)
    manifest["case"]["assignments"] = copy.deepcopy(state["requests"]["reference"]["assignments"])
    if "layer_sizes" in manifest["case"]:
        manifest["case"]["layer_sizes"] = {
            str(a["slot"]): list(state["images"][a["layer"]].size)
            for a in manifest["case"]["assignments"] if "layer" in a
        }
    manifest["case"]["untouched_defaults"] = []
    manifest["case"]["requests_authoritative"] = True
    manifest["minimized_by_tool"] = o.identity(__file__)
    manifest["assets"] = {name: o.sha256(directory / name) for name in sorted(assets)}
    o.write_json(directory / "case.json", manifest)
    return manifest


def proposals(state):
    """Strictly smaller edits: paired slot reset, unit downsample, then image size."""
    slots = sorted({a["slot"] for r in state["requests"].values() for a in r["assignments"]})
    for slot in slots:
        new = copy.deepcopy(state)
        for r in new["requests"].values():
            r["assignments"] = [a for a in r["assignments"] if a["slot"] != slot]
        yield f"untouched-default-slot-{slot}", new
    if any(r.get("host_context", {}).get("spatial", {}).get(axis, {}).get("denominator", 1) !=
           r.get("host_context", {}).get("spatial", {}).get(axis, {}).get("numerator", 1)
           for r in state["requests"].values() for axis in ("downsample_x", "downsample_y")):
        new = copy.deepcopy(state)
        for r in new["requests"].values():
            spatial = r["host_context"]["spatial"]
            for axis in ("downsample_x", "downsample_y"):
                spatial[axis] = {"numerator": 1, "denominator": 1}
            spatial["full_resolution_width"], spatial["full_resolution_height"] = new["images"]["input.png"].size
        new["manifest"]["case"]["downsample"] = "1"
        yield "downsample-1", new
    w, h = state["images"]["input.png"].size
    sizes = dict.fromkeys([(max(1,w//2),max(1,h//2)), (max(1,w//2),h), (w,max(1,h//2)),
                          (max(1,w-1),h), (w,max(1,h-1))])
    for nw, nh in sizes:
        if (nw, nh) == (w, h):
            continue
        for mode in ("crop", "nearest"):
            new = copy.deepcopy(state)
            for name, im in new["images"].items():
                iw, ih = im.size
                size = (max(1, math.ceil(iw*nw/w)), max(1, math.ceil(ih*nh/h)))
                new["images"][name] = im.crop((0,0,*size)) if mode == "crop" else im.resize(size, Image.Resampling.NEAREST)
            for r in new["requests"].values():
                context = r.get("host_context", {})
                spatial = context.get("spatial", {})
                for axis, dimension, key in (("downsample_x",nw,"full_resolution_width"), ("downsample_y",nh,"full_resolution_height")):
                    ratio = spatial.get(axis, {"numerator": 1, "denominator": 1})
                    spatial[key] = math.ceil(dimension / Fraction(ratio["numerator"], ratio["denominator"]))
                if "smart_output_request_rect" in context:
                    l,t,rr,b = context["smart_output_request_rect"]
                    context["smart_output_request_rect"] = [math.floor(l*nw/w),math.floor(t*nh/h),math.ceil(rr*nw/w),math.ceil(b*nh/h)]
            yield f"{mode}-{nw}x{nh}", new


def first_difference(directory, route, o):
    depth = o.ROUTES[route][0]
    a, b = (o.load_output(directory / (s + ".png"), depth) for s in ("reference", "candidate"))
    if a.shape != b.shape:
        return {"shape_mismatch": [list(a.shape), list(b.shape)]}
    locations = np.argwhere(a != b)
    if not len(locations):
        return None
    y,x,c = map(int, locations[0])
    # Request .rgba16le/.rgba32f-le sidecars and PNGs are RGBA. Fixture-v2
    # checkpoint output.bin is a different transport and is packed ARGB.
    result = {"x": x, "y": y, "channel_index": c, "depth": depth,
              "reference_word": int(a[y,x,c]), "candidate_word": int(b[y,x,c])}
    result["channel_order"] = "RGBA"
    result["channel"] = result["channel_order"][c]
    if depth == 32:
        result.update(reference_bits=f"0x{int(a[y,x,c]):08x}", candidate_bits=f"0x{int(b[y,x,c]):08x}",
                      reference_value=repr(float(a.view('<f4')[y,x,c])), candidate_value=repr(float(b.view('<f4')[y,x,c])))
    else:
        result.update(reference_value=int(a[y,x,c]), candidate_value=int(b[y,x,c]))
    return result


def minimize(args, o):
    if args.max_attempts < 1 or args.confirmations < 1:
        raise ValueError("attempts and confirmations must be positive")
    state = load_bundle(args.case_dir, o)
    out = (args.out or HERE / "runs" / ("minimize-" + time.strftime("%Y%m%d-%H%M%S"))).resolve()
    out.mkdir(parents=True, exist_ok=False)
    history = []
    report = {"schema_version": 1, "source": str(args.case_dir.resolve()), "tool": o.identity(o.__file__),
              "workflow_tool": o.identity(__file__), "original_size": list(state["images"]["input.png"].size),
              "timeout_seconds": args.timeout, "confirmations": args.confirmations, "steps": history,
              "complete": False, "minimality": "not_established"}

    def attempt(label, trial):
        directory = out / f"step-{len(history):04d}-{label}"
        manifest = write_bundle(directory, trial, o)
        results = [o.evaluate_case(directory, manifest, args.timeout)]
        for index in range(1, args.confirmations):
            if results[-1]["status"] != "mismatched":
                break
            confirm = directory / f"confirmation-{index}"
            cm = write_bundle(confirm, trial, o)
            results.append(o.evaluate_case(confirm, cm, args.timeout))
        accepted = len(results) == args.confirmations and all(r["status"] == "mismatched" for r in results)
        history.append({"operation": label, "directory": str(directory), "accepted": accepted, "results": results})
        o.write_json(out / "summary.json", report)
        return accepted, directory

    accepted, best = attempt("baseline", state)
    if not accepted:
        report.update(complete=True, exit_code=2, error="baseline mismatch did not reproduce on every confirmation")
        o.write_json(out / "summary.json", report)
        print(report["error"])
        return 2
    local_minimal = False
    while len(history) < args.max_attempts:
        improved = False
        for label, trial in proposals(state):
            if len(history) >= args.max_attempts:
                break
            accepted, directory = attempt(label, trial)
            if accepted:
                state, best, improved = trial, directory, True
                break
        else:
            local_minimal = True
        if not improved:
            break
    report.update(complete=True, exit_code=0, minimal_case_dir=str(best),
                  final_size=list(state["images"]["input.png"].size),
                  minimality="local_minimum_under_documented_moves" if local_minimal else "attempt_budget_exhausted",
                  first_difference=first_difference(best, state["manifest"]["route"], o))
    o.write_json(out / "summary.json", report)
    print(f"MINIMIZED {report['original_size']} -> {report['final_size']} {report['minimality']} case={best}")
    print(json.dumps(report["first_difference"], ensure_ascii=False))
    return 0
