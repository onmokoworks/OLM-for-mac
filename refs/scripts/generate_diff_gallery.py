#!/usr/bin/env python3
"""Generate an HTML gallery of OLM pixel diffs across local reports."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(tempfile.gettempdir()) / "olm_reports" / "diff_gallery"

PLUGIN_ORDER = [
    "ColorKeep",
    "OLMBlur",
    "OLMColorKey",
    "OLMToonDilate",
    "OLMDistanceGradation",
    "OLMSmoother",
    "OLMSmoother2",
    "OLMDirectionalBlur",
    "OLMRadialBlur",
    "OLMKiraKira",
    "Unassigned",
]

PLUGIN_ALIASES = [
    ("olmsmoother2", "OLMSmoother2"),
    ("olmsmootherv2", "OLMSmoother2"),
    ("smoother2", "OLMSmoother2"),
    ("smootherv2", "OLMSmoother2"),
    ("colorkeep", "ColorKeep"),
    ("olmblur", "OLMBlur"),
    ("olmcolorkey", "OLMColorKey"),
    ("olmtoondilate", "OLMToonDilate"),
    ("olmdistancegradation", "OLMDistanceGradation"),
    ("olmdirectionalblur", "OLMDirectionalBlur"),
    ("olmradialblur", "OLMRadialBlur"),
    ("olmkirakira", "OLMKiraKira"),
    ("olmsmoother", "OLMSmoother"),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_plugin(text: str | None) -> str:
    if not text:
        return "Unassigned"
    if text in PLUGIN_ORDER:
        return text
    compact = re.sub(r"[^a-z0-9]", "", text.lower())
    for key, plugin in PLUGIN_ALIASES:
        if key in compact:
            return plugin
    return "Unassigned"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def effect_names(case: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for effect in case.get("effects", []) or []:
        if isinstance(effect, dict):
            for key in ("match_name", "name"):
                value = effect.get(key)
                if isinstance(value, str):
                    names.append(value)
    return names


def load_neighbor_manifest(report_path: Path) -> dict[str, Any] | None:
    for parent in [report_path.parent.parent, report_path.parent.parent.parent, report_path.parent]:
        candidate = parent / "reference_manifest.json"
        if candidate.exists():
            data = load_json(candidate)
            if isinstance(data, dict) and isinstance(data.get("cases"), list):
                return data
    return None


def case_map(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not manifest:
        return rows
    for index, case in enumerate(manifest.get("cases", []), start=1):
        if isinstance(case, dict):
            case_id = str(case.get("id") or f"case_{index:04d}")
            rows[case_id] = case
    return rows


def infer_plugin(report_path: Path, manifest: dict[str, Any] | None) -> str:
    if manifest:
        cases = manifest.get("cases", [])
        if cases and isinstance(cases[0], dict):
            plugin = normalize_plugin(" ".join(effect_names(cases[0])))
            if plugin != "Unassigned":
                return plugin
    return normalize_plugin(rel(report_path))


def sibling_dirs(report_path: Path) -> tuple[Path, Path, Path]:
    run_dir = report_path.parent.parent
    return run_dir / "reference", run_dir / "candidate", run_dir / "diff"


def find_image(path: Path, frame: str | None) -> Path | None:
    if not frame:
        return None
    candidates = [path / frame, path / "png" / frame, path / "reference" / frame, path / "candidate" / frame]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(path.glob(f"**/{Path(frame).name}"))
    return matches[0] if matches else None


def diff_image_path(diff_dir: Path, frame: str | None, case_id: str) -> Path | None:
    if not frame:
        return None
    stem = Path(frame).stem
    candidates = [
        diff_dir / f"{stem}_{case_id}_diff.png",
        diff_dir / f"{stem}_diff.png",
        diff_dir / frame,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(diff_dir.glob(f"*{case_id}*diff*.png"))
    return matches[0] if matches else None


def read_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def compute_witness(reference: Path | None, candidate: Path | None, row: dict[str, Any]) -> dict[str, Any] | None:
    samples = row.get("samples")
    if isinstance(samples, list) and samples:
        sample = samples[0]
        if isinstance(sample, dict) and "x" in sample and "y" in sample:
            return sample
    if not reference or not candidate or not reference.exists() or not candidate.exists():
        return None
    ref = read_rgba(reference)
    cand = read_rgba(candidate)
    if ref.shape != cand.shape:
        return None
    delta = np.abs(ref.astype(np.int32) - cand.astype(np.int32))
    pixel_delta = delta.max(axis=-1)
    y, x = np.unravel_index(np.argmax(pixel_delta), pixel_delta.shape)
    return {
        "x": int(x),
        "y": int(y),
        "reference": [int(v) for v in ref[y, x]],
        "candidate": [int(v) for v in cand[y, x]],
        "delta": [int(v) for v in delta[y, x]],
    }


def crop_box(image: Image.Image, witness: dict[str, Any] | None, radius: int) -> tuple[int, int, int, int]:
    width, height = image.size
    if not witness:
        return (0, 0, width, height)
    x = int(witness.get("x", width // 2))
    y = int(witness.get("y", height // 2))
    return (max(0, x - radius), max(0, y - radius), min(width, x + radius + 1), min(height, y + radius + 1))


def save_asset(src: Path | None, dest: Path, witness: dict[str, Any] | None, crop_radius: int) -> dict[str, str | None]:
    if not src or not src.exists():
        return {"full": None, "crop": None}
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    crop_dest = dest.with_name(dest.stem + "_crop.png")
    image = Image.open(src).convert("RGBA")
    crop = image.crop(crop_box(image, witness, crop_radius))
    scale = max(1, min(8, 320 // max(1, max(crop.size))))
    crop = crop.resize((crop.size[0] * scale, crop.size[1] * scale), Image.Resampling.NEAREST)
    crop.save(crop_dest)
    return {"full": rel(dest), "crop": rel(crop_dest)}


def scan_reports(report_roots: list[Path], include_exact: bool, limit_per_report: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for root in report_roots:
        if not root.exists():
            continue
        for report_path in sorted(root.glob("**/*.json")):
            if "dashboard" in report_path.parts or "diff_gallery" in report_path.parts:
                continue
            resolved = report_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                report = load_json(report_path)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(report, dict) or not isinstance(report.get("cases"), list):
                continue
            manifest = load_neighbor_manifest(report_path)
            cases_by_id = case_map(manifest)
            plugin = infer_plugin(report_path, manifest)
            reference_dir, candidate_dir, diff_dir = sibling_dirs(report_path)
            rows = []
            for row in report["cases"]:
                if not isinstance(row, dict):
                    continue
                max_diff = row.get("max_diff")
                try:
                    numeric_max = int(max_diff)
                except (TypeError, ValueError):
                    numeric_max = -1
                if numeric_max <= 0 and not include_exact:
                    continue
                rows.append(row)
            rows.sort(
                key=lambda row: (
                    int(row.get("max_diff") or -1),
                    float(row.get("mean_diff") or 0.0),
                    float(row.get("nonzero_px_percent") or 0.0),
                ),
                reverse=True,
            )
            for row in rows[:limit_per_report]:
                case_id = str(row.get("id") or "")
                case = cases_by_id.get(case_id, {})
                frame = str(row.get("frame") or case.get("frame") or "")
                reference = find_image(reference_dir, frame)
                candidate = find_image(candidate_dir, frame)
                diff = diff_image_path(diff_dir, frame, case_id)
                if not reference and not candidate and not diff:
                    continue
                witness = compute_witness(reference, candidate, row)
                items.append(
                    {
                        "plugin": plugin,
                        "case_id": case_id,
                        "frame": frame,
                        "report": rel(report_path),
                        "run_dir": rel(report_path.parent.parent),
                        "max_diff": row.get("max_diff"),
                        "mean_diff": row.get("mean_diff"),
                        "nonzero_px_percent": row.get("nonzero_px_percent"),
                        "witness": witness,
                        "reference_path": reference,
                        "candidate_path": candidate,
                        "diff_path": diff,
                    }
                )
    return items


def write_gallery(items: list[dict[str, Any]], output_dir: Path, crop_radius: int) -> dict[str, Any]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    data_items: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        slug = re.sub(r"[^a-zA-Z0-9_.-]+", "_", f"{index:04d}_{item['plugin']}_{item['case_id']}")
        witness = item.get("witness")
        asset_base = assets_dir / slug
        assets = {
            "reference": save_asset(item.get("reference_path"), asset_base.with_name(slug + "_reference.png"), witness, crop_radius),
            "candidate": save_asset(item.get("candidate_path"), asset_base.with_name(slug + "_candidate.png"), witness, crop_radius),
            "diff": save_asset(item.get("diff_path"), asset_base.with_name(slug + "_diff.png"), witness, crop_radius),
        }
        data_items.append(
            {
                **{k: v for k, v in item.items() if not k.endswith("_path")},
                "assets": assets,
            }
        )
    data = {
        "kind": "olm_diff_gallery",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "case_count": len(data_items),
        "items": data_items,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (output_dir / "data.js").write_text(f"window.olmDiffGalleryData = {json.dumps(data, ensure_ascii=False)};\n", encoding="utf-8")
    (output_dir / "index.html").write_text(render_html(data), encoding="utf-8")
    return data


def img_tag(asset: dict[str, str | None], label: str) -> str:
    crop = asset.get("crop")
    full = asset.get("full")
    if not crop:
        return f'<div class="missing">{escape(label)}<br>not available</div>'
    href = escape(full or crop)
    root_prefix = "../../../"
    return f'<a href="{root_prefix}{href}"><img src="{root_prefix}{escape(crop)}" alt="{escape(label)}"></a>'


def witness_text(witness: Any) -> str:
    if not isinstance(witness, dict):
        return "-"
    parts = []
    if "x" in witness and "y" in witness:
        parts.append(f"({witness['x']},{witness['y']})")
    for key in ("reference", "candidate", "delta"):
        if key in witness:
            parts.append(f"{key}={witness[key]}")
    return " / ".join(parts) if parts else "-"


def plugin_sort_key(plugin: str) -> tuple[int, str]:
    try:
        return (PLUGIN_ORDER.index(plugin), plugin)
    except ValueError:
        return (len(PLUGIN_ORDER), plugin)


def render_html(data: dict[str, Any]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in data["items"]:
        grouped[item["plugin"]].append(item)
    plugins = [plugin for plugin in PLUGIN_ORDER if plugin != "Unassigned"]
    plugin_counts = {
        plugin: len(grouped[plugin])
        for plugin in sorted(set(plugins) | set(grouped), key=plugin_sort_key)
    }
    plugin_order = list(plugin_counts)
    plugin_counts_json = json.dumps(plugin_counts, ensure_ascii=False)
    plugin_order_json = json.dumps(plugin_order, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OLM Diff Gallery</title>
  <style>
    :root {{ color-scheme: dark; --bg:#1b1c1f; --fg:#edf1f5; --muted:#98a2ad; --line:#31353b; --panel:#22262b; --image-bg:#171a1f; --panel-alt:#1d2025; --accent:#c7d2df; --accent-strong:#eef3f8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--fg); }}
    header {{ padding:22px 28px 14px; border-bottom:1px solid var(--line); background:rgba(29,32,37,0.96); backdrop-filter:blur(10px); position:sticky; top:0; z-index:2; }}
    h1 {{ margin:0 0 4px; font-size:24px; letter-spacing:0; }}
    .sub {{ color:var(--muted); max-width:980px; }}
    nav {{ display:flex; flex-wrap:wrap; gap:10px 14px; margin-top:14px; padding-top:12px; border-top:1px solid var(--line); }}
    nav a {{ color:var(--muted); text-decoration:none; padding:0 0 3px; border-bottom:1px solid transparent; }}
    nav a:hover {{ color:var(--accent-strong); border-bottom-color:var(--accent); }}
    main {{ padding:24px 28px 56px; }}
    section {{ margin-bottom:40px; }}
    h2 {{ display:flex; align-items:baseline; gap:10px; font-size:18px; margin:0 0 14px; padding-bottom:8px; border-bottom:1px solid var(--line); }}
    h2 span {{ color:var(--muted); font-size:13px; font-weight:500; }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(560px,1fr)); gap:16px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); padding:14px; overflow:hidden; box-shadow:0 0 0 1px rgba(255,255,255,0.01) inset; }}
    .card-head {{ display:flex; justify-content:space-between; gap:12px; align-items:start; padding-bottom:10px; border-bottom:1px solid var(--line); }}
    h3 {{ margin:0; font-size:15px; overflow-wrap:anywhere; }}
    .metrics {{ display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }}
    .metrics span {{ border:1px solid var(--line); padding:2px 6px; color:var(--muted); background:var(--panel-alt); min-width:72px; text-align:center; }}
    .witness {{ margin:10px 0 12px; padding:8px 10px; background:#1c2025; border-left:2px solid #4a5663; color:var(--muted); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; overflow-wrap:anywhere; }}
    .triptych {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    figure {{ margin:0; min-width:0; }}
    figcaption {{ font-size:12px; color:var(--muted); margin-bottom:5px; }}
    img {{ display:block; max-width:100%; width:100%; height:220px; object-fit:contain; image-rendering:pixelated; background:var(--image-bg); border:1px solid var(--line); }}
    .missing {{ height:220px; display:grid; place-items:center; text-align:center; color:var(--muted); border:1px dashed var(--line); background:#191c21; }}
    .empty {{ background:var(--panel); border:1px dashed var(--line); color:var(--muted); padding:18px; }}
    details {{ margin-top:12px; color:var(--muted); padding-top:10px; border-top:1px solid var(--line); }}
    summary {{ cursor:pointer; color:var(--accent); }}
    code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; overflow-wrap:anywhere; }}
    @media (max-width:760px) {{ .cards {{ grid-template-columns:1fr; }} .triptych {{ grid-template-columns:1fr; }} img,.missing {{ height:180px; }} header,main {{ padding-left:14px; padding-right:14px; }} nav {{ gap:8px 12px; }} }}
  </style>
  <script src="./data.js"></script>
</head>
<body>
  <header>
    <h1>OLM Diff Gallery</h1>
    <div class="sub">Generated {escape(data['generated_at'])}. Non-exact local reports only. Crops are centered on the first/max witness when available.</div>
    <nav id="plugin-nav"></nav>
  </header>
  <main id="gallery-root"><p>Loading gallery...</p></main>
  <script>
    const ROOT_PREFIX = "../../../";
    const PLUGIN_COUNTS = {plugin_counts_json};
    const PLUGIN_ORDER = {plugin_order_json};

    function escapeHtml(value) {{
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function witnessText(witness) {{
      if (!witness || typeof witness !== "object") return "-";
      const parts = [];
      if ("x" in witness && "y" in witness) parts.push(`(${{witness.x}},${{witness.y}})`);
      for (const key of ["reference", "candidate", "delta"]) {{
        if (key in witness) parts.push(`${{key}}=${{JSON.stringify(witness[key])}}`);
      }}
      return parts.length ? parts.join(" / ") : "-";
    }}

    function imgTag(asset, label) {{
      const crop = asset && asset.crop;
      const full = asset && asset.full;
      if (!crop) return `<div class="missing">${{escapeHtml(label)}}<br>not available</div>`;
      const href = ROOT_PREFIX + escapeHtml(full || crop);
      const src = ROOT_PREFIX + escapeHtml(crop);
      return `<a href="${{href}}"><img src="${{src}}" alt="${{escapeHtml(label)}}"></a>`;
    }}

    function renderCard(item) {{
      const assets = item.assets || {{}};
      return `
        <article class="card">
          <div class="card-head">
            <h3>${{escapeHtml(item.case_id)}}</h3>
            <div class="metrics">
              <span>max ${{escapeHtml(item.max_diff)}}</span>
              <span>mean ${{escapeHtml(item.mean_diff)}}</span>
              <span>nz% ${{escapeHtml(item.nonzero_px_percent)}}</span>
            </div>
          </div>
          <div class="witness">${{escapeHtml(witnessText(item.witness))}}</div>
          <div class="triptych">
            <figure><figcaption>Windows / reference</figcaption>${{imgTag(assets.reference, "reference")}}</figure>
            <figure><figcaption>Mac / candidate</figcaption>${{imgTag(assets.candidate, "candidate")}}</figure>
            <figure><figcaption>Amplified diff</figcaption>${{imgTag(assets.diff, "diff")}}</figure>
          </div>
          <details>
            <summary>files</summary>
            <p>report: <code>${{escapeHtml(item.report)}}</code></p>
            <p>run: <code>${{escapeHtml(item.run_dir)}}</code></p>
            <p>frame: <code>${{escapeHtml(item.frame || "-")}}</code></p>
          </details>
        </article>
      `;
    }}

    function renderGallery() {{
      const data = window.olmDiffGalleryData;
      const nav = document.getElementById("plugin-nav");
      const root = document.getElementById("gallery-root");
      if (!data || !Array.isArray(data.items)) {{
        root.innerHTML = "<p>Gallery data was not loaded.</p>";
        return;
      }}

      const grouped = new Map();
      for (const item of data.items) {{
        const key = item.plugin || "Unassigned";
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(item);
      }}

      nav.innerHTML = PLUGIN_ORDER.map((plugin) =>
        `<a href="#${{escapeHtml(plugin)}}">${{escapeHtml(plugin)}} (${{PLUGIN_COUNTS[plugin] ?? 0}})</a>`
      ).join("");

      root.innerHTML = PLUGIN_ORDER.map((plugin) => {{
        const items = grouped.get(plugin) || [];
        const cards = items.length
          ? items.map(renderCard).join("")
          : '<div class="empty">No durable non-exact image comparison report found for this plug-in yet.</div>';
        return `
          <section id="${{escapeHtml(plugin)}}">
            <h2>${{escapeHtml(plugin)}} <span>${{items.length}}</span></h2>
            <div class="cards">${{cards}}</div>
          </section>
        `;
      }}).join("");
    }}

    renderGallery();
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-root", action="append", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-exact", action="store_true")
    parser.add_argument("--limit-per-report", type=int, default=12)
    parser.add_argument("--crop-radius", type=int, default=32)
    args = parser.parse_args()

    roots = args.reports_root or [ROOT / "refs" / "reports"]
    roots = [path if path.is_absolute() else ROOT / path for path in roots]
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    items = scan_reports(roots, args.include_exact, args.limit_per_report)
    data = write_gallery(items, output_dir, args.crop_radius)
    print(f"diff_gallery_html={output_dir / 'index.html'}")
    print(f"diff_gallery_data={output_dir / 'data.json'}")
    print(f"diff_gallery_cases={data['case_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
